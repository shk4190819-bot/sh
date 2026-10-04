import ast
import difflib
import json
import logging
import os
import re
import secrets
from functools import wraps
from types import MappingProxyType, ModuleType

from authlib.integrations.flask_client import OAuth
from cryptography.fernet import Fernet, InvalidToken
from flask import Blueprint, Flask, Response, abort, flash, redirect, render_template, request, session, url_for
from flask_wtf.csrf import CSRFError, CSRFProtect
from jinja2 import DictLoader
from werkzeug.exceptions import HTTPException
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import check_password_hash, generate_password_hash

import ai_providers
import bundles
import deps
import github_client
from models import ApiKey, EnvVar, Log, Route, RouteSource, User, db
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
deps.add_to_path()
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


def get_github_token(user):
    """הטוקן המוצפן של GitHub של המשתמש (נשמר בטבלת ApiKey עם provider=github), או None."""
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
        return redirect(url_for("index"))
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
    return redirect(url_for("index"))


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

    route = Route.query.filter_by(user_id=user.id, route_name=route_name).first()
    if not route:
        route = Route(user_id=user.id, route_name=route_name, full_path=f"/{user.username}/{route_name}")
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
    db.session.commit()

    if user.is_admin:  # המנהל לא צריך לאשר לעצמו
        activate(route)
        flash(f"השרת פעיל בכתובת {route.full_path}", "success")
    else:
        flash("הקוד נשלח לבדיקה ויופעל אחרי אישור מנהל.", "success")
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
        if user.is_admin:
            activate(route)
            flash("השינויים נשמרו והשרת עודכן.", "success")
        else:
            flash("השינויים נשלחו לבדיקה. הגרסה הפעילה ממשיכה לרוץ עד שמנהל יאשר.", "success")
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


@app.post("/delete/<int:route_id>")
@login_required
def delete_route(route_id):
    user = current_user()
    route = db.session.get(Route, route_id)
    if not route or (route.user_id != user.id and not user.is_admin):
        abort(404)
    path = route.full_path
    old = _subapps.pop(route.id, None)  # ב-workers אחרים מספיק שהשורה נמחקה מה-DB: הבקשות הבאות יקבלו 404
    if old and old[2]:
        bundles.unload(old[2])
    db.session.delete(route)  # היומנים נמחקים יחד איתו (cascade)
    db.session.commit()
    flash(f"השרת {path} נמחק.", "success")
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
    if user.is_admin:
        activate(route)
        flash("נמשכה גרסה חדשה מ-GitHub והשרת עודכן.", "success")
    else:
        flash("נמשכה גרסה חדשה מ-GitHub, והיא ממתינה לאישור מנהל.", "success")
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
    if not isinstance(bp, Blueprint):
        raise RuntimeError("bp is not a Flask Blueprint")
    sub = Flask(f"user_route_{ident}")
    sub.register_blueprint(bp)
    return sub, None
def activate(route):
    """מעביר קוד ממתין ל-live. נקרא רק אחרי אישור מנהל (או כשהמנהל עצמו פורס)."""
    try:
        _, pkg = build_subapp(route.pending_code, route.full_path, route.id, route_env(route), tag="dry")  # בדיקת טעינה
        if pkg:
            bundles.unload(pkg)  # זו הייתה רק בדיקה
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
    sub, pkg = build_subapp(route.live_code, route.full_path, route.id, route_env(route), tag=route.live_version)
    if cached and cached[2]:
        bundles.unload(cached[2])  # שחרור הגרסה הקודמת של חבילה מרובת קבצים
    _subapps[route.id] = (route.live_version, sub, pkg)
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
        "max_code_chars": MAX_CODE_CHARS,
        "max_ai_chars": MAX_AI_CODE_CHARS,
        "users_count": 0,
        "active_count": 0,
    }
    if user.is_admin:
        ctx["pending"] = Route.query.filter(Route.pending_code.isnot(None)).all()
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
