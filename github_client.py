"""גישה קריאה-בלבד ל-GitHub: משיכת קובץ בודד מתוך ריפו (ציבורי, או פרטי עם טוקן)."""
import base64
import io
import json
import os
import re
import threading
import time
import zipfile
from datetime import datetime, timezone
from urllib.parse import quote

import requests
from cryptography.exceptions import UnsupportedAlgorithm
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

API = "https://api.github.com"
TIMEOUT = 15

REPO_RE = re.compile(r"^[A-Za-z0-9_.-]{1,100}/[A-Za-z0-9_.-]{1,100}$")
URL_RE = re.compile(
    r"^https?://(?:www\.)?github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?"
    r"(?:/(?:blob|tree)/([^/?#]+)(?:/([^?#]+?))?)?/?(?:[?#].*)?$"
)
REF_RE = re.compile(r"^[A-Za-z0-9_./-]{1,100}$")


class GithubError(Exception):
    """הודעה שבטוח להציג למשתמש."""


def parse_input(text, path="", ref=""):
    """מקבל כתובת GitHub (ריפו או קובץ) או user/repo, ומחזיר (repo, path, ref).

    קישור כמו https://github.com/user/repo/blob/main/dir/app.py מכיל הכול. שדות path/ref הנפרדים גוברים עליו.
    """
    text = (text or "").strip()
    path = (path or "").strip().lstrip("/")
    ref = (ref or "").strip()

    m = URL_RE.match(text)
    if m:
        owner, repo, url_ref, url_path = m.groups()
        full = f"{owner}/{repo}"
        ref = ref or (url_ref or "")
        path = path or (url_path or "")
    elif REPO_RE.match(text):
        full = text
    else:
        raise GithubError("כתובת הריפו לא תקינה. דוגמאות: https://github.com/משתמש/ריפו או משתמש/ריפו")

    if not path:
        raise GithubError("חסר נתיב לקובץ בתוך הריפו (למשל app.py).")
    if len(path) > 300 or "\\" in path or any(seg in ("..", "") for seg in path.split("/")):
        raise GithubError("נתיב הקובץ לא תקין.")
    if ref and not REF_RE.match(ref):
        raise GithubError("שם הענף לא תקין.")
    return full, path, ref


def _headers(token=None):
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "SH-platform",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def token_login(token):
    """בודק שהטוקן תקף ומחזיר את שם המשתמש ב-GitHub."""
    try:
        r = requests.get(f"{API}/user", headers=_headers(token), timeout=TIMEOUT)
    except requests.RequestException:
        raise GithubError("לא הצלחתי להתחבר ל-GitHub. נסה שוב בעוד רגע.")
    if r.status_code == 401:
        raise GithubError("הטוקן לא תקין או שפג תוקפו.")
    if r.status_code != 200:
        raise GithubError(f"GitHub החזיר שגיאה ({r.status_code}).")
    return r.json().get("login", "")


