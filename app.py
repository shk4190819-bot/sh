import ast
import logging
import os
import re
import secrets
from functools import wraps
from types import ModuleType

from authlib.integrations.flask_client import OAuth
from cryptography.fernet import Fernet, InvalidToken
from flask import Blueprint, Flask, Response, abort, flash, redirect, render_template, request, session, url_for
from flask_wtf.csrf import CSRFError, CSRFProtect
from jinja2 import DictLoader
from werkzeug.exceptions import HTTPException
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import check_password_hash, generate_password_hash

import ai_providers
from models import ApiKey, Log, Route, User, db
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
with app.app_context():
    db.create_all()

oauth = OAuth(app)
google = oauth.register(
    name="google",
    client_id=os.environ.get("GOOGLE_CLIENT_ID"),
    client_secret=os.environ.get("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

USERNAME_RE = re.compile(r"^[a-z][a-z0-9_]{2,29}$")
ROUTE_RE = re.compile(r"^[a-z0-9][a-z0-9_]{0,39}$")
LANG_RE = re.compile(r"^[\w+#.\- ]{1,30}$")
RESERVED = {"admin", "auth", "login", "logout", "static", "settings", "deploy", "api", "review"}
PY_LANGS = {"python", "py", "python3", "flask"}
MAX_CODE_CHARS = 30_000


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
    return {"current_user": current_user(), "google_enabled": bool(os.environ.get("GOOGLE_CLIENT_ID"))}


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if current_user() is None:
            session.clear()
            return redirect(url_for("login_page"))
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
    if ADMIN_USERNAME and user.username == ADMIN_USERNAME and user.password_hash and not user.is_admin:
        user.is_admin = True
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
        return render_template("login.html")

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
    flash("נרשמת בהצלחה, ברוך הבא!" if action == "register" else "התחברת בהצלחה.", "success")
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
    return redirect(url_for("login_page"))


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
    return redirect(url_for("index"))


# ==========================================
# 5. פריסה: תרגום (או Python ישיר) -> אישור מנהל -> הפעלה
# ==========================================
def strip_fences(text):
    m = re.search(r"```(?:python|py)?\s*\n(.*?)```", text, re.DOTALL)
    return (m.group(1) if m else text).strip()


def validate_python(code):
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        raise UserError(f"שגיאת תחביר בקוד (שורה {e.lineno}): {e.msg}")
    defines_bp = any(
        isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "bp" for t in n.targets)
        for n in tree.body
    )
    if not defines_bp:
        raise UserError("הקוד חייב להגדיר Blueprint בשם bp, למשל: bp = Blueprint('x', __name__)")


@app.post("/deploy")
@login_required
def deploy_server():
    user = current_user()

    route_name = (request.form.get("route_name") or "").strip().lower()
    if not ROUTE_RE.match(route_name):
        raise UserError("שם נתיב: עד 40 תווים, אנגלית קטנה/ספרות/_ בלבד.")
    source_lang = (request.form.get("source_lang") or "").strip()
    if not LANG_RE.match(source_lang):
        raise UserError("שפת מקור לא תקינה.")
    code = request.form.get("code") or ""
    if not code.strip() or len(code) > MAX_CODE_CHARS:
        raise UserError(f"הקוד ריק או ארוך מדי (מקסימום {MAX_CODE_CHARS} תווים).")

    force_ai = request.form.get("force_ai") == "1"
    if source_lang.lower() in PY_LANGS and not force_ai:
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

    route = Route.query.filter_by(user_id=user.id, route_name=route_name).first()
    if not route:
        route = Route(user_id=user.id, route_name=route_name, full_path=f"/{user.username}/{route_name}")
        db.session.add(route)
    route.source_lang = source_lang
    route.pending_code = final_code
    if route.live_code is None:
        route.status = "pending"
    db.session.commit()

    if user.is_admin:  # המנהל לא צריך לאשר לעצמו
        activate(route)
        flash(f"השרת פעיל בכתובת {route.full_path}", "success")
    else:
        flash("הקוד נשלח לבדיקה ויופעל אחרי אישור מנהל.", "success")
    return redirect(url_for("index"))


# --- הרצת השרתים הווירטואליים: כל אחד כאפליקציית Flask קטנה משלו, נטענת מה-DB לפי דרישה ---
_subapps = {}  # route_id -> (live_version, flask_app). cache לכל worker, מתרענן לפי live_version


def build_subapp(code, label, ident):
    module = ModuleType(f"user_route_{ident}")
    exec(compile(code, f"<user:{label}>", "exec"), module.__dict__)
    bp = getattr(module, "bp", None)
    if not isinstance(bp, Blueprint):
        raise RuntimeError("bp is not a Flask Blueprint")
    sub = Flask(f"user_route_{ident}")
    sub.register_blueprint(bp)
    return sub


def activate(route):
    """מעביר קוד ממתין ל-live. נקרא רק אחרי אישור מנהל (או כשהמנהל עצמו פורס)."""
    try:
        build_subapp(route.pending_code, route.full_path, route.id)  # בדיקת טעינה לפני שמפעילים
    except Exception as e:
        raise UserError(f"הקוד לא נטען: {type(e).__name__}: {str(e)[:200]}")
    route.live_code = route.pending_code
    route.pending_code = None
    route.live_version += 1
    route.status = "active"
    db.session.commit()


def get_subapp(route):
    cached = _subapps.get(route.id)
    if cached and cached[0] == route.live_version:
        return cached[1]
    sub = build_subapp(route.live_code, route.full_path, route.id)
    _subapps[route.id] = (route.live_version, sub)
    return sub


def record_log(route_id, message):
    try:
        db.session.add(Log(route_id=route_id, message=message[:500]))
        db.session.commit()
    except Exception:
        db.session.rollback()
        app.logger.exception("Failed to write log")


HTTP_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE"]


@app.route("/<username>/<route_name>", defaults={"rest": ""}, methods=HTTP_METHODS, strict_slashes=False)
@app.route("/<username>/<route_name>/<path:rest>", methods=HTTP_METHODS)
@csrf.exempt  # ה-webhooks החיצוניים לא יכולים לשלוח CSRF token
def dispatch(username, route_name, rest):
    route = (
        Route.query.join(User)
        .filter(User.username == username, Route.route_name == route_name, Route.status == "active")
        .first()
    )
    if route is None or not route.live_code:
        abort(404)
    try:
        sub = get_subapp(route)
        environ = request.environ.copy()
        environ["SCRIPT_NAME"] = request.script_root + f"/{username}/{route_name}"
        environ["PATH_INFO"] = "/" + rest
        response = Response.from_app(sub, environ, buffered=True)
    except Exception:
        app.logger.exception("Sub-server failed: %s", route.full_path)
        record_log(route.id, f"Method: {request.method} | Status: 502 | IP: {request.remote_addr} | load/run error")
        abort(502)
    record_log(route.id, f"Method: {request.method} | Status: {response.status_code} | IP: {request.remote_addr}")
    return response


# ==========================================
# 6. לוח בקרה, אישורי מנהל ולוגים
# ==========================================
@app.route("/")
@login_required
def index():
    user = current_user()
    routes = Route.query.filter_by(user_id=user.id).order_by(Route.created_at.desc()).all()
    ctx = {
        "routes": routes,
        "providers": ai_providers.PROVIDERS,
        "saved_providers": {k.provider for k in user.api_keys},
        "pending": [],
        "users_count": 0,
        "active_count": 0,
    }
    if user.is_admin:
        ctx["pending"] = Route.query.filter(Route.pending_code.isnot(None)).all()
        ctx["users_count"] = User.query.count()
        ctx["active_count"] = Route.query.filter_by(status="active").count()
    return render_template("dashboard.html", **ctx)


@app.route("/admin/review/<int:route_id>")
@admin_required
def review_route(route_id):
    route = db.session.get(Route, route_id)
    if not route or not route.pending_code:
        abort(404)
    return render_template("review.html", route=route)


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


@app.route("/admin/logs/<int:route_id>")
@login_required
def view_logs(route_id):
    user = current_user()
    route = db.session.get(Route, route_id)
    if not route or (route.user_id != user.id and not user.is_admin):
        abort(404)
    logs = Log.query.filter_by(route_id=route.id).order_by(Log.timestamp.desc()).limit(50).all()
    return render_template("logs.html", route=route, logs=logs)


if __name__ == "__main__":
    # פיתוח בלבד. בפרודקשן: gunicorn app:app
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
