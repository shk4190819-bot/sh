"""שמות שרתים גלובליים: ולידציה, שמות שמורים ותכנון מיגרציה.

מודול טהור (בלי Flask ובלי DB), כדי ש-app.py וגם סקריפט המיגרציה ישתמשו באותם כללים בלי לייבא את app.py
(שהייבוא שלו מריץ create_all מול ה-DB).
"""
import re

MAX_ROUTE_NAME = 40
# superset של ה-regex הישן ([a-z0-9][a-z0-9_]{0,39}): כל שם קיים נשאר תקף, ובנוסף מותר "-"
ROUTE_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,39}$")

# הסגמנט הראשון של כל route במערכת + שמות שמורים נוספים. app.py מוסיף על זה את מה שנגזר מ-app.url_map,
# והסקריפט של המיגרציה (שלא יכול לייבא את app.py) משתמש ברשימה הזו בלבד. test_routing.py בודק שאין סטייה.
RESERVED_STATIC = frozenset({
    # routes של המערכת
    "admin", "auth", "login", "logout", "static", "settings", "deploy", "healthz", "new", "account", "pending",
    "edit", "delete", "sync",
    # קבצים שדפדפנים ובוטים מבקשים מהשורש
    "favicon", "robots", "sitemap",
})
# היו שמורים בעבר לשמות משתמש בלבד. הם לא routes של המערכת, ולכן אינם חוסמים שמות שרתים (שרתים קיימים בשם api נשארים)
USERNAME_EXTRA_RESERVED = frozenset({"api", "review"})


class RouteNameError(ValueError):
    """הודעה שבטוח להציג למשתמש."""


def derive_reserved(url_map):
    """הסגמנט הסטטי הראשון של כל כלל ב-url_map (למשל /edit/<int:id> -> edit). כללים שמתחילים בפרמטר מדלגים."""
    out = set()
    for rule in url_map.iter_rules():
        parts = rule.rule.split("/")
        first = parts[1] if len(parts) > 1 else ""
        if first and not first.startswith("<"):
            out.add(first)
    return out


def check_route_name(name, reserved):
    """מחזיר את השם התקין, או זורק RouteNameError עם הודעה בעברית. לא בודק ייחודיות (זה מול ה-DB)."""
    if not isinstance(name, str) or not name:
        raise RouteNameError("לא הוזן שם נתיב.")
    if "/" in name or "\\" in name or ".." in name:
        raise RouteNameError("שם הנתיב לא יכול להכיל / או \\ או ..")
    if len(name) > MAX_ROUTE_NAME:
        raise RouteNameError(f"שם הנתיב ארוך מדי (עד {MAX_ROUTE_NAME} תווים).")
    if not ROUTE_RE.match(name):
        raise RouteNameError("שם נתיב: אנגלית קטנה, ספרות, _ ו- בלבד, ומתחיל באות או ספרה.")
    if name in reserved:
        raise RouteNameError(f"השם {name} שמור למערכת. בחר שם אחר.")
    return name


def duplicate_name(route_name, username, taken, n=1):
    """{route_name}_{username} עד 40 תווים. אם תפוס (ב-taken), מוסיף _2, _3... ומקצר את route_name לפי הצורך."""
    while True:
        suffix = f"_{username}" + ("" if n == 1 else f"_{n}")
        base = route_name[: max(1, MAX_ROUTE_NAME - len(suffix))]
        cand = (base + suffix)[:MAX_ROUTE_NAME]
        if cand not in taken:
            return cand
        n += 1


def plan_migration(rows, reserved=RESERVED_STATIC):
    """מתכנן את המעבר לשמות גלובליים. לא נוגע ב-DB.

    rows: רשימת dict עם id, username, route_name, full_path, created_at, legacy_path (או None).
    מחזיר רשימת dict (מסודרת לפי ותק): id, username, route_name (הישן), new_name, old_full_path, new_full_path,
    legacy_path (מה שיישמר), action: keep | rename_duplicate | rename_reserved | already_migrated.
    """
    ordered = sorted(rows, key=lambda r: (r["created_at"], r["id"]))
    all_original = {r["route_name"] for r in ordered}
    # שורות שכבר במבנה החדש (full_path == /name) שומרות על השם שלהן ופוסלות אותו לאחרים
    taken = {r["route_name"] for r in ordered if r["full_path"] == f"/{r['route_name']}"}
    out = []
    for r in ordered:
        base = {
            "id": r["id"], "username": r["username"], "route_name": r["route_name"],
            "old_full_path": r["full_path"],
        }
        if r["full_path"] == f"/{r['route_name']}":
            out.append({**base, "new_name": r["route_name"], "new_full_path": r["full_path"],
                        "legacy_path": r.get("legacy_path"), "action": "already_migrated"})
            continue
        name, action = r["route_name"], "keep"
        if name in reserved or not ROUTE_RE.match(name):
            action = "rename_reserved"
        elif name in taken:
            action = "rename_duplicate"
        if action != "keep":
            # המועמד לא יכול להתנגש גם עם שם מקורי של שרת אחר שעוד לא עובד (כדי שלא ניקח לו את השם הטבעי שלו)
            name = duplicate_name(r["route_name"], r["username"], taken | all_original | set(reserved))
        taken.add(name)
        out.append({**base, "new_name": name, "new_full_path": f"/{name}",
                    "legacy_path": r.get("legacy_path") or r["full_path"], "action": action})
    return out
