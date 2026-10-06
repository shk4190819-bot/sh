#!/usr/bin/env python3
"""מיגרציה: כתובות שרתים מ-/<username>/<route_name> ל-/<route_name> (שם גלובלי).

שימוש:
    python migrate_global_routes.py --dry-run                 # מדפיס תוכנית, לא כותב כלום (ברירת המחדל)
    python migrate_global_routes.py --dry-run --json plan.json
    python migrate_global_routes.py --apply                   # כותב; מבקש אישור אחרי הצגת ה-DB היעד
    python migrate_global_routes.py --apply --yes             # בלי שאלה (לסקריפטים)

ה-DB נלקח מ-DATABASE_URL (או --database-url). הסקריפט לא מיובא ולא רץ מ-app.py, ואף פעם לא בזמן startup.

מה הוא עושה לכל שרת שעדיין בכתובת הישנה:
  * legacy_path = הכתובת הישנה (רק אם עוד ריק)
  * full_path   = /<route_name החדש>
  * הוותיק ביותר (created_at, ואז id) שומר על השם; שאר הכפולים, ושמות שמורים, הופכים ל-{route_name}_{username} (עד 40 תווים)
  * route_name  = השם החדש (כדי ש-route_name ו-full_path יישארו עקביים)
הרצה חוזרת בטוחה: שרתים שכבר במבנה החדש לא נוגעים בהם.
"""
import argparse
import json
import os
import sys
from collections import Counter

from sqlalchemy import create_engine, inspect, text

import route_names


def normalize_url(url):
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return url


def load_rows(conn):
    """שורות השרתים (בצירוף username). אם עמודת legacy_path עוד לא קיימת, נחשבת ריקה."""
    cols = {c["name"] for c in inspect(conn).get_columns("routes")}
    has_legacy = "legacy_path" in cols
    legacy_sel = "r.legacy_path" if has_legacy else "NULL"
    q = text(
        f"SELECT r.id, r.user_id, u.username, r.route_name, r.full_path, r.created_at, {legacy_sel} AS legacy_path "
        "FROM routes r JOIN users u ON u.id = r.user_id"
    )
    rows = [dict(m) for m in conn.execute(q).mappings()]
    for r in rows:  # datetime (PostgreSQL) או מחרוזת (SQLite): מחרוזת ISO ממיינת נכון; בלי תאריך = הוותיק ביותר
        r["created_at"] = str(r["created_at"] or "")
    return rows, has_legacy


def summarize(plan):
    c = Counter(p["action"] for p in plan)
    return {k: c.get(k, 0) for k in ("keep", "rename_duplicate", "rename_reserved", "already_migrated")}


def print_plan(plan, has_legacy):
    changes = [p for p in plan if p["action"] != "already_migrated"]
    print(f"עמודת legacy_path קיימת: {'כן' if has_legacy else 'לא (תיווצר ב-apply, או כשהאפליקציה תעלה)'}")
    print(f"סה\"כ שרתים: {len(plan)}")
    for k, v in summarize(plan).items():
        print(f"  {k:18} {v}")
    print()
    for p in changes:
        mark = "" if p["action"] == "keep" else f"   <-- {p['action']}"
        print(f"  #{p['id']:<5} {p['old_full_path']:<45} -> {p['new_full_path']}{mark}")
    renamed = [p for p in changes if p["action"] != "keep"]
    if renamed:
        print(f"\n{len(renamed)} שרתים משנים שם (הכתובת הישנה שלהם נשמרת ב-legacy_path וממשיכה לעבוד).")


def apply_plan(conn, plan, has_legacy):
    if not has_legacy:
        conn.execute(text("ALTER TABLE routes ADD COLUMN legacy_path VARCHAR(150)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_routes_legacy_path ON routes (legacy_path)"))
    upd = text(
        "UPDATE routes SET route_name = :name, full_path = :path, legacy_path = :legacy "
        "WHERE id = :id AND full_path = :old_path"  # רק אם השורה לא השתנתה מאז הקריאה (הגנה מ-race)
    )
    n = 0
    for p in plan:
        if p["action"] == "already_migrated":
            continue
        res = conn.execute(upd, {"name": p["new_name"], "path": p["new_full_path"], "legacy": p["legacy_path"],
                                 "id": p["id"], "old_path": p["old_full_path"]})
        if res.rowcount != 1:
            raise RuntimeError(f"שרת #{p['id']} השתנה בזמן המיגרציה. שום דבר לא נשמר; הרץ שוב.")
        n += 1
    return n


def mask(url):
    try:
        return url.split("@", 1)[1] if "@" in url else url
    except IndexError:
        return "?"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="מדפיס תוכנית בלבד (ברירת מחדל)")
    mode.add_argument("--apply", action="store_true", help="מבצע את השינויים ב-DB")
    ap.add_argument("--yes", action="store_true", help="עם --apply: בלי שאלת אישור")
    ap.add_argument("--database-url", default=os.environ.get("DATABASE_URL"), help="ברירת מחדל: DATABASE_URL")
    ap.add_argument("--json", metavar="FILE", help="שומר את התוכנית גם כקובץ JSON")
    args = ap.parse_args(argv)

    if not args.database_url:
        ap.error("חסר DATABASE_URL (או --database-url).")
    url = normalize_url(args.database_url)
    engine = create_engine(url)
    print(f"DB: {mask(url)}  |  מצב: {'APPLY' if args.apply else 'DRY-RUN (לא נכתב כלום)'}\n")

    with engine.connect() as conn:
        rows, has_legacy = load_rows(conn)
    plan = route_names.plan_migration(rows)
    print_plan(plan, has_legacy)
    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(plan, f, ensure_ascii=False, indent=2, default=str)
        print(f"\nהתוכנית נשמרה ב-{args.json}")

    if not args.apply:
        return 0
    if not any(p["action"] != "already_migrated" for p in plan):
        print("\nאין מה לשנות.")
        return 0
    if not args.yes and input("\nלהחיל את השינויים על ה-DB הזה? כתוב yes: ").strip().lower() != "yes":
        print("בוטל.")
        return 1
    with engine.begin() as conn:  # טרנזקציה אחת: הכול או כלום
        n = apply_plan(conn, plan, has_legacy)
    print(f"\nעודכנו {n} שרתים.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
