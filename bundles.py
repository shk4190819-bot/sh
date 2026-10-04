"""שרתים מרובי קבצים: אריזה ל-JSON אחד (נשמר בעמודת הקוד הרגילה), בדיקה, וטעינה מהזיכרון.

כל חבילה נטענת תחת שם ייחודי (ubundle_<id>_<גרסה>), כך ששני משתמשים עם קובץ בשם utils.py
לא מתנגשים. שום דבר לא נכתב לדיסק: הקבצים נקראים מהזיכרון דרך import hook.
ייבוא מקומי בסגנון `import utils` או `from utils import x` מתורגם בזמן הטעינה לשם הייחודי.
"""
import ast
import importlib
import importlib.abc
import importlib.util
import json
import re
import sys
import threading
from types import MappingProxyType

from flask import Blueprint, Flask


class BundleError(Exception):
    """הודעה שבטוח להציג למשתמש."""


MAX_PY_FILES = 100
_IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_PREFERRED_ENTRIES = ("app.py", "main.py", "server.py", "__init__.py")


# ---------- אריזה ----------
def pack(files, entry):
    """אורז {נתיב: טקסט} + קובץ ראשי למחרוזת אחת. לא זורק שגיאות: הבדיקה נעשית ב-validate."""
    return json.dumps({"bundle": 1, "entry": entry, "files": files}, ensure_ascii=False)


def is_bundle(code):
    return isinstance(code, str) and code.lstrip().startswith('{"bundle"')


def unpack(code):
    try:
        data = json.loads(code)
        entry, files = data["entry"], data["files"]
        if not isinstance(entry, str) or not isinstance(files, dict):
            raise ValueError
    except (ValueError, KeyError, TypeError):
        raise BundleError("נתוני החבילה פגומים.")
    return entry, files


# ---------- ניתוח קוד ----------
def _parse(path, source):
    try:
        return ast.parse(source, filename=path)
    except SyntaxError as e:
        raise BundleError(f"שגיאת תחביר ב-{path} (שורה {e.lineno}): {e.msg}")


APP_NAMES = ("bp", "app", "application")


def _defines_bp(tree):
    """bp / app / application = ... או from x import app (ברמה העליונה של הקובץ)."""
    for n in tree.body:
        if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id in APP_NAMES for t in n.targets):
            return True
        if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name) and n.target.id in APP_NAMES:
            return True
        if isinstance(n, (ast.ImportFrom, ast.Import)):
            for a in n.names:
                if (a.asname or a.name.split(".")[0]) in APP_NAMES:
                    return True
    return False


def _py_files(files):
    return {p: s for p, s in files.items() if p.endswith(".py")}


def _module_name(path):
    """a/b.py -> (a.b, False) ; a/__init__.py -> (a, True). None אם השם לא תקף כמודול."""
    parts = path[:-3].split("/")
    is_pkg = parts[-1] == "__init__"
    if is_pkg:
        parts = parts[:-1]
    if not parts or not all(_IDENT_RE.match(p) for p in parts):
        return None
    return ".".join(parts), is_pkg


def _local_tops(files):
    tops = set()
    for p in _py_files(files):
        m = _module_name(p)
        if m:
            tops.add(m[0].split(".")[0])
    return tops


def pick_entry(files, requested=None):
    """בוחר קובץ ראשי: זה שהמשתמש ציין, או קובץ שמגדיר bp (מעדיף app.py / main.py)."""
    requested = (requested or "").strip().lstrip("/")
    if requested:
        if requested not in files or not requested.endswith(".py"):
            raise BundleError(f"הקובץ הראשי {requested} לא נמצא בריפו (או שהוא לא קובץ Python).")
        return requested
    candidates = []
    for p, src in _py_files(files).items():
        try:
            if _defines_bp(ast.parse(src)):
                candidates.append(p)
        except SyntaxError:
            continue
    if not candidates:
        raise BundleError("לא נמצא קובץ שמגדיר אפליקציית Flask בשם app (או Blueprint בשם bp). ציין קובץ ראשי.")

    def rank(p):
        base = p.rsplit("/", 1)[-1]
        return (p.count("/"), _PREFERRED_ENTRIES.index(base) if base in _PREFERRED_ENTRIES else 99, len(p), p)

    return sorted(candidates, key=rank)[0]