def fetch_file(repo, path, ref="", token=None):
    """מחזיר {"content", "sha", "size"} של קובץ טקסט (עד 1MB) מתוך הריפו."""
    url = f"{API}/repos/{repo}/contents/{quote(path, safe='/')}"
    params = {"ref": ref} if ref else None
    try:
        r = requests.get(url, headers=_headers(token), params=params, timeout=TIMEOUT)
    except requests.RequestException:
        raise GithubError("לא הצלחתי להתחבר ל-GitHub. נסה שוב בעוד רגע.")

    if r.status_code == 401:
        forget_token(token)
        raise GithubError("הטוקן של GitHub לא תקין או שפג תוקפו. חבר אותו מחדש.")
    if r.status_code == 403:
        if r.headers.get("X-RateLimit-Remaining") == "0":
            raise GithubError("חרגת ממגבלת הבקשות של GitHub. חיבור טוקן מגדיל אותה, או נסה שוב מאוחר יותר.")
        forget_token(token)
        raise GithubError("אין הרשאה לקרוא את הקובץ. לטוקן צריכה להיות הרשאת Contents: Read לריפו הזה.")
    if r.status_code == 404:
        raise GithubError("הקובץ לא נמצא. בדוק את שם הריפו, הנתיב והענף. אם הריפו פרטי, חבר טוקן של GitHub.")
    if r.status_code != 200:
        raise GithubError(f"GitHub החזיר שגיאה ({r.status_code}).")

    data = r.json()
    if isinstance(data, list):
        raise GithubError("הנתיב מצביע על תיקייה ולא על קובץ.")
    if data.get("type") != "file":
        raise GithubError("הנתיב אינו קובץ רגיל.")
    if data.get("encoding") != "base64":
        raise GithubError("הקובץ גדול מדי (מעל 1MB) או בפורמט שלא נתמך.")
    try:
        content = base64.b64decode(data.get("content") or "").decode("utf-8")
    except (ValueError, UnicodeDecodeError):
        raise GithubError("הקובץ אינו טקסט בקידוד UTF-8.")
    return {"content": content, "sha": data.get("sha", ""), "size": data.get("size", 0)}


# ---------- ריפו שלם (כמה קבצים) ----------
MAX_ZIP_BYTES = 20 * 1024 * 1024
MAX_FILE_BYTES = 300_000
MAX_TOTAL_BYTES = 1_500_000
MAX_FILES = 100
TEXT_EXTS = {".py", ".html", ".htm", ".css", ".js", ".json", ".txt", ".md", ".yaml", ".yml", ".xml", ".svg",
             ".csv", ".ini", ".cfg", ".toml", ".jinja", ".j2"}
SKIP_DIRS = {".git", ".github", "__pycache__", "node_modules", "venv", ".venv", ".idea", ".vscode"}


def parse_repo_input(text, subdir="", ref=""):
    """כתובת ריפו (או user/repo, או קישור /tree/ענף/תיקייה) -> (repo, subdir, ref)."""
    text = (text or "").strip()
    subdir = (subdir or "").strip().strip("/")
    ref = (ref or "").strip()
    m = URL_RE.match(text)
    if m:
        owner, repo, url_ref, url_path = m.groups()
        full = f"{owner}/{repo}"
        ref = ref or (url_ref or "")
        subdir = subdir or (url_path or "").strip("/")
    elif REPO_RE.match(text):
        full = text
    else:
        raise GithubError("כתובת הריפו לא תקינה. דוגמאות: https://github.com/משתמש/ריפו או משתמש/ריפו")
    if subdir and (len(subdir) > 300 or "\\" in subdir or any(seg in ("..", "") for seg in subdir.split("/"))):
        raise GithubError("נתיב התיקייה לא תקין.")
    if ref and not REF_RE.match(ref):
        raise GithubError("שם הענף לא תקין.")
    return full, subdir, ref


