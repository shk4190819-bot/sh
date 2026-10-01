"""התקנה אוטומטית של ספריות שקוד המשתמשים צריך."""
import ast
import fcntl
import importlib
import importlib.util
import os
import subprocess
import sys

LIB_DIR = os.environ.get("USER_LIBS_DIR", "/tmp/user_libs")
_LOCK_FILE = os.path.join(os.path.dirname(LIB_DIR.rstrip("/")) or "/tmp", "user_libs.lock")
PIP_TIMEOUT = 180

# שם ה-import  ->  שם החבילה ב-PyPI. מוסיפים כאן ספריות מותרות.
ALLOWED = {
    "bs4": "beautifulsoup4",
    "lxml": "lxml",
    "requests": "requests",
    "httpx": "httpx",
    "yaml": "pyyaml",
    "dateutil": "python-dateutil",
    "pytz": "pytz",
    "PIL": "pillow",
    "jwt": "pyjwt",
    "markdown": "markdown",
    "feedparser": "feedparser",
    "pydantic": "pydantic",
    "xmltodict": "xmltodict",
    "cachetools": "cachetools",
}

# הרחבה בלי לגעת בקוד: USER_LIBS_EXTRA="import_name:package,other:package2"
for _pair in filter(None, os.environ.get("USER_LIBS_EXTRA", "").split(",")):
    if ":" in _pair:
        _imp, _pkg = _pair.split(":", 1)
        ALLOWED[_imp.strip()] = _pkg.strip()


class DependencyError(Exception):
    pass


def add_to_path():
    os.makedirs(LIB_DIR, exist_ok=True)
    if LIB_DIR not in sys.path:
        sys.path.append(LIB_DIR)
    importlib.invalidate_caches()


def imported_modules(code):
    """שמות ה-top-level של כל ה-imports בקוד (כולל imports בתוך פונקציות)."""
    names = set()
    for node in ast.walk(ast.parse(code)):
        if isinstance(node, ast.Import):
            names.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names.add(node.module.split(".")[0])
    return names


def _missing(code):
    out = []
    for name in sorted(imported_modules(code)):
        if name in sys.stdlib_module_names:
            continue
        try:
            if importlib.util.find_spec(name) is None:
                out.append(name)
        except (ImportError, ValueError):
            out.append(name)
    return out


def analyze(code):
    """לתצוגה בדף הבדיקה: installed | will_install | blocked."""
    add_to_path()
    result = []
    for name in sorted(imported_modules(code)):
        if name in sys.stdlib_module_names:
            continue
        try:
            installed = importlib.util.find_spec(name) is not None
        except (ImportError, ValueError):
            installed = False
        status = "installed" if installed else ("will_install" if name in ALLOWED else "blocked")
        result.append({"name": name, "package": ALLOWED.get(name), "status": status})
    return result


def ensure_dependencies(code):
    add_to_path()
    missing = _missing(code)
    if not missing:
        return

    rejected = [m for m in missing if m not in ALLOWED]
    if rejected:
        raise DependencyError(
            "הספריות הבאות לא מותקנות ואינן ברשימה המותרת: "
            + ", ".join(rejected)
            + ". המנהל יכול להוסיף אותן ל-ALLOWED ב-deps.py."
        )

    # נעילה בין processes: worker אחד מתקין, האחרים ממתינים ואז רואים שכבר הותקן
    with open(_LOCK_FILE, "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            importlib.invalidate_caches()
            missing = _missing(code)
            if not missing:
                return
            packages = sorted({ALLOWED[m] for m in missing})
            cmd = [
                sys.executable, "-m", "pip", "install",
                "--target", LIB_DIR,
                "--only-binary", ":all:",  # בלי הרצת setup.py של חבילות מקור
                "--no-input", "--disable-pip-version-check", "--quiet",
                *packages,
            ]
            try:
                proc = subprocess.run(cmd, capture_output=True, text=True, timeout=PIP_TIMEOUT)
            except subprocess.TimeoutExpired:
                raise DependencyError(f"התקנת {', '.join(packages)} חרגה מ-{PIP_TIMEOUT} שניות.")
            if proc.returncode != 0:
                tail = (proc.stderr or proc.stdout or "").strip()[-300:]
                raise DependencyError(f"התקנת {', '.join(packages)} נכשלה: {tail}")
            importlib.invalidate_caches()
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)