def validate(files, entry):
    if not isinstance(files, dict) or not files:
        raise BundleError("החבילה ריקה.")
    for p, s in files.items():
        if not isinstance(p, str) or not isinstance(s, str):
            raise BundleError("נתוני החבילה לא תקינים.")
        if not p or len(p) > 300 or p.startswith("/") or "\\" in p or any(seg in ("", "..") for seg in p.split("/")):
            raise BundleError(f"נתיב קובץ לא תקין: {p}")
    py = _py_files(files)
    if len(py) > MAX_PY_FILES:
        raise BundleError(f"יותר מדי קבצי Python (מעל {MAX_PY_FILES}).")
    if entry not in py:
        raise BundleError(f"הקובץ הראשי {entry} לא נמצא בחבילה.")
    trees = {p: _parse(p, s) for p, s in py.items()}
    if not _module_name(entry):
        raise BundleError("שם הקובץ הראשי חייב להיות מורכב מאותיות באנגלית, ספרות וקו תחתון בלבד (למשל app.py).")
    if not _defines_bp(trees[entry]):
        raise BundleError(f"הקובץ הראשי {entry} חייב להגדיר app = Flask(__name__) (או bp = Blueprint(...)).")


def external_imports_code(files):
    """קוד שמכיל רק `import X` לכל ספרייה חיצונית שהחבילה צריכה (בלי מודולים מקומיים), לבדיקת תלויות."""
    local = _local_tops(files)
    names = set()
    for p, src in _py_files(files).items():
        try:
            tree = ast.parse(src)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                names.add(node.module.split(".")[0])
    return "\n".join(f"import {n}" for n in sorted(names - local)) + "\n"


def diff_files(old, new):
    """[(נתיב, 'new' | 'deleted' | 'modified')] רק לקבצים שהשתנו."""
    out = []
    for p in sorted(set(old) | set(new)):
        if p not in old:
            out.append((p, "new"))
        elif p not in new:
            out.append((p, "deleted"))
        elif old[p] != new[p]:
            out.append((p, "modified"))
    return out


# ---------- טעינה מהזיכרון ----------
_MODULES = {}  # שם מודול מלא -> _Info
_LOCK = threading.RLock()


class _Info:
    def __init__(self, source, filename, is_pkg, env):
        self.source, self.filename, self.is_pkg, self.env = source, filename, is_pkg, env


class _Rewriter(ast.NodeTransformer):
    """מתרגם ייבוא של מודולים מקומיים לשם הייחודי של החבילה."""

    def __init__(self, pkg, local):
        self.pkg, self.local = pkg, local

    def visit_ImportFrom(self, node):
        if node.level == 0 and node.module and node.module.split(".")[0] in self.local:
            node.module = f"{self.pkg}.{node.module}"
        return node

    def visit_Import(self, node):
        if not any(a.name.split(".")[0] in self.local for a in node.names):
            return node
        out = []
        for a in node.names:
            top = a.name.split(".")[0]
            if top not in self.local:
                out.append(ast.copy_location(ast.Import(names=[a]), node))
                continue
            full = f"{self.pkg}.{a.name}"
            if a.asname:
                src = f"{a.asname} = __import__('importlib').import_module({full!r})"
            else:
                src = (
                    f"__import__('importlib').import_module({full!r})\n"
                    f"{top} = __import__('importlib').import_module({self.pkg + '.' + top!r})"
                )
            for stmt in ast.parse(src).body:
                for n in ast.walk(stmt):
                    ast.copy_location(n, node)
                out.append(stmt)
        return out


class _Loader(importlib.abc.Loader):
    def __init__(self, info, pkg, local):
        self.info, self.pkg, self.local = info, pkg, local

    def create_module(self, spec):
        return None

    def get_filename(self, fullname):
        return self.info.filename

    def exec_module(self, module):
        module.__dict__["env"] = MappingProxyType(dict(self.info.env or {}))  # משתני הסביבה של השרת הזה בלבד
        module.__file__ = self.info.filename
        if not self.info.source.strip():
            return
        tree = ast.parse(self.info.source, filename=self.info.filename)
        tree = _Rewriter(self.pkg, self.local).visit(tree)
        ast.fix_missing_locations(tree)
        exec(compile(tree, self.info.filename, "exec"), module.__dict__)