def fetch_repo(repo, ref="", subdir="", token=None):
    """מוריד את הריפו כ-ZIP (בקשה אחת) ומחזיר {"files": {נתיב: טקסט}, "sha": מזהה קומיט, "skipped": [...]}.

    רק קבצי טקסט מוכרים נשמרים. שום דבר לא נכתב לדיסק: הקריאה היא מתוך הזיכרון.
    """
    url = f"{API}/repos/{repo}/zipball" + (f"/{quote(ref, safe='/')}" if ref else "")
    try:
        r = requests.get(url, headers=_headers(token), stream=True, timeout=TIMEOUT * 2)
    except requests.RequestException:
        raise GithubError("לא הצלחתי להתחבר ל-GitHub. נסה שוב בעוד רגע.")
    if r.status_code == 401:
        forget_token(token)
        raise GithubError("הטוקן של GitHub לא תקין או שפג תוקפו. חבר אותו מחדש.")
    if r.status_code == 403:
        if r.headers.get("X-RateLimit-Remaining") == "0":
            raise GithubError("חרגת ממגבלת הבקשות של GitHub. חיבור טוקן מגדיל אותה, או נסה שוב מאוחר יותר.")
        forget_token(token)
        raise GithubError("אין הרשאה לקרוא את הריפו. לטוקן צריכה להיות הרשאת Contents: Read לריפו הזה.")
    if r.status_code == 404:
        raise GithubError("הריפו או הענף לא נמצאו. אם הריפו פרטי, חבר טוקן של GitHub.")
    if r.status_code != 200:
        raise GithubError(f"GitHub החזיר שגיאה ({r.status_code}).")

    buf, size = io.BytesIO(), 0
    for chunk in r.iter_content(65536):
        size += len(chunk)
        if size > MAX_ZIP_BYTES:
            raise GithubError("הריפו גדול מדי (מעל 20MB). בחר ענף או ריפו קטן יותר.")
        buf.write(chunk)
    try:
        zf = zipfile.ZipFile(buf)
    except zipfile.BadZipFile:
        raise GithubError("GitHub החזיר קובץ לא תקין.")

    infos = [i for i in zf.infolist() if not i.is_dir()]
    if not infos:
        raise GithubError("הריפו ריק.")
    top = infos[0].filename.split("/", 1)[0]  # owner-repo-<sha>
    sha = top.rsplit("-", 1)[-1]
    prefix = f"{top}/" + (f"{subdir}/" if subdir else "")

    files, skipped, total = {}, [], 0
    for info in infos:
        name = info.filename
        if not name.startswith(prefix):
            continue
        rel = name[len(prefix):]
        parts = rel.split("/")
        if not rel or any(p in ("", "..") for p in parts) or any(p in SKIP_DIRS for p in parts[:-1]):
            continue
        if (info.external_attr >> 16) & 0o170000 == 0o120000:  # symlink
            continue
        ext = "." + parts[-1].rsplit(".", 1)[-1].lower() if "." in parts[-1] else ""
        if ext not in TEXT_EXTS:
            skipped.append(rel)
            continue
        if info.file_size > MAX_FILE_BYTES:
            skipped.append(rel)
            continue
        try:
            text = zf.read(info).decode("utf-8")
        except (UnicodeDecodeError, zipfile.BadZipFile):
            skipped.append(rel)
            continue
        total += len(text.encode("utf-8"))
        files[rel] = text.replace("\r\n", "\n")
        if len(files) > MAX_FILES:
            raise GithubError(f"יותר מדי קבצים (מעל {MAX_FILES}). ציין תיקייה קטנה יותר בתוך הריפו.")
        if total > MAX_TOTAL_BYTES:
            raise GithubError("סך הקבצים גדול מדי. ציין תיקייה קטנה יותר בתוך הריפו.")
    if not files:
        raise GithubError("לא נמצאו קבצי קוד בתיקייה שצוינה.")
    return {"files": files, "sha": sha, "skipped": skipped}


# ---------- GitHub App (חיבור בלחיצה במקום טוקן ידני) ----------
# הרשאות מינימליות בלבד: קריאת קוד ומטא-דאטה. המפתח הפרטי נשאר בשרת, ואף פעם לא נשלח לדפדפן.
APP_SLUG_RE = re.compile(r"^[A-Za-z0-9-]{1,100}$")
INSTALL_PERMISSIONS = {"contents": "read", "metadata": "read"}
TOKEN_REFRESH_MARGIN = 300  # מחדשים installation token 5 דקות לפני הפג תוקף

_token_cache = {}  # installation_id -> (token, expires_epoch). בזיכרון של ה-worker בלבד
_token_lock = threading.Lock()


class InstallationGone(GithubError):
    """ההתקנה הוסרה או שה-App כבר לא רואה אותה."""


