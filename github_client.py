"""גישה קריאה-בלבד ל-GitHub: משיכת קובץ בודד מתוך ריפו (ציבורי, או פרטי עם טוקן)."""
import base64
import io
import re
import zipfile
from urllib.parse import quote

import requests

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
        raise GithubError("הטוקן של GitHub לא תקין או שפג תוקפו. חבר אותו מחדש.")
    if r.status_code == 403:
        if r.headers.get("X-RateLimit-Remaining") == "0":
            raise GithubError("חרגת ממגבלת הבקשות של GitHub. חיבור טוקן מגדיל אותה, או נסה שוב מאוחר יותר.")
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
        raise GithubError("הטוקן של GitHub לא תקין או שפג תוקפו. חבר אותו מחדש.")
    if r.status_code == 403:
        if r.headers.get("X-RateLimit-Remaining") == "0":
            raise GithubError("חרגת ממגבלת הבקשות של GitHub. חיבור טוקן מגדיל אותה, או נסה שוב מאוחר יותר.")
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