class _Finder(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        info = _MODULES.get(fullname)
        if info is None:
            return None
        pkg = fullname.split(".", 1)[0]
        loader = _Loader(info, pkg, info.local)
        return importlib.util.spec_from_loader(fullname, loader, origin=info.filename, is_package=info.is_pkg)


_finder = _Finder()


def _install_finder():
    if _finder not in sys.meta_path:
        sys.meta_path.insert(0, _finder)


_TEMPLATE_EXTS = (".html", ".htm", ".txt", ".xml", ".jinja", ".j2")


def _after_dir(path, dirname):
    """app/templates/a/b.html -> a/b.html (רק אם templates / static הוא אחד מתיקיות הנתיב)."""
    parts = path.split("/")
    if dirname in parts[:-1]:
        return "/".join(parts[parts.index(dirname, 0, len(parts) - 1) + 1:])
    return None


def attach_assets(flask_app, files):
    """templates ו-static מהזיכרון: אין דיסק, אז הקבצים מוגשים מתוך החבילה."""
    from jinja2 import DictLoader
    from flask import Response, abort
    import mimetypes

    templates, static = {}, {}
    for p, s in files.items():
        t = _after_dir(p, "templates") if p.lower().endswith(_TEMPLATE_EXTS) else None
        if t:
            templates[t] = s
        st = _after_dir(p, "static")
        if st:
            static[st] = s
    if templates:
        flask_app.jinja_loader = DictLoader(templates)
    if static:
        def serve_static(filename):
            if filename not in static:
                abort(404)
            return Response(static[filename], mimetype=mimetypes.guess_type(filename)[0] or "text/plain")

        if "static" in flask_app.view_functions:
            flask_app.view_functions["static"] = serve_static
        else:
            flask_app.add_url_rule("/static/<path:filename>", endpoint="static", view_func=serve_static)


def unload(pkg):
    """משחרר חבילה שנטענה: מוחק אותה מ-sys.modules ומהרישום."""
    if not pkg:
        return
    with _LOCK:
        for name in [n for n in _MODULES if n == pkg or n.startswith(pkg + ".")]:
            _MODULES.pop(name, None)
        for name in [n for n in sys.modules if n == pkg or n.startswith(pkg + ".")]:
            sys.modules.pop(name, None)


def load(code, ident, tag, env=None):
    """טוען חבילה ומחזיר (אפליקציית Flask, שם החבילה לשחרור)."""
    entry, files = unpack(code)
    validate(files, entry)
    pkg = "ubundle_" + re.sub(r"\W", "_", f"{ident}_{tag}")
    local = _local_tops(files)
    entry_mod = _module_name(entry)[0]

    with _LOCK:
        _install_finder()
        unload(pkg)  # שאריות מטעינה קודמת עם אותו שם
        _MODULES[pkg] = _Info("", f"<bundle:{ident}>/__init__", True, env)
        _MODULES[pkg].local = local
        for path, src in _py_files(files).items():
            m = _module_name(path)
            if not m:
                continue
            name, is_pkg = m
            full = f"{pkg}.{name}"
            info = _Info(src, f"<bundle:{ident}>/{path}", is_pkg, env)
            info.local = local
            _MODULES[full] = info
            parts = full.split(".")
            for i in range(2, len(parts)):  # תיקיות בלי __init__.py נטענות כחבילות ריקות
                parent = ".".join(parts[:i])
                if parent not in _MODULES:
                    pinfo = _Info("", f"<bundle:{ident}>/{'/'.join(parts[1:i])}/", True, env)
                    pinfo.local = local
                    _MODULES[parent] = pinfo
        try:
            module = importlib.import_module(f"{pkg}.{entry_mod}")
            bp = getattr(module, "bp", None)
            if isinstance(bp, Blueprint):
                sub = Flask(f"user_route_{ident}")
                sub.register_blueprint(bp)
            else:
                sub = getattr(module, "app", None)
                if sub is None:
                    sub = getattr(module, "application", None)
                if sub is None or not callable(sub):
                    raise BundleError("בקובץ הראשי לא נמצא app (אפליקציית Flask) או bp (Blueprint).")
            if isinstance(sub, Flask):
                attach_assets(sub, files)
        except BundleError:
            unload(pkg)
            raise
        except Exception as e:
            unload(pkg)
            raise BundleError(f"הטעינה נכשלה: {type(e).__name__}: {str(e)[:300]}")
    return sub, pkg