def app_config():
    """הגדרות ה-App ממשתני הסביבה, או None אם משהו חסר (אז כפתור Connect מוסתר ונשאר רק טוקן ידני)."""
    slug = (os.environ.get("GITHUB_APP_SLUG") or "").strip()
    client_id = (os.environ.get("GITHUB_APP_CLIENT_ID") or "").strip()
    secret = (os.environ.get("GITHUB_APP_CLIENT_SECRET") or "").strip()
    key = os.environ.get("GITHUB_APP_PRIVATE_KEY") or ""
    key_file = (os.environ.get("GITHUB_APP_PRIVATE_KEY_FILE") or "").strip()  # למשל Secret File ב-Render
    if not key and key_file:
        try:
            with open(key_file, encoding="utf-8") as f:
                key = f.read()
        except OSError:
            key = ""
    key = key.replace("\\n", "\n").strip()
    if not (slug and client_id and secret and key) or not APP_SLUG_RE.match(slug):
        return None
    return {"slug": slug, "client_id": client_id, "client_secret": secret, "private_key": key}


def _b64url(raw):
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def make_app_jwt(client_id, private_key_pem, now=None):
    """JWT של ה-App (RS256, תקף 9 דקות). iss = Client ID."""
    now = int(now if now is not None else time.time())
    header = {"alg": "RS256", "typ": "JWT"}
    payload = {"iat": now - 60, "exp": now + 540, "iss": client_id}
    signing = ".".join(_b64url(json.dumps(part, separators=(",", ":")).encode()) for part in (header, payload))
    try:
        key = serialization.load_pem_private_key(private_key_pem.encode(), password=None)
        signature = key.sign(signing.encode(), padding.PKCS1v15(), hashes.SHA256())
    except (ValueError, TypeError, UnsupportedAlgorithm):
        raise GithubError("המפתח הפרטי של ה-App בהגדרות השרת לא תקין.")
    return f"{signing}.{_b64url(signature)}"


def _request(method, url, **kwargs):
    try:
        return requests.request(method, url, timeout=TIMEOUT, **kwargs)
    except requests.RequestException:
        raise GithubError("לא הצלחתי להתחבר ל-GitHub. נסה שוב בעוד רגע.")


def _app_headers(cfg):
    return _headers(make_app_jwt(cfg["client_id"], cfg["private_key"]))


def exchange_code(code, cfg):
    """מחליף את ה-code מההפניה בטוקן משתמש קצר חיים. משמש רק לאימות בעלות, ולא נשמר."""
    r = _request(
        "POST", "https://github.com/login/oauth/access_token",
        headers={"Accept": "application/json", "User-Agent": "SH-platform"},
        json={"client_id": cfg["client_id"], "client_secret": cfg["client_secret"], "code": code},
    )
    try:
        data = r.json()
    except ValueError:
        data = {}
    token = data.get("access_token") if r.status_code == 200 else None
    if not token:
        raise GithubError("האימות מול GitHub נכשל או שפג תוקפו. התחל את החיבור מחדש.")
    return token


def user_login(user_token):
    """שם המשתמש ב-GitHub של בעל הטוקן."""
    r = _request("GET", f"{API}/user", headers=_headers(user_token))
    if r.status_code != 200:
        raise GithubError("לא הצלחתי לאמת את חשבון ה-GitHub שלך. התחל מחדש.")
    return r.json().get("login", "")


def user_installation_ids(user_token):
    """מזהי ההתקנות של ה-App שהמשתמש הזה (לפי הטוקן שלו) רשאי לגשת אליהן."""
    ids = set()
    for page in range(1, 6):
        r = _request("GET", f"{API}/user/installations", headers=_headers(user_token),
                     params={"per_page": 100, "page": page})
        if r.status_code != 200:
            raise GithubError("לא הצלחתי לאמת את ההתקנה מול GitHub. התחל מחדש.")
        items = r.json().get("installations", [])
        ids.update(i.get("id") for i in items)
        if len(items) < 100:
            break
    return ids


