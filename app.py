import ast
import contextlib
import contextvars
import difflib
import hmac
import json
import logging
import os
import random
import re
import secrets
import sys
import threading
import time
import traceback
from functools import wraps
from types import MappingProxyType, ModuleType
from urllib.parse import urlencode

from authlib.integrations.flask_client import OAuth
from cryptography.fernet import Fernet, InvalidToken
from flask import Blueprint, Flask, Response, abort, flash, redirect, render_template, request, session, url_for
from flask_wtf.csrf import CSRFError, CSRFProtect
from jinja2 import DictLoader
from sqlalchemy import and_ as sa_and, func as sa_func, inspect as sa_inspect, or_ as sa_or, text as sa_text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from werkzeug.exceptions import HTTPException
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import check_password_hash, generate_password_hash

import ai_providers
import bundles
import deps
import github_client
import route_names
from models import ApiKey, EnvVar, Log, Route, RouteSource, User, db, utcnow
from ui import TEMPLATES

# ==========================================
# 1. הגדרות - סודות חובה, בלי ברירות מחדל
# ==========================================
def require_env(name):
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


app = Flask(__name__)
app.jinja_loader = DictLoader(TEMPLATES)
app.secret_key = require_env("FLASK_SECRET_KEY")
# יצירת מפתח הצפנה:  python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
fernet = Fernet(require_env("ENCRYPTION_KEY"))
ADMIN_EMAIL = (os.environ.get("ADMIN_EMAIL") or "").strip().lower()
# חלופה ל-Google: משתמש (שנרשם עם סיסמה) בשם הזה הופך למנהל בכניסה הראשונה. אחרי זה אפשר למחוק את המשתנה.
ADMIN_USERNAME = (os.environ.get("ADMIN_USERNAME") or "").strip().lower()

database_url = os.getenv("DATABASE_URL", "sqlite:///local.db")
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)
# SQLAlchemy 2.1+ משתמש כברירת מחדל ב-psycopg (גרסה 3). אנחנו מתקינים psycopg2, ולכן מציינים אותו במפורש.
if database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+psycopg2://", 1)

app.config.update(
    SQLALCHEMY_DATABASE_URI=database_url,
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    # מסדי נתונים חיצוניים סוגרים חיבורים לא פעילים; זה בודק ומחדש חיבור לפני שימוש
    SQLALCHEMY_ENGINE_OPTIONS={"pool_pre_ping": True, "pool_recycle": 280},
    MAX_CONTENT_LENGTH=2 * 1024 * 1024,
    # שם ייחודי (לא "session" של Flask) כדי שקוד משתמש יוכל להשתמש בשם "session" בלי להתנגש במערכת הניהול
    SESSION_COOKIE_NAME="sh_admin_session",
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    # לפיתוח מקומי בלי HTTPS: INSECURE_COOKIES=1
    SESSION_COOKIE_SECURE=os.environ.get("INSECURE_COOKIES") != "1",
)
if os.environ.get("TRUST_PROXY") == "1":  # מאחורי Render / nginx: IP אמיתי בלוגים
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

logging.basicConfig(level=logging.INFO)
csrf = CSRFProtect(app)
db.init_app(app)
deps.add_to_path()
def ensure_schema():
    """מוסיף עמודות חדשות לטבלאות קיימות (create_all לא משנה טבלה שכבר קיימת).
    משתמשים שכבר היו במערכת נחשבים מאושרים."""
    cols = {c["name"] for c in sa_inspect(db.engine).get_columns("users")}
    if "is_approved" not in cols:
        true_lit = "1" if db.engine.dialect.name == "sqlite" else "TRUE"
        try:
            db.session.execute(sa_text(f"ALTER TABLE users ADD COLUMN is_approved BOOLEAN NOT NULL DEFAULT {true_lit}"))
            db.session.commit()
        except Exception:  # worker אחר הספיק להוסיף את העמודה
            db.session.rollback()
    # הכתובת הישנה של שרת (/<username>/<route_name>), נשמרת במיגרציה. העמודה והאינדקס נוצרים כאן; הנתונים רק במיגרציה
    route_cols = {c["name"] for c in sa_inspect(db.engine).get_columns("routes")}
    if "legacy_path" not in route_cols:
        try:
            db.session.execute(sa_text("ALTER TABLE routes ADD COLUMN legacy_path VARCHAR(150)"))
            db.session.commit()
        except Exception:  # worker אחר הספיק להוסיף את העמודה
            db.session.rollback()
    try:
        db.session.execute(sa_text("CREATE INDEX IF NOT EXISTS ix_routes_legacy_path ON routes (legacy_path)"))
        db.session.commit()
    except Exception:
        db.session.rollback()


with app.app_context():
    db.create_all()
    ensure_schema()