def installation_info(installation_id, cfg):
    """{"login", "type", "repository_selection"} של חשבון ההתקנה, לפי GitHub (מאומת ע"י JWT של ה-App)."""
    r = _request("GET", f"{API}/app/installations/{int(installation_id)}", headers=_app_headers(cfg))
    if r.status_code == 404:
        raise InstallationGone("ההתקנה לא נמצאה ב-GitHub.")
    if r.status_code != 200:
        raise GithubError(f"GitHub החזיר שגיאה ({r.status_code}).")
    data = r.json()
    account = data.get("account") or {}
    return {
        "login": account.get("login", ""),
        "type": account.get("type", ""),
        "repository_selection": data.get("repository_selection", ""),
    }


def _expiry_epoch(value):
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp()
    except (TypeError, ValueError):
        return time.time() + 3000


def installation_token(installation_id, cfg=None):
    """installation token (קריאה בלבד) עם cache בזיכרון עד לפני הפג תוקף."""
    cfg = cfg or app_config()
    if not cfg:
        raise GithubError("חיבור GitHub App לא מוגדר בשרת.")
    installation_id = int(installation_id)
    with _token_lock:
        hit = _token_cache.get(installation_id)
        if hit and hit[1] - time.time() > TOKEN_REFRESH_MARGIN:
            return hit[0]
    for attempt in (1, 2):  # 401 מ-GitHub: ניסיון חוזר אחד בלבד, עם JWT חדש. שאר הכשלים לא נוסים שוב
        r = _request("POST", f"{API}/app/installations/{installation_id}/access_tokens",
                     headers=_app_headers(cfg), json={"permissions": INSTALL_PERMISSIONS})
        if r.status_code == 401 and attempt == 1:
            forget_installation(installation_id)
            continue
        break
    if r.status_code in (401, 403, 404):  # אימות/הרשאה/התקנה נכשלו: לא משאירים טוקן ישן ב-cache
        forget_installation(installation_id)
    if r.status_code == 404:
        raise InstallationGone("ההתקנה לא נמצאה ב-GitHub. ייתכן שה-App הוסר.")
    if r.status_code == 401:
        raise GithubError("האימות של ה-App מול GitHub נכשל. בדוק את הגדרות השרת.")
    if r.status_code == 403:
        raise GithubError("GitHub סירב להנפיק טוקן להתקנה. ייתכן שההתקנה הושעתה או שההרשאות שלה השתנו.")
    if r.status_code != 201:
        raise GithubError(f"הנפקת טוקן מ-GitHub נכשלה ({r.status_code}).")
    data = r.json()
    token = data.get("token")
    if not token:
        raise GithubError("GitHub לא החזיר טוקן.")
    with _token_lock:
        _token_cache[installation_id] = (token, _expiry_epoch(data.get("expires_at")))
    return token


def forget_installation(installation_id):
    with _token_lock:
        _token_cache.pop(int(installation_id), None)


def forget_token(token):
    """מוחק מה-cache טוקן ש-GitHub דחה בשימוש (401 / 403), כדי שהבקשה הבאה תנפיק חדש. הטוקן עצמו לא נרשם בשום מקום."""
    if not token:
        return
    with _token_lock:
        for key in [k for k, (cached, _) in _token_cache.items() if cached == token]:
            _token_cache.pop(key, None)


def list_repos(token):
    """שמות הריפוזיטוריז (owner/repo) שההתקנה רואה. לבורר הריפוזיטוריז בטופס הפריסה."""
    names = []
    for page in range(1, 6):
        r = _request("GET", f"{API}/installation/repositories", headers=_headers(token),
                     params={"per_page": 100, "page": page})
        if r.status_code != 200:
            raise GithubError(f"GitHub החזיר שגיאה ({r.status_code}).")
        repos = r.json().get("repositories", [])
        names.extend(x.get("full_name", "") for x in repos)
        if len(repos) < 100:
            break
    return names