oauth = OAuth(app)
google = oauth.register(
    name="google",
    client_id=os.environ.get("GOOGLE_CLIENT_ID"),
    client_secret=os.environ.get("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

USERNAME_RE = re.compile(r"^[a-z][a-z0-9_]{2,29}$")
ROUTE_RE = route_names.ROUTE_RE  # [a-z0-9][a-z0-9_-]{0,39}
LANG_RE = re.compile(r"^[\w+#.\- ]{1,30}$")
RESERVED = set(route_names.RESERVED_STATIC | route_names.USERNAME_EXTRA_RESERVED)  # שמות משתמש שמורים. לשמות שרתים: reserved_route_names()
PY_LANGS = {"python", "py", "python3", "flask"}
# מגבלות אורך קוד (ניתנות לשינוי במשתני סביבה ב-Render)
MAX_CODE_CHARS = int(os.environ.get("MAX_CODE_CHARS", "200000"))  # Python ישיר: נשמר כמו שהוא, בלי AI
MAX_AI_CODE_CHARS = int(os.environ.get("MAX_AI_CODE_CHARS", "60000"))  # תרגום ב-AI: התשובה חייבת להיכנס בפלט אחד של המודל
ENV_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,63}$")
MAX_ENV_VARS = 50
MAX_ENV_VALUE = 4096
# סיומת קובץ ב-GitHub -> שפת מקור (py נשלח ישירות, השאר מתורגם ב-AI)
EXT_LANG = {".py": "Python", ".php": "PHP", ".js": "JavaScript", ".mjs": "JavaScript", ".java": "Java", ".go": "Go", ".rb": "Ruby", ".cs": "C#"}


class UserError(Exception):
    """שגיאה שבטוח להציג למשתמש."""


# ==========================================
# 2. שגיאות - בלי לחשוף פרטים פנימיים
# ==========================================
@app.errorhandler(UserError)
def handle_user_error(e):
    # שגיאות שבטוח להציג: חוזרים לאותו מסך עם הודעה ברורה, בלי להעיף את המשתמש לדף נפרד
    if request.endpoint == "login_page":
        flash(str(e), "danger")
        return render_template(
            "login.html",
            tab=request.form.get("action", "login"),
            prefill=(request.form.get("username") or "")[:50],
        ), 400
    if current_user():
        flash(str(e), "danger")
        if request.endpoint == "deploy_server":
            # נשארים בטופס עם כל מה שהוזן, כדי שלא יאבד (מקביל ל-edit_route)
            return render_template(
                "new.html",
                form=request.form,
                providers=ai_providers.PROVIDERS,
                saved_providers={k.provider for k in current_user().api_keys},
                max_code_chars=MAX_CODE_CHARS,
                max_ai_chars=MAX_AI_CODE_CHARS,
            ), 400
        if request.endpoint in ("update_key", "update_github", "github_app_connect", "github_app_callback", "github_app_disconnect"):
            return redirect(url_for("account"))
        return redirect(url_for("index"))
    return render_template("error.html", message=str(e)), 400


@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    return render_template("error.html", message="פג תוקף הטופס. רענן את הדף ונסה שוב."), 400


@app.errorhandler(Exception)
def handle_exception(e):
    if isinstance(e, HTTPException):
        return render_template("error.html", message=e.description or e.name), e.code
    app.logger.exception("Unhandled error")
    return render_template("error.html", message="אירעה שגיאה פנימית. נסה שוב מאוחר יותר."), 500


# ==========================================
# 3. משתמשים והרשאות
# ==========================================
def current_user():
    uid = session.get("user_id")
    return db.session.get(User, uid) if uid else None


@app.context_processor
def inject_globals():
    user = current_user()
    pending_users_count = User.query.filter_by(is_approved=False).count() if user and user.is_admin else 0
    return {
        "current_user": user,
        "google_enabled": bool(os.environ.get("GOOGLE_CLIENT_ID")),
        "pending_users_count": pending_users_count,
    }


def login_required(f):
    """דורש משתמש מחובר ומאושר. משתמש שעוד לא אושר מופנה לדף ההמתנה."""

    @wraps(f)
    def wrapper(*args, **kwargs):
        user = current_user()
        if user is None:
            session.clear()
            return redirect(url_for("login_page"))
        if not (user.is_approved or user.is_admin):
            return redirect(url_for("pending_page"))
        return f(*args, **kwargs)

    return wrapper


def admin_required(f):
    @wraps(f)
    @login_required
    def wrapper(*args, **kwargs):
        if not current_user().is_admin:
            abort(403)
        return f(*args, **kwargs)

    return wrapper


def start_session(user):
    session.clear()  # מונע session fixation
    changed = False
    if ADMIN_USERNAME and user.username == ADMIN_USERNAME and user.password_hash and not user.is_admin:
        user.is_admin = True
        changed = True
    if user.is_admin and not user.is_approved:  # מנהל תמיד מאושר
        user.is_approved = True
        changed = True
    if changed:
        db.session.commit()
    session["user_id"] = user.id


def unique_username(email):
    base = re.sub(r"[^a-z0-9_]", "", email.split("@")[0].lower())[:24]
    if not base or not base[0].isalpha():
        base = "u" + base
    if len(base) < 3:
        base += "user"
    name = base
    while name in RESERVED or User.query.filter_by(username=name).first():
        name = f"{base}_{secrets.token_hex(2)}"
    return name


@app.route("/login", methods=["GET", "POST"])
def login_page():
    if request.method == "GET":
        if current_user():
            return redirect(url_for("index"))
        tab = request.args.get("tab")
        return render_template("login.html", tab=tab if tab in ("login", "register") else "login")

    username = (request.form.get("username") or "").strip().lower()
    password = request.form.get("password") or ""
    action = request.form.get("action")

    if action == "register":
        if not USERNAME_RE.match(username) or username in RESERVED:
            raise UserError("שם משתמש: 3-30 תווים, אנגלית קטנה/ספרות/_, מתחיל באות, ולא שם שמור.")
        if len(password) < 8:
            raise UserError("הסיסמה חייבת להכיל לפחות 8 תווים.")
        if User.query.filter_by(username=username).first():
            raise UserError("שם המשתמש כבר קיים במערכת. נסה שם אחר.")
        user = User(username=username, password_hash=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()
    elif action == "login":
        user = User.query.filter_by(username=username).first()
        # משתמשי Google אין להם password_hash, ולכן אי אפשר להיכנס אליהם עם סיסמה
        if not user or not user.password_hash or not check_password_hash(user.password_hash, password):
            raise UserError("שם משתמש או סיסמה שגויים.")
    else:
        abort(400)

    start_session(user)
    if action == "register":
        if user.is_approved or user.is_admin:
            flash("נרשמת בהצלחה, ברוך הבא!", "success")
        else:
            flash("נרשמת בהצלחה. החשבון ממתין לאישור מנהל.", "success")
    else:
        flash("התחברת בהצלחה.", "success")
    return redirect(url_for("index"))


@app.route("/auth/google")
def auth_google():
    if not os.environ.get("GOOGLE_CLIENT_ID"):
        abort(404)
    return google.authorize_redirect(url_for("auth_callback", _external=True))


@app.route("/auth/callback")
def auth_callback():
    token = google.authorize_access_token()
    info = token.get("userinfo") or {}
    sub = info.get("sub")
    email = (info.get("email") or "").strip().lower()
    if not sub or not email or not info.get("email_verified"):
        raise UserError("לא ניתן לאמת את חשבון Google (נדרש מייל מאומת).")

    user = User.query.filter_by(google_sub=sub).first()
    if not user:
        user = User(username=unique_username(email), email=email, google_sub=sub)
        db.session.add(user)
    if ADMIN_EMAIL and email == ADMIN_EMAIL:
        user.is_admin = True
    db.session.commit()

    start_session(user)
    return redirect(url_for("index"))


@app.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/pending")
def pending_page():
    """דף המתנה למשתמש שנרשם ועוד לא אושר."""
    user = current_user()
    if user is None:
        return redirect(url_for("login_page"))
    if user.is_approved or user.is_admin:
        return redirect(url_for("index"))
    return render_template("pending.html")


# ==========================================
# 4. מפתחות API (מוצפנים)
# ==========================================
def get_api_key(user, provider):
    if provider not in ai_providers.PROVIDERS:
        raise UserError("ספק AI לא נתמך.")
    row = ApiKey.query.filter_by(user_id=user.id, provider=provider).first()
    if not row:
        raise UserError(f"לא הוגדר מפתח API עבור {ai_providers.PROVIDERS[provider]}.")
    try:
        return fernet.decrypt(row.encrypted_key.encode()).decode()
    except InvalidToken:
        raise UserError("לא ניתן לפענח את המפתח השמור. הזן אותו מחדש.")


GITHUB_APP_PROVIDER = "github_app"  # שורת ApiKey שערכה JSON מוצפן: installation_id, login, type
GITHUB_APP_STATE_TTL = 600  # שניות


def get_github_app_link(user):
    """הקישור של המשתמש להתקנת ה-GitHub App ({installation_id, login, type}), או None."""
    row = ApiKey.query.filter_by(user_id=user.id, provider=GITHUB_APP_PROVIDER).first()
    if not row:
        return None
    try:
        data = json.loads(fernet.decrypt(row.encrypted_key.encode()).decode())
        data["installation_id"] = int(data["installation_id"])
    except (InvalidToken, ValueError, KeyError, TypeError):
        return None
    return data


def get_github_token(user):
    """טוקן קריאה ל-GitHub, או None.

    אם המשתמש חיבר את ה-App, רק הוא משמש: כשל בהנפקה או התקנה שבוטלה זורקים UserError, ואין נפילה שקטה ל-PAT
    (כדי שביטול הגישה ב-GitHub באמת יעצור את הגישה). טוקן ידני (provider=github) משמש רק כשאין חיבור App בכלל."""
    if ApiKey.query.filter_by(user_id=user.id, provider=GITHUB_APP_PROVIDER).first() is not None:
        link = get_github_app_link(user)
        if link is None:
            raise UserError("חיבור ה-GitHub App שלך פגום. נתק אותו וחבר מחדש.")
        if not github_client.app_config():
            raise UserError("החיבור ל-GitHub בלחיצה לא מוגדר כרגע בשרת. פנה למנהל, או נתק את החיבור וחבר טוקן.")
        try:
            return github_client.installation_token(link["installation_id"])
        except github_client.InstallationGone:
            raise UserError("ההתקנה של ה-App ב-GitHub הוסרה. נתק את החיבור וחבר מחדש.")
        except github_client.GithubError as e:
            app.logger.warning("GitHub App token failed for user %s: %s", user.id, e)
            raise UserError(f"הנפקת הגישה ל-GitHub דרך ה-App נכשלה: {e}")
    row = ApiKey.query.filter_by(user_id=user.id, provider="github").first()
    if not row:
        return None
    try:
        return fernet.decrypt(row.encrypted_key.encode()).decode()
    except InvalidToken:
        return None


def route_env(route):
    """משתני הסביבה של שרת אחד, מפוענחים: {name: value}."""
    out = {}
    for v in route.env_vars:
        try:
            out[v.name] = fernet.decrypt(v.encrypted_value.encode()).decode()
        except InvalidToken:
            continue
    return out


@app.post("/settings/github")
@login_required
def update_github():
    user = current_user()
    row = ApiKey.query.filter_by(user_id=user.id, provider="github").first()
    if request.form.get("action") == "delete":
        if row:
            db.session.delete(row)
            db.session.commit()
        flash("החיבור ל-GitHub נותק.", "success")
        return redirect(url_for("account"))
    token = (request.form.get("token") or "").strip()
    if not token:
        raise UserError("לא הוזן טוקן.")
    try:
        login = github_client.token_login(token)
    except github_client.GithubError as e:
        raise UserError(str(e))
    encrypted = fernet.encrypt(token.encode()).decode()
    if row:
        row.encrypted_key = encrypted
    else:
        db.session.add(ApiKey(user_id=user.id, provider="github", encrypted_key=encrypted))
    db.session.commit()
    flash(f"GitHub חובר בהצלחה (החשבון {login}).", "success")
    return redirect(url_for("account"))


@app.post("/settings/github/app/connect")
@login_required
def github_app_connect():
    cfg = github_client.app_config()
    if not cfg:
        raise UserError("החיבור ל-GitHub בלחיצה לא מוגדר בשרת. אפשר לחבר בעזרת טוקן.")
    state = secrets.token_urlsafe(32)
    session["gh_app_state"] = {"s": state, "u": current_user().id, "t": int(time.time())}
    return redirect(f"https://github.com/apps/{cfg['slug']}/installations/new?" + urlencode({"state": state}))


@app.get("/settings/github/app/callback")
@login_required
def github_app_callback():
    """ההפניה מ-GitHub אחרי התקנה. ה-installation_id בכתובת ניתן לניחוש, ולכן לא סומכים עליו:
    state מקשר את הבקשה לסשן שלנו, וה-code מוכיח שהמשתמש עצמו רשאי לגשת להתקנה הזו."""
    user = current_user()
    state = request.args.get("state", "")
    # שימוש חד-פעמי, ונצרך רק כשההפניה כוללת state: בקשה זרה (בלי state) לא מוחקת חיבור שנמצא בתהליך
    saved = session.pop("gh_app_state", None) if state else None
    code = request.args.get("code", "")
    action = request.args.get("setup_action", "")

    if action == "request":
        flash("הבקשה נשלחה וממתינה לאישור מנהל הארגון ב-GitHub. אחרי האישור אפשר לחבר שוב.", "info")
        return redirect(url_for("account"))
    if not state:  # למשל עדכון הרשאות ישירות מ-GitHub: אין מה לקשר
        flash("ההרשאות עודכנו ב-GitHub. כדי לחבר חשבון, השתמש בכפתור החיבור כאן.", "info")
        return redirect(url_for("account"))
    valid = (
        isinstance(saved, dict)
        and hmac.compare_digest(str(saved.get("s", "")).encode(), state.encode())
        and saved.get("u") == user.id
        and 0 <= time.time() - int(saved.get("t", 0)) <= GITHUB_APP_STATE_TTL
    )
    if not valid:
        raise UserError("בקשת החיבור פגה או לא תקפה. התחל מחדש מכפתור החיבור.")

    cfg = github_client.app_config()
    if not cfg:
        raise UserError("החיבור ל-GitHub בלחיצה לא מוגדר בשרת.")
    try:
        installation_id = int(request.args.get("installation_id", ""))
    except ValueError:
        raise UserError("GitHub לא החזיר מזהה התקנה. התחל מחדש.")
    if not code:
        raise UserError("GitHub לא החזיר אישור משתמש. ודא שב-App מופעל Request user authorization (OAuth) during installation.")

    try:
        user_token = github_client.exchange_code(code, cfg)  # נזרק מיד אחרי הבדיקות, לא נשמר
        gh_login = github_client.user_login(user_token)
        if installation_id not in github_client.user_installation_ids(user_token):
            raise UserError("ההתקנה הזו לא שייכת לחשבון ה-GitHub שלך.")
        info = github_client.installation_info(installation_id, cfg)
    except github_client.GithubError as e:
        raise UserError(str(e))
    # גרסה 1: רק החשבון האישי. בהתקנת ארגון SH היה מקבל גישה לכל ריפוזיטוריז ההתקנה, גם אלה שהמשתמש עצמו לא מורשה אליהם
    if info["type"] != "User" or not gh_login or info["login"].lower() != gh_login.lower():
        raise UserError("בשלב זה אפשר לחבר רק התקנה של החשבון האישי שלך ב-GitHub, לא של ארגון.")

    old = get_github_app_link(user)
    payload = json.dumps({"installation_id": installation_id, "login": info["login"], "type": info["type"]})
    encrypted = fernet.encrypt(payload.encode()).decode()
    row = ApiKey.query.filter_by(user_id=user.id, provider=GITHUB_APP_PROVIDER).first()
    if row:
        row.encrypted_key = encrypted
    else:
        db.session.add(ApiKey(user_id=user.id, provider=GITHUB_APP_PROVIDER, encrypted_key=encrypted))
    db.session.commit()
    if old and old["installation_id"] != installation_id:
        github_client.forget_installation(old["installation_id"])
    flash(f"GitHub חובר בהצלחה (החשבון {info['login']}).", "success")
    return redirect(url_for("account"))


@app.post("/settings/github/app/disconnect")
@login_required
def github_app_disconnect():
    user = current_user()
    link = get_github_app_link(user)
    row = ApiKey.query.filter_by(user_id=user.id, provider=GITHUB_APP_PROVIDER).first()
    if row:
        db.session.delete(row)
        db.session.commit()
    if link:
        github_client.forget_installation(link["installation_id"])
    flash("החיבור ל-GitHub נותק. להסרה מלאה של ה-App אפשר להיכנס להגדרות ב-GitHub.", "success")
    return redirect(url_for("account"))


@app.post("/settings/key")
@login_required
def update_key():
    user = current_user()
    provider = request.form.get("provider")
    if provider not in ai_providers.PROVIDERS:
        raise UserError("ספק AI לא נתמך.")
    row = ApiKey.query.filter_by(user_id=user.id, provider=provider).first()

    if request.form.get("action") == "delete":
        if row:
            db.session.delete(row)
    else:
        key = (request.form.get("api_key") or "").strip()
        if not key:
            raise UserError("לא הוזן מפתח.")
        encrypted = fernet.encrypt(key.encode()).decode()
        if row:
            row.encrypted_key = encrypted
        else:
            db.session.add(ApiKey(user_id=user.id, provider=provider, encrypted_key=encrypted))
    db.session.commit()
    flash("המפתח נמחק." if request.form.get("action") == "delete" else "המפתח נשמר בהצלחה.", "success")
    return redirect(url_for("account"))


# ==========================================
# 5. פריסה: תרגום (או Python ישיר) -> אישור מנהל -> הפעלה
# ==========================================
_reserved_cache = None


def reserved_route_names():
    """שמות שאסור לתת לשרת: הרשימה המפורשת + הסגמנט הראשון של כל route במערכת (נגזר מ-app.url_map).
    מחושב בבקשה הראשונה (אחרי שכל ה-routes נרשמו) ונשמר."""
    global _reserved_cache
    if _reserved_cache is None:
        derived = route_names.derive_reserved(app.url_map)
        missing = derived - route_names.RESERVED_STATIC
        if missing:  # route חדש נוסף למערכת: להוסיף ל-RESERVED_STATIC כדי שסקריפט המיגרציה ישמור עליו
            app.logger.warning("System routes missing from route_names.RESERVED_STATIC: %s", sorted(missing))
        _reserved_cache = frozenset(route_names.RESERVED_STATIC | derived)
    return _reserved_cache


def legacy_urls_enabled():
    """כתובות /<username>/<route_name> הישנות. ברירת מחדל: פעיל. כיבוי: LEGACY_USER_URLS=0 (או false/no/off)."""
    return (os.environ.get("LEGACY_USER_URLS") or "1").strip().lower() not in ("0", "false", "no", "off")


def validate_route_name(raw):
    """ולידציה מרכזית של שם שרת: פורמט, path traversal ושמות שמורים. מחזיר את השם המנורמל או זורק UserError."""
    try:
        return route_names.check_route_name((raw or "").strip().lower(), reserved_route_names())
    except route_names.RouteNameError as e:
        raise UserError(str(e))


def assert_route_name_free(name):
    """הכתובת הציבורית היא /<name> ולכן השם ייחודי גלובלית. UserError אם תפוס (ה-DB מגן בנוסף דרך full_path unique)."""
    if Route.query.filter(sa_or(Route.full_path == f"/{name}", Route.route_name == name)).first():
        raise UserError(f"השם {name} כבר תפוס. שמות שרתים ייחודיים לכל המשתמשים, בחר שם אחר.")
    if legacy_urls_enabled():
        prefix = f"/{name}/"
        shadow = Route.query.filter(
            sa_or(Route.legacy_path.startswith(prefix, autoescape=True), Route.full_path.startswith(prefix, autoescape=True))
        ).first()
        if shadow:  # השם הוא שם משתמש עם כתובות ישנות פעילות; שרת חדש בשם הזה היה מסתיר אותן
            raise UserError(f"השם {name} תפוס (משמש כתובות ישנות של משתמש בשם הזה). בחר שם אחר.")


def strip_fences(text):
    m = re.search(r"```(?:python|py)?\s*\n(.*?)```", text, re.DOTALL)
    return (m.group(1) if m else text).strip()


def validate_python(code):
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        raise UserError(f"שגיאת תחביר בקוד (שורה {e.lineno}): {e.msg}")
    if not bundles._defines_bp(tree):
        raise UserError("הקוד חייב להגדיר אפליקציית Flask בשם app, למשל: app = Flask(__name__) (או Blueprint בשם bp).")


@app.post("/deploy")
@login_required
def deploy_server():
    user = current_user()

    route_name = validate_route_name(request.form.get("route_name"))
    # פריסה חוזרת של שרת קיים של אותו משתמש מעדכנת אותו; שם חדש חייב להיות פנוי גלובלית (בודקים לפני קריאת ה-AI)
    route = Route.query.filter_by(user_id=user.id, route_name=route_name).first()
    if route is None:
        assert_route_name_free(route_name)

    mode = request.form.get("source_mode")
    gh_meta = None
    if mode == "repo":  # ריפו או תיקייה שלמה מ-GitHub (כמה קבצים)
        try:
            repo, subdir, ref = github_client.parse_repo_input(
                request.form.get("github_url"), request.form.get("github_subdir"), request.form.get("github_ref")
            )
            info = github_client.fetch_repo(repo, ref, subdir, get_github_token(user))
            entry = bundles.pick_entry(info["files"], request.form.get("github_entry"))
            bundles.validate(info["files"], entry)
        except (github_client.GithubError, bundles.BundleError) as e:
            raise UserError(str(e))
        source_lang = "Python"
        final_code = bundles.pack(info["files"], entry)
        gh_meta = {"repo": repo, "path": subdir, "ref": ref, "sha": info["sha"]}
    else:
        force_ai = False
        if mode == "github":  # קובץ בודד מ-GitHub
            try:
                repo, path, ref = github_client.parse_input(
                    request.form.get("github_url"), request.form.get("github_path"), request.form.get("github_ref")
                )
                info = github_client.fetch_file(repo, path, ref, get_github_token(user))
            except github_client.GithubError as e:
                raise UserError(str(e))
            source_lang = EXT_LANG.get(os.path.splitext(path)[1].lower())
            if not source_lang:
                raise UserError("סוג הקובץ לא נתמך. סיומות נתמכות: " + ", ".join(sorted(EXT_LANG)))
            code = info["content"].replace("\r\n", "\n")
            gh_meta = {"repo": repo, "path": path, "ref": ref, "sha": info["sha"]}
        else:
            source_lang = (request.form.get("source_lang") or "").strip()
            if not LANG_RE.match(source_lang):
                raise UserError("שפת מקור לא תקינה.")
            code = request.form.get("code") or ""
            force_ai = request.form.get("force_ai") == "1"

        if not code.strip():
            raise UserError("הקובץ בריפו ריק." if gh_meta else "לא הוזן קוד.")
        use_ai = not (source_lang.lower() in PY_LANGS and not force_ai)
        limit = MAX_AI_CODE_CHARS if use_ai else MAX_CODE_CHARS
        if len(code) > limit:
            hint = " אפשר לפצל לכמה שרתים קטנים, או להשתמש בקוד Python ישירות (בלי AI)." if use_ai else ""
            raise UserError(f"הקוד ארוך מדי: {len(code):,} תווים, והמקסימום כאן הוא {limit:,}.{hint}")

        if not use_ai:
            final_code = code  # Python: אין צורך ב-AI
        else:
            provider = request.form.get("provider")
            api_key = get_api_key(user, provider)
            prompt = ai_providers.build_translation_prompt(source_lang, code)
            try:
                final_code = strip_fences(ai_providers.generate(provider, api_key, prompt))
            except ai_providers.ProviderError as e:
                raise UserError(f"שגיאה מספק ה-AI: {e}")
        validate_python(final_code)

    if not route:
        route = Route(user_id=user.id, route_name=route_name, full_path=f"/{route_name}")
        db.session.add(route)
    route.source_lang = source_lang
    route.pending_code = final_code
    if route.live_code is None:
        route.status = "pending"
    if gh_meta:
        if route.source is None:
            route.source = RouteSource(**gh_meta)
        else:
            for key, value in gh_meta.items():
                setattr(route.source, key, value)
    else:
        route.source = None  # הדבקה ידנית מנתקת את הקישור ל-GitHub
    try:
        db.session.commit()
    except IntegrityError:  # race: משתמש אחר תפס את השם בין הבדיקה לשמירה (full_path unique)
        db.session.rollback()
        raise UserError(f"השם {route_name} נתפס הרגע על ידי שרת אחר. בחר שם אחר.")

    activate(route)  # משתמש מאושר: השרת עולה מיד, בלי אישור מנהל
    flash(f"השרת פעיל בכתובת {route.full_path}", "success")
    return redirect(url_for("index"))


def make_diff(old, new, from_label="לפני", to_label="אחרי"):
    return [
        line.rstrip("\n")
        for line in difflib.unified_diff(old.splitlines(True), new.splitlines(True), from_label, to_label, n=3)
    ]


def get_editable_route(route_id):
    """שרת שהמשתמש רשאי לערוך (הבעלים או מנהל) ויש בו קוד."""
    user = current_user()
    route = db.session.get(Route, route_id)
    if not route or (route.user_id != user.id and not user.is_admin):
        abort(404)
    if not (route.pending_code or route.live_code):
        abort(404)
    return route
def render_edit(route, code, status=200, **extra):
    user = current_user()
    bundle = None
    if bundles.is_bundle(code):
        entry, files = bundles.unpack(code)
        bundle = {"entry": entry, "files": files}
    html = render_template(
        "edit.html",
        route=route,
        code=code,
        bundle=bundle,
        max_code_chars=MAX_CODE_CHARS,
        providers=ai_providers.PROVIDERS,
        saved_providers={k.provider for k in user.api_keys},
        env_names=sorted(v.name for v in route.env_vars),
        **extra,
    )
    return html, status


@app.route("/edit/<int:route_id>", methods=["GET", "POST"])
@login_required
def edit_route(route_id):
    """עריכת הקוד של שרת קיים. משתמש רגיל: השינוי ממתין לאישור והגרסה הפעילה ממשיכה לרוץ. מנהל: מיידי."""
    user = current_user()
    route = get_editable_route(route_id)
    current = route.pending_code or route.live_code

    if request.method == "GET":
        return render_edit(route, current)

    is_bundle = bundles.is_bundle(current)
    code = current if is_bundle else (request.form.get("code") or "").replace("\r\n", "\n")
    try:
        if is_bundle:
            entry, old_files = bundles.unpack(current)
            try:
                files = json.loads(request.form.get("bundle_json") or "")
                if not isinstance(files, dict):
                    raise ValueError
            except ValueError:
                raise UserError("נתוני הקבצים לא התקבלו כראוי. רענן את הדף ונסה שוב.")
            files = {p: str(c).replace("\r\n", "\n") for p, c in sorted(files.items())}
            code = bundles.pack(files, entry)  # נשמר כאן כדי שהעריכה לא תאבד אם יש שגיאה
            if set(files) != set(old_files):
                raise UserError("אי אפשר להוסיף או למחוק קבצים בעורך. לשינוי מבנה, ייבא מחדש מ-GitHub.")
            try:
                bundles.validate(files, entry)
            except bundles.BundleError as e:
                raise UserError(str(e))
            unchanged = files == old_files
        else:
            if not code.strip():
                raise UserError("הקוד ריק.")
            if len(code) > MAX_CODE_CHARS:
                raise UserError(f"הקוד ארוך מדי: {len(code):,} תווים, והמקסימום הוא {MAX_CODE_CHARS:,}.")
            validate_python(code)
            unchanged = code.strip() == current.strip()
        if unchanged:
            flash("לא בוצעו שינויים.", "info")
            return redirect(url_for("edit_route", route_id=route.id))

        route.pending_code = code
        db.session.commit()
        activate(route)
        flash("השינויים נשמרו והשרת עודכן.", "success")
    except UserError as e:
        # נשארים בעורך עם הקוד שהוקלד, כדי שלא יאבד
        db.session.rollback()
        flash(str(e), "danger")
        return render_edit(route, code, 400)
    return redirect(url_for("index"))


@app.post("/edit/<int:route_id>/ai")
@login_required
def edit_route_ai(route_id):
    """מבקש מה-AI לשנות את הקוד שבעורך. התוצאה רק נטענת לעורך להצגה, ושום דבר לא נשמר עד לחיצה על שמירה."""
    user = current_user()
    route = get_editable_route(route_id)
    if bundles.is_bundle(route.pending_code or route.live_code):
        flash("עריכה בעזרת AI זמינה רק לשרתים של קובץ בודד.", "danger")
        return redirect(url_for("edit_route", route_id=route.id))
    code = (request.form.get("code") or route.pending_code or route.live_code or "").replace("\r\n", "\n")
    instruction = (request.form.get("instruction") or "").strip()
    try:
        if not instruction:
            raise UserError("כתוב מה לשנות בקוד.")
        if len(instruction) > 2000:
            raise UserError("ההוראה ארוכה מדי (עד 2,000 תווים).")
        if len(code) > MAX_AI_CODE_CHARS:
            raise UserError(f"הקוד ארוך מדי לעריכה ב-AI ({len(code):,} תווים, המקסימום {MAX_AI_CODE_CHARS:,}). אפשר לערוך אותו ידנית.")
        provider = request.form.get("provider")
        api_key = get_api_key(user, provider)
        try:
            raw = ai_providers.generate(provider, api_key, ai_providers.build_edit_prompt(instruction, code))
        except ai_providers.ProviderError as e:
            raise UserError(f"שגיאה מספק ה-AI: {e}")
        new_code = strip_fences(raw)
        validate_python(new_code)
    except UserError as e:
        flash(str(e), "danger")
        return render_edit(route, code, 400, instruction=instruction)

    diff_lines = make_diff(code, new_code, "לפני ההצעה", "הצעת ה-AI")
    return render_edit(route, new_code, instruction=instruction, ai_diff=diff_lines, original_code=code)


def drop_route_cache(route):
    """משחרר את השרת מה-cache של ה-worker הנוכחי. ב-workers אחרים מספיק שהשורה נמחקה מה-DB: הבקשות הבאות יקבלו 404."""
    old = _subapps.pop(route.id, None)
    if old and old[2]:
        bundles.unload(old[2])


@app.post("/delete/<int:route_id>")
@login_required
def delete_route(route_id):
    user = current_user()
    route = db.session.get(Route, route_id)
    if not route or (route.user_id != user.id and not user.is_admin):
        abort(404)
    path = route.full_path
    owner_id = route.user_id
    drop_route_cache(route)
    db.session.delete(route)  # היומנים נמחקים יחד איתו (cascade)
    db.session.commit()
    flash(f"השרת {path} נמחק.", "success")
    if owner_id != user.id:  # מנהל שמחק שרת של משתמש אחר חוזר לדף המשתמש
        return redirect(url_for("admin_user", user_id=owner_id))
    return redirect(url_for("index"))


@app.post("/sync/<int:route_id>")
@login_required
def sync_route(route_id):
    """מושך את הגרסה העדכנית מ-GitHub (קובץ בודד או ריפו מרובה קבצים). כמו כל שינוי קוד: ממתין לאישור מנהל (מנהל: מיידי)."""
    user = current_user()
    route = get_editable_route(route_id)
    src = route.source
    if src is None:
        abort(404)
    current = route.pending_code or route.live_code
    is_bundle = bundles.is_bundle(current)
    token = get_github_token(route.owner)
    try:
        if is_bundle:
            info = github_client.fetch_repo(src.repo, src.ref, src.path, token)
        elif src.path.lower().endswith(".py"):
            info = github_client.fetch_file(src.repo, src.path, src.ref, token)
        else:
            raise UserError("סנכרון אוטומטי נתמך רק לקבצי Python ולריפו מרובה קבצים. לשפות אחרות יש לייבא מחדש מטופס הפריסה.")
    except github_client.GithubError as e:
        raise UserError(str(e))
    if info["sha"] == src.sha:
        flash("אין שינויים בריפו מאז הסנכרון האחרון.", "info")
        return redirect(url_for("edit_route", route_id=route.id))

    if is_bundle:
        old_entry, _ = bundles.unpack(current)
        try:
            entry = old_entry if old_entry in info["files"] else bundles.pick_entry(info["files"])
            bundles.validate(info["files"], entry)
        except bundles.BundleError as e:
            raise UserError(str(e))
        code = bundles.pack(info["files"], entry)
    else:
        code = info["content"].replace("\r\n", "\n")
        if not code.strip():
            raise UserError("הקובץ בריפו ריק.")
        if len(code) > MAX_CODE_CHARS:
            raise UserError(f"הקובץ ארוך מדי: {len(code):,} תווים, והמקסימום הוא {MAX_CODE_CHARS:,}.")
        validate_python(code)

    src.sha = info["sha"]
    route.pending_code = code
    db.session.commit()
    activate(route)
    flash("נמשכה גרסה חדשה מ-GitHub והשרת עודכן.", "success")
    return redirect(url_for("index"))


@app.post("/edit/<int:route_id>/env")
@login_required
def set_env_var(route_id):
    route = get_editable_route(route_id)
    name = (request.form.get("name") or "").strip()
    value = (request.form.get("value") or "").strip()
    try:
        if not ENV_NAME_RE.match(name):
            raise UserError("שם משתנה: אותיות אנגליות, ספרות ו-_ בלבד, בלי להתחיל בספרה (עד 64 תווים).")
        if not value:
            raise UserError("הערך ריק.")
        if len(value) > MAX_ENV_VALUE:
            raise UserError(f"הערך ארוך מדי (עד {MAX_ENV_VALUE:,} תווים).")
        row = EnvVar.query.filter_by(route_id=route.id, name=name).first()
        if row is None and len(route.env_vars) >= MAX_ENV_VARS:
            raise UserError(f"אפשר להגדיר עד {MAX_ENV_VARS} משתנים לשרת.")
    except UserError as e:
        flash(str(e), "danger")
        return redirect(url_for("edit_route", route_id=route.id))

    encrypted = fernet.encrypt(value.encode()).decode()
    if row:
        row.encrypted_value = encrypted
    else:
        db.session.add(EnvVar(route_id=route.id, name=name, encrypted_value=encrypted))
    if route.live_code:
        route.live_version += 1  # מרענן את ה-cache בכל ה-workers: השרת יעלה מחדש עם הערך החדש
    db.session.commit()
    flash(f"המשתנה {name} נשמר.", "success")
    return redirect(url_for("edit_route", route_id=route.id))


@app.post("/edit/<int:route_id>/env/delete")
@login_required
def delete_env_var(route_id):
    route = get_editable_route(route_id)
    name = (request.form.get("name") or "").strip()
    row = EnvVar.query.filter_by(route_id=route.id, name=name).first()
    if row:
        db.session.delete(row)
        if route.live_code:
            route.live_version += 1
        db.session.commit()
        flash(f"המשתנה {name} נמחק.", "success")
    return redirect(url_for("edit_route", route_id=route.id))


# --- הרצת השרתים הווירטואליים: כל אחד כאפליקציית Flask קטנה משלו, נטענת מה-DB לפי דרישה ---
_subapps = {}  # route_id -> (live_version, flask_app). cache לכל worker, מתרענן לפי live_version
def build_subapp(code, label, ident, env=None, tag=0):
    """בונה אפליקציית WSGI מקוד שרת. מחזיר (אפליקציה, שם חבילה לשחרור, או None לשרת של קובץ בודד)."""
    if bundles.is_bundle(code):
        _, files = bundles.unpack(code)
        deps.ensure_dependencies(bundles.external_imports_code(files))
        try:
            return bundles.load(code, ident, tag, env)
        except bundles.BundleError as e:
            raise RuntimeError(str(e))
    deps.ensure_dependencies(code)
    module = ModuleType(f"user_route_{ident}")
    module.__dict__["env"] = MappingProxyType(dict(env or {}))  # משתני הסביבה של השרת הזה בלבד
    exec(compile(code, f"<user:{label}>", "exec"), module.__dict__)
    bp = getattr(module, "bp", None)
    if isinstance(bp, Blueprint):
        sub = Flask(f"user_route_{ident}")
        sub.register_blueprint(bp)
        return sub, None
    sub = getattr(module, "app", None)
    if sub is None:
        sub = getattr(module, "application", None)
    if sub is None or not callable(sub):
        raise RuntimeError("לא נמצא app (אפליקציית Flask) או bp (Blueprint) בקוד")
    return sub, None
def activate(route):
    """מעביר קוד ממתין ל-live. נקרא רק אחרי אישור מנהל (או כשהמנהל עצמו פורס)."""
    ctx = RequestLogCtx(route.id)  # פלט ושגיאות של טעינת הבדיקה משויכים לשרת הזה
    token = _req_ctx.set(ctx)
    failure = None
    try:
        _, pkg = build_subapp(route.pending_code, route.full_path, route.id, route_env(route), tag="dry")  # בדיקת טעינה
        if pkg:
            bundles.unload(pkg)  # זו הייתה רק בדיקה
    except Exception as e:
        failure = e
    finally:
        _req_ctx.reset(token)
    if failure is not None:
        ctx.add_system("activate load error", failure)
    flush_request_logs(ctx)
    if failure is not None:
        raise UserError(f"הקוד לא נטען: {type(failure).__name__}: {str(failure)[:200]}")
    route.live_code = route.pending_code
    route.pending_code = None
    route.live_version += 1
    route.status = "active"
    db.session.commit()
def get_subapp(route):
    cached = _subapps.get(route.id)
    if cached and cached[0] == route.live_version:
        return cached[1]
    sub, pkg = build_subapp(route.live_code, route.full_path, route.id, route_env(route), tag=route.live_version)
    if cached and cached[2]:
        bundles.unload(cached[2])  # שחרור הגרסה הקודמת של חבילה מרובת קבצים
    _subapps[route.id] = (route.live_version, sub, pkg)
    return sub


# ==========================================
# יומנים: כל אירוע של בקשה משויך ל-route_id ול-request_id
# ==========================================
# הבקשה צוברת אירועים בזיכרון (access, print/stdout/stderr, logging, שגיאות) ושומרת אותם בסוף ב-commit אחד.
# הפורמט נשמר בעמודת Log.message הקיימת (בלי שינוי schema). הפורמט הישן "Method: .. | Status: .. | IP: .." עדיין נתמך בתצוגה.
#   access:  Method: GET | Status: 200 | IP: 1.2.3.4 | Path: /x | Req: <id> | Size: 123
#   אחר:     Kind: app|log|system | Req: <id> | [Src/Level/Logger: ..] | Msg: <טקסט חופשי, תמיד אחרון>
# מגבלה ידועה: ה-context הוא ContextVar, ולכן print/logging של thread שהקוד פתח בעצמו לא משויך לשרת (נשאר רק ב-stdout המקורי).
MAX_LOGS_PER_ROUTE = int(os.environ.get("MAX_LOGS_PER_ROUTE", "1000"))
MAX_EVENTS_PER_REQUEST = int(os.environ.get("MAX_LOG_EVENTS_PER_REQUEST", "50"))  # אירועי app/logging בבקשה אחת (access ושגיאות מערכת נוספים מעבר לכך)
MAX_LOG_MESSAGE = int(os.environ.get("MAX_LOG_MESSAGE_CHARS", "2000"))  # אורך מרבי של הודעה שלמה
MAX_LOG_TEXT = 500  # אורך הטקסט החופשי (לפני traceback)
MAX_LOG_TRACEBACK = 1200  # סוף ה-traceback בלבד: שם נמצאת השגיאה עצמה
VIEW_LOGS_LIMIT = 200

_req_ctx = contextvars.ContextVar("request_log_ctx", default=None)
_suppress_capture = contextvars.ContextVar("request_log_suppress", default=False)


def _clean(value, limit=200):
    """ערך שמגיע מהמשתמש (נתיב, שם logger) בתוך כותרת ההודעה: בלי תווי בקרה ובלי ' | ', כדי שלא יזייף שדות."""
    return "".join(ch for ch in str(value) if ch.isprintable()).replace("|", "¦")[:limit]


class RequestLogCtx:
    """האירועים של בקשה אחת (או הפעלה אחת) של שרת אחד."""

    def __init__(self, route_id):
        self.route_id = route_id
        self.request_id = secrets.token_hex(5)
        self.events = []  # [(timestamp, message)]
        self.dropped = 0
        self._bufs = {"stdout": "", "stderr": ""}
        self._lock = threading.Lock()

    def _add(self, message, force=False):
        with self._lock:
            if not force and len(self.events) >= MAX_EVENTS_PER_REQUEST:
                self.dropped += 1
                return
            self.events.append((utcnow(), message[:MAX_LOG_MESSAGE]))

    def _event(self, kind, text, **fields):
        head = " | ".join([f"Kind: {kind}", f"Req: {self.request_id}"] + [f"{k}: {_clean(v, 100)}" for k, v in fields.items() if v])
        return f"{head} | Msg: {text}"

    def add_stream(self, src, data):
        """print / stdout / stderr: אירוע לכל שורה שלמה. שורה חלקית ממתינה עד שתושלם (או עד סוף הבקשה)."""
        with self._lock:
            full = len(self.events) >= MAX_EVENTS_PER_REQUEST
        if full:  # בלי לבנות מחרוזות ענקיות אחרי שהגענו למגבלה
            with self._lock:
                self.dropped += data.count("\n")
            return
        with self._lock:
            lines = (self._bufs[src] + data).split("\n")
            self._bufs[src] = lines.pop()
            if len(self._bufs[src]) > MAX_LOG_TEXT:  # שורה ארוכה בלי ירידת שורה
                lines.append(self._bufs[src])
                self._bufs[src] = ""
        for line in lines:
            line = line.rstrip("\r")
            if line.strip():
                self._add(self._event("app", line[:MAX_LOG_TEXT], Src=src))

    def add_log(self, record):
        try:
            text = record.getMessage()
        except Exception:
            text = str(record.msg)
        text = text[:MAX_LOG_TEXT]
        if record.exc_info and record.exc_info[0] is not None:
            text += "\n" + "".join(traceback.format_exception(*record.exc_info))[-MAX_LOG_TRACEBACK:]
        self._add(self._event("log", text, Level=record.levelname, Logger=record.name))

    def add_system(self, text, exc=None):
        """שגיאת runtime / load / activate. נשמרת גם כשהגענו למגבלת האירועים."""
        text = text[:MAX_LOG_TEXT]
        if exc is not None:
            text += f": {type(exc).__name__}: {str(exc)[:300]}"
            tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
            text += "\n" + tb[-MAX_LOG_TRACEBACK:]
        self._add(self._event("system", text), force=True)

    def add_access(self, method, status, ip, path, size):
        # בכוונה בלי query string: הוא עלול להכיל סודות
        parts = [f"Method: {_clean(method, 10)}", f"Status: {int(status)}", f"IP: {_clean(ip or '-', 64)}", f"Path: {_clean(path)}", f"Req: {self.request_id}"]
        if size is not None:
            parts.append(f"Size: {int(size)}")
        self._add(" | ".join(parts), force=True)

    def close(self):
        for src, rest in self._bufs.items():
            if rest.strip():
                self._add(self._event("app", rest[:MAX_LOG_TEXT], Src=src))
            self._bufs[src] = ""
        if self.dropped:
            self._add(self._event("system", f"{self.dropped} אירועים נוספים לא נשמרו (מגבלה: {MAX_EVENTS_PER_REQUEST} לבקשה)"), force=True)
            self.dropped = 0


class _StreamTee:
    """עוטף את stdout/stderr: הפלט תמיד ממשיך ליעד המקורי, ובנוסף נצבר אם יש request context פעיל."""

    _is_req_tee = True

    def __init__(self, target, name):
        self._target, self._name = target, name

    def write(self, data):
        n = self._target.write(data)
        ctx = _req_ctx.get()
        if ctx is not None and isinstance(data, str) and not _suppress_capture.get():
            try:
                ctx.add_stream(self._name, data)
            except Exception:
                pass
        return n

    def writelines(self, lines):
        for line in lines:
            self.write(line)

    def __getattr__(self, name):
        return getattr(self._target, name)


def _capturing_handle(self, record):
    """אירוע logging נתפס פעם אחת, ברמת ה-Logger. בזמן הטיפול בו כתיבת handler ל-stderr (שעטוף ב-tee) לא נספרת שוב."""
    ctx = _req_ctx.get()
    if ctx is None or _suppress_capture.get():
        return _capturing_handle.orig(self, record)
    if not self.disabled:
        try:
            ctx.add_log(record)
        except Exception:
            pass
    token = _suppress_capture.set(True)
    try:
        return _capturing_handle.orig(self, record)
    finally:
        _suppress_capture.reset(token)


def install_log_capture():
    """idempotent. נקרא פעם אחת בעלייה."""
    for name in ("stdout", "stderr"):
        if not getattr(getattr(sys, name), "_is_req_tee", False):
            setattr(sys, name, _StreamTee(getattr(sys, name), name))
    if not hasattr(logging.Logger.handle, "orig"):
        _capturing_handle.orig = logging.Logger.handle
        logging.Logger.handle = _capturing_handle


@contextlib.contextmanager
def _system_logging():
    """לוגים של המערכת עצמה (גם כשהם נכתבים בזמן בקשה) לא נכנסים ליומן של השרת."""
    token = _suppress_capture.set(True)
    try:
        yield
    finally:
        _suppress_capture.reset(token)


install_log_capture()


def prune_logs(route_id, session=None):
    """משאיר רק את היומנים האחרונים של שרת, כדי שהמסד לא יתנפח (חשוב במסד חינמי)."""
    s = session or db.session
    cutoff = s.query(Log.id).filter_by(route_id=route_id).order_by(Log.id.desc()).offset(MAX_LOGS_PER_ROUTE).limit(1).scalar()
    if cutoff:
        s.query(Log).filter(Log.route_id == route_id, Log.id <= cutoff).delete(synchronize_session=False)
        s.commit()


def flush_request_logs(ctx):
    """שמירה מרוכזת: commit אחד לכל האירועים. session נפרד, כדי לא לשמור בטעות שינויים פתוחים של db.session."""
    ctx.close()
    if not ctx.events:
        return
    try:
        with Session(db.engine) as s:
            s.add_all([Log(route_id=ctx.route_id, timestamp=ts, message=msg) for ts, msg in ctx.events])
            s.commit()
            if random.random() < min(1.0, 0.02 * len(ctx.events)):  # ניקוי מדי פעם, לא בכל בקשה
                prune_logs(ctx.route_id, s)
    except Exception:
        with _system_logging():
            app.logger.exception("Failed to write logs")


_LOG_KEYS = ("Kind", "Method", "Status", "IP", "Path", "Req", "Size", "Src", "Level", "Logger")


def parse_log(row):
    """מפענח שורת Log (פורמט ישן וחדש) לשדות לתצוגה. שדה שלא קיים בהודעה נשאר ריק."""
    msg = row.message or ""
    head, body = msg, ""
    if msg.startswith("Kind: "):  # רק הפורמט החדש מכיל Msg חופשי; הטקסט שאחרי Msg לא מפוענח
        head, _, body = msg.partition(" | Msg: ")
    fields, extra = {}, []
    for part in head.split(" | "):
        key, sep, value = part.partition(": ")
        if sep and key in _LOG_KEYS and key not in fields:
            fields[key] = value
        else:
            extra.append(part)
    if "Method" in fields and "Status" in fields:
        kind = "access"
    elif fields.get("Kind") in ("app", "log", "system"):
        kind = fields["Kind"]
    else:
        kind = "raw"
    req = fields.get("Req", "")
    if kind == "access":
        bits = [fields.get("Path", ""), fields.get("IP", "")]
        if fields.get("Size"):
            bits.append(f"{fields['Size']} B")
        if req:
            bits.append(f"req {req}")
        meta = " · ".join(b for b in bits + extra if b)
    elif kind == "raw":
        meta = msg
    else:
        meta = (f"req {req} · " if req else "") + body
    level = fields.get("Level", "")
    status = fields.get("Status", "")
    if kind == "access":
        tone = "bad" if status[:1] == "5" else "warn" if status[:1] == "4" else ""
    elif kind == "system" or level in ("ERROR", "CRITICAL"):
        tone = "bad"
    elif level == "WARNING":
        tone = "warn"
    else:
        tone = ""
    return {
        "kind": kind,
        "timestamp": row.timestamp,
        "method": fields.get("Method", "") if kind == "access" else (fields.get("Src", "") if kind == "app" else ("log" if kind == "log" else "")),
        "status": status,
        "level": level,
        "label": {"app": "App", "log": level or "Log", "system": "System"}.get(kind, ""),
        "req": req,
        "meta": meta,
        "tone": tone,
    }


HTTP_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE"]


@app.route("/healthz")
def healthz():
    """בדיקת תקינות ל-Render (Health Check Path). לא נוגע במסד הנתונים."""
    return "ok", 200, {"Cache-Control": "no-store"}


@app.template_filter("timeago")
def timeago(dt):
    if not dt:
        return ""
    secs = max(0, int((utcnow() - dt).total_seconds()))
    if secs < 60:
        return "הרגע"
    mins = secs // 60
    if mins < 60:
        return "לפני דקה" if mins == 1 else f"לפני {mins} דקות"
    hours = mins // 60
    if hours < 24:
        return "לפני שעה" if hours == 1 else f"לפני {hours} שעות"
    days = hours // 24
    if days < 30:
        return "לפני יום" if days == 1 else f"לפני {days} ימים"
    return dt.strftime("%d/%m/%Y")


def strip_admin_cookie_from_request(environ):
    """מסיר את session cookie של מערכת הניהול מהבקשה לפני שהיא מגיעה לקוד משתמש (שאר העוגיות והכותרות נשארות)."""
    kept = [c for c in environ.get("HTTP_COOKIE", "").split(";") if c.split("=", 1)[0].strip() != app.config["SESSION_COOKIE_NAME"]]
    if "".join(kept).strip():
        environ["HTTP_COOKIE"] = ";".join(kept).strip()
    else:
        environ.pop("HTTP_COOKIE", None)


def strip_admin_cookie_from_response(response):
    """מסיר Set-Cookie שמנסה להגדיר או למחוק את session cookie של מערכת הניהול (שאר ה-Set-Cookie נשארים)."""
    cookies = response.headers.getlist("Set-Cookie")
    del response.headers["Set-Cookie"]
    for cookie in cookies:
        if cookie.split("=", 1)[0].strip() != app.config["SESSION_COOKIE_NAME"]:
            response.headers.add("Set-Cookie", cookie)


def _servable(query):
    """שרת פעיל של משתמש מאושר (משתמש שהושעה: השרתים שלו לא מוגשים)."""
    return query.filter(Route.status == "active", sa_or(User.is_approved.is_(True), User.is_admin.is_(True)))


def find_route_by_name(name):
    return _servable(Route.query.join(User).filter(Route.full_path == f"/{name}")).first()


def find_route_by_legacy_path(path):
    # legacy_path ריק = עדיין לא עברה מיגרציה, ואז full_path הוא עדיין הכתובת הישנה
    cond = sa_or(Route.legacy_path == path, sa_and(Route.legacy_path.is_(None), Route.full_path == path))
    return _servable(Route.query.join(User).filter(cond)).first()


def resolve_route(first, rest):
    """(route, script_name, path_info) או None. הכתובת החדשה /<route_name>/... קודמת; אחריה הישנה /<username>/<route_name>/..."""
    route = find_route_by_name(first)
    if route is not None:
        return route, f"/{first}", "/" + rest
    if legacy_urls_enabled() and rest:
        second, _, subrest = rest.partition("/")
        if ROUTE_RE.match(second):
            legacy = f"/{first}/{second}"
            route = find_route_by_legacy_path(legacy)
            if route is not None:
                return route, legacy, "/" + subrest
    return None


@app.route("/<route_name>", defaults={"rest": ""}, methods=HTTP_METHODS, strict_slashes=False)
@app.route("/<route_name>/<path:rest>", methods=HTTP_METHODS)
@csrf.exempt  # ה-webhooks החיצוניים לא יכולים לשלוח CSRF token
def dispatch(route_name, rest):
    # routes של המערכת (/edit/<abc>, /deploy ב-GET וכו') שנפלו לכאן, וסגמנטים לא תקינים (favicon.ico, wp-login.php): בלי פנייה ל-DB
    if route_name in reserved_route_names() or not ROUTE_RE.match(route_name):
        abort(404)
    resolved = resolve_route(route_name, rest)
    if resolved is None:
        abort(404)
    route, script_name, path_info = resolved
    if not route.live_code:
        abort(404)
    # ה-context נקבע לפני הטעינה וההרצה של קוד המשתמש: גם פלט בזמן load משויך לשרת ולבקשה הנכונים
    ctx = RequestLogCtx(route.id)
    token = _req_ctx.set(ctx)
    phase, response, failure = "load", None, None
    try:
        sub = get_subapp(route)
        phase = "run"
        environ = request.environ.copy()
        environ["SCRIPT_NAME"] = request.script_root + script_name
        environ["PATH_INFO"] = path_info
        strip_admin_cookie_from_request(environ)
        response = Response.from_app(sub, environ, buffered=True)
        strip_admin_cookie_from_response(response)
        response.headers["X-Content-Type-Options"] = "nosniff"
    except Exception as e:
        failure = e
        ctx.add_system(f"{phase} error", e)
        with _system_logging():
            app.logger.exception("Sub-server failed (%s): %s", phase, route.full_path)
    finally:
        _req_ctx.reset(token)
    size = None
    if response is not None:
        try:
            size = response.calculate_content_length()
        except Exception:
            pass
    ctx.add_access(request.method, 502 if failure is not None else response.status_code, request.remote_addr, request.path, size)
    flush_request_logs(ctx)
    if failure is not None:
        abort(502)
    return response


# ==========================================
# 6. לוח בקרה, אישורי מנהל ולוגים
# ==========================================
@app.route("/new")
@login_required
def new_server():
    user = current_user()
    return render_template(
        "new.html",
        providers=ai_providers.PROVIDERS,
        saved_providers={k.provider for k in user.api_keys},
        max_code_chars=MAX_CODE_CHARS,
        max_ai_chars=MAX_AI_CODE_CHARS,
    )


@app.route("/account")
@login_required
def account():
    user = current_user()
    return render_template(
        "account.html",
        providers=ai_providers.PROVIDERS,
        saved_providers={k.provider for k in user.api_keys},
        gh_app=get_github_app_link(user),
        gh_app_enabled=github_client.app_config() is not None,
    )


@app.route("/")
def index():
    user = current_user()
    if user is None:
        return render_template("landing.html")  # דף פתיחה לפני כניסה/הרשמה
    if not (user.is_approved or user.is_admin):
        return redirect(url_for("pending_page"))
    routes = Route.query.filter_by(user_id=user.id).order_by(Route.created_at.desc()).all()
    ctx = {
        "routes": routes,
        "providers": ai_providers.PROVIDERS,
        "saved_providers": {k.provider for k in user.api_keys},
        "pending": [],
        "pending_users": [],
        "max_code_chars": MAX_CODE_CHARS,
        "max_ai_chars": MAX_AI_CODE_CHARS,
        "users_count": 0,
        "active_count": 0,
    }
    if user.is_admin:
        ctx["pending"] = Route.query.filter(Route.pending_code.isnot(None), Route.live_code.is_(None)).all()  # שאריות מלפני המעבר לאישור משתמשים
        ctx["pending_users"] = User.query.filter_by(is_approved=False).order_by(User.created_at.asc()).all()
        ctx["users_count"] = User.query.count()
        ctx["active_count"] = Route.query.filter_by(status="active").count()
    return render_template("dashboard.html", **ctx)


def analyze_libs(code):
    """מצב הספריות החיצוניות שהקוד (או החבילה) צריך, לתצוגה בדף הבדיקה."""
    if bundles.is_bundle(code):
        _, files = bundles.unpack(code)
        return deps.analyze(bundles.external_imports_code(files))
    return deps.analyze(code)


@app.route("/admin/review/<int:route_id>")
@admin_required
def review_route(route_id):
    route = db.session.get(Route, route_id)
    if not route or not route.pending_code:
        abort(404)
    diff_lines = None
    bundle = None
    if bundles.is_bundle(route.pending_code):
        entry, files = bundles.unpack(route.pending_code)
        changes = None
        if route.live_code and bundles.is_bundle(route.live_code):  # עדכון לשרת קיים: רק מה ששונה
            _, old_files = bundles.unpack(route.live_code)
            changes = [
                {"path": p, "status": st, "diff": make_diff(old_files.get(p, ""), files.get(p, ""), "פעיל", "חדש")}
                for p, st in bundles.diff_files(old_files, files)
            ]
        bundle = {"entry": entry, "files": files, "changes": changes}
    elif route.live_code and not bundles.is_bundle(route.live_code):
        diff_lines = make_diff(route.live_code, route.pending_code, "גרסה פעילה", "גרסה חדשה")
    return render_template("review.html", route=route, libs=analyze_libs(route.pending_code), diff_lines=diff_lines, bundle=bundle)


@app.post("/admin/review/<int:route_id>/approve")
@admin_required
def approve_route(route_id):
    route = db.session.get(Route, route_id)
    if not route or not route.pending_code:
        abort(404)
    activate(route)
    flash(f"השרת אושר ופעיל: {route.full_path}", "success")
    return redirect(url_for("index"))


@app.post("/admin/review/<int:route_id>/reject")
@admin_required
def reject_route(route_id):
    route = db.session.get(Route, route_id)
    if not route:
        abort(404)
    route.pending_code = None
    if not route.live_code:
        route.status = "rejected"
    db.session.commit()
    flash("הבקשה נדחתה.", "info")
    return redirect(url_for("index"))


# ==========================================
# 7. ניהול משתמשים (מנהל)
# ==========================================
def get_user_or_404(user_id):
    target = db.session.get(User, user_id)
    if not target:
        abort(404)
    return target


def back_to(default="admin_users", user_id=None):
    """חזרה למסך שממנו נשלחה הפעולה (רק ערכים מוכרים, לא כתובת חופשית)."""
    where = request.form.get("back")
    if where == "index":
        return redirect(url_for("index"))
    if where == "user" and user_id:
        return redirect(url_for("admin_user", user_id=user_id))
    return redirect(url_for(default))


@app.route("/admin/users")
@admin_required
def admin_users():
    users = User.query.order_by(User.is_approved.asc(), User.created_at.desc()).all()
    counts = dict(db.session.query(Route.user_id, sa_func.count(Route.id)).group_by(Route.user_id).all())
    return render_template("admin_users.html", users=users, counts=counts)


@app.route("/admin/users/<int:user_id>")
@admin_required
def admin_user(user_id):
    target = get_user_or_404(user_id)
    routes = Route.query.filter_by(user_id=target.id).order_by(Route.created_at.desc()).all()
    return render_template("admin_user.html", target=target, routes=routes)


@app.post("/admin/users/<int:user_id>/approve")
@admin_required
def approve_user(user_id):
    target = get_user_or_404(user_id)
    target.is_approved = True
    db.session.commit()
    flash(f"המשתמש {target.username} אושר.", "success")
    return back_to(user_id=target.id)


@app.post("/admin/users/<int:user_id>/suspend")
@admin_required
def suspend_user(user_id):
    target = get_user_or_404(user_id)
    if target.is_admin:
        flash("אי אפשר להשעות מנהל.", "danger")
        return back_to(user_id=target.id)
    target.is_approved = False
    db.session.commit()
    flash(f"המשתמש {target.username} הושעה. השרתים שלו הפסיקו להיות מוגשים, והקוד נשמר.", "info")
    return back_to(user_id=target.id)


@app.post("/admin/users/<int:user_id>/delete")
@admin_required
def delete_user(user_id):
    target = get_user_or_404(user_id)
    if target.is_admin:
        flash("אי אפשר למחוק מנהל.", "danger")
        return back_to(user_id=target.id)
    name = target.username
    for route in target.routes:
        drop_route_cache(route)
    db.session.delete(target)  # שרתים, יומנים, משתני סביבה ומפתחות נמחקים יחד איתו (cascade)
    db.session.commit()
    flash(f"המשתמש {name} וכל השרתים שלו נמחקו.", "success")
    if request.form.get("back") == "index":
        return redirect(url_for("index"))
    return redirect(url_for("admin_users"))


@app.route("/admin/logs/<int:route_id>")
@login_required
def view_logs(route_id):
    user = current_user()
    route = db.session.get(Route, route_id)
    if not route or (route.user_id != user.id and not user.is_admin):
        abort(404)
    logs = Log.query.filter_by(route_id=route.id).order_by(Log.timestamp.desc(), Log.id.desc()).limit(VIEW_LOGS_LIMIT).all()
    entries = [parse_log(row) for row in logs]
    return render_template("logs.html", route=route, logs=logs, entries=entries)


if __name__ == "__main__":
    # פיתוח בלבד. בפרודקשן: gunicorn app:app
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
