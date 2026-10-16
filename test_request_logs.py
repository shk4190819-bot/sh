"""בדיקות ממוקדות ליומני הבקשות: שיוך לשרת ולבקשה, בידוד בין שרתים, מגבלות, תאימות לפורמט הישן.

הרצה:  python -m unittest test_request_logs   (או pytest)
משתני הסביבה והמסד נקבעים כאן, לפני ייבוא app (מסד SQLite זמני).
"""
import io
import logging
import os
import sys
import tempfile
import threading
import unittest

from cryptography.fernet import Fernet

_tmp = tempfile.mkdtemp()
os.environ["FLASK_SECRET_KEY"] = "test-secret"
os.environ["ENCRYPTION_KEY"] = Fernet.generate_key().decode()
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}/test.db"
os.environ["INSECURE_COOKIES"] = "1"

import app as appmod  # noqa: E402
from models import Log, Route, User, db  # noqa: E402

CODE_A = '''
from flask import Flask
import logging
app = Flask(__name__)
print("LOAD-A")
@app.route("/")
def index():
    print("PRINT-A")
    logging.getLogger("user_a").warning("LOG-A")
    return "A"
@app.route("/dup")
def dup():
    h = logging.StreamHandler(__import__("sys").stderr)   # handler של המשתמש שכותב ל-stderr (עטוף ב-tee)
    lg = logging.getLogger("user_dup")
    lg.addHandler(h)
    lg.warning("DUP-ONCE")
    print("ERR-LINE", file=__import__("sys").stderr)
    return "d"
@app.route("/e500")
def e500():
    return "bad", 500
@app.route("/boom")
def boom():
    print("BEFORE-BOOM")
    raise ValueError("boom-A")
@app.route("/spam")
def spam():
    for i in range(500):
        print("spam", i)
    print("X" * 20000)
    return "s"
@app.route("/thread")
def thread():
    import threading
    t = threading.Thread(target=lambda: print("FROM-THREAD"))
    t.start(); t.join()
    return "t"
@app.route("/secret")
def secret():
    return "ok"
'''
CODE_B = '''
from flask import Flask
app = Flask(__name__)
@app.route("/")
def index():
    print("PRINT-B")
    return "B"
'''
CODE_LOADFAIL = 'print("LOADFAIL-OUT")\nraise RuntimeError("load-fail")\n'
CODE_WSGI = 'def application(environ, start_response):\n    print("WSGI-OUT")\n    raise ZeroDivisionError("wsgi-boom")\n'


class RequestLogsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        appmod.install_log_capture()  # בטוח לקרוא שוב (ל-pytest שמחליף sys.stdout)
        cls.app = appmod.app
        cls.app.config["TESTING"] = False  # ה-handlers של המערכת פעילים כמו בפרודקשן
        with cls.app.app_context():
            u = User(username="owner", is_admin=True, is_approved=True)
            db.session.add(u)
            db.session.commit()
            cls.uid = u.id
            cls.routes = {}
            for name, code in (("srva", CODE_A), ("srvb", CODE_B), ("loadfail", CODE_LOADFAIL), ("wsgibad", CODE_WSGI)):
                r = Route(user_id=u.id, route_name=name, full_path=f"/{name}", status="active", live_code=code, live_version=1)
                db.session.add(r)
                db.session.commit()
                cls.routes[name] = r.id

    def setUp(self):
        self.client = self.app.test_client()
        with self.app.app_context():
            Log.query.delete()
            db.session.commit()
        appmod._subapps.clear()
        self.saved = (appmod.MAX_EVENTS_PER_REQUEST, appmod.MAX_LOG_MESSAGE)

    def tearDown(self):
        appmod.MAX_EVENTS_PER_REQUEST, appmod.MAX_LOG_MESSAGE = self.saved

    def logs(self, name):
        with self.app.app_context():
            rows = Log.query.filter_by(route_id=self.routes[name]).order_by(Log.id).all()
            return [appmod.parse_log(r) | {"raw": r.message} for r in rows]

    @staticmethod
    def of_kind(entries, kind):
        return [e for e in entries if e["kind"] == kind]

    # --- שיוך, request_id, בידוד
    def test_two_servers_isolated_and_linked(self):
        self.assertEqual(self.client.get("/srva/").status_code, 200)
        self.assertEqual(self.client.get("/srvb/").status_code, 200)
        a, b = self.logs("srva"), self.logs("srvb")
        self.assertTrue(all("-B" not in e["raw"] for e in a))
        self.assertTrue(all("-A" not in e["raw"] for e in b))
        self.assertIn("PRINT-A", " ".join(e["raw"] for e in a))
        self.assertIn("PRINT-B", " ".join(e["raw"] for e in b))
        # access + load print + print + logging: אותו request_id
        self.assertEqual(len({e["req"] for e in a}), 1)
        self.assertEqual(len(a[0]["req"]), 10)
        kinds = sorted(e["kind"] for e in a)
        self.assertEqual(kinds, ["access", "app", "app", "log"])  # LOAD-A, PRINT-A, LOG-A, access
        acc = self.of_kind(a, "access")[0]
        self.assertEqual(acc["method"], "GET")
        self.assertEqual(acc["status"], "200")
        self.assertIn("/srva/", acc["meta"])
        self.assertIn("Size: 1", acc["raw"])
        lg = self.of_kind(a, "log")[0]
        self.assertEqual(lg["level"], "WARNING")
        self.assertIn("Logger: user_a", lg["raw"])

    def test_route_id_correct(self):
        self.client.get("/srva/")
        self.client.get("/srvb/")
        with self.app.app_context():
            for name in ("srva", "srvb"):
                rows = Log.query.filter_by(route_id=self.routes[name]).count()
                self.assertGreater(rows, 0)
            self.assertEqual(Log.query.filter(~Log.route_id.in_(self.routes.values())).count(), 0)

    def test_distinct_request_ids(self):
        self.client.get("/srva/")
        self.client.get("/srva/")
        reqs = {e["req"] for e in self.logs("srva")}
        self.assertEqual(len(reqs), 2)

    def test_query_string_not_stored(self):
        self.client.get("/srva/secret?token=SUPERSECRET")
        self.assertTrue(all("SUPERSECRET" not in e["raw"] for e in self.logs("srva")))

    # --- stdout / duplicates / מחוץ ל-context
    def test_original_stream_still_receives_output(self):
        tee = sys.stdout
        self.assertTrue(getattr(tee, "_is_req_tee", False))
        buf, old = io.StringIO(), tee._target
        tee._target = buf
        try:
            self.client.get("/srva/")
        finally:
            tee._target = old
        self.assertIn("PRINT-A", buf.getvalue())

    def test_no_duplicates_stderr_plus_logging(self):
        err = sys.stderr
        buf, old = io.StringIO(), err._target
        err._target = buf
        try:
            self.client.get("/srva/dup")
        finally:
            err._target = old
        a = self.logs("srva")
        self.assertEqual(sum("DUP-ONCE" in e["raw"] for e in a), 1)  # אירוע logging אחד, בלי עותק מה-tee
        self.assertEqual(len([e for e in a if "ERR-LINE" in e["raw"]]), 1)
        self.assertIn("DUP-ONCE", buf.getvalue())  # והפלט המקורי ל-stderr לא אבד

    def test_output_outside_request_not_captured(self):
        before = self.count_all()
        print("OUTSIDE-REQUEST")
        print("OUTSIDE-ERR", file=sys.stderr)
        logging.getLogger("system").warning("OUTSIDE-LOG")
        self.assertEqual(self.count_all(), before)

    def test_thread_output_not_attributed(self):
        self.client.get("/srva/thread")
        self.assertTrue(all("FROM-THREAD" not in e["raw"] for e in self.logs("srva")))

    def count_all(self):
        with self.app.app_context():
            return Log.query.count()

    # --- שגיאות
    def test_user_app_returns_500(self):
        r = self.client.get("/srva/e500")
        self.assertEqual(r.status_code, 500)
        acc = self.of_kind(self.logs("srva"), "access")[-1]
        self.assertEqual(acc["status"], "500")
        self.assertEqual(acc["tone"], "bad")

    def test_user_app_raises_exception(self):
        r = self.client.get("/srva/boom")
        self.assertEqual(r.status_code, 500)
        a = self.logs("srva")
        text = " ".join(e["raw"] for e in a)
        self.assertIn("BEFORE-BOOM", text)
        self.assertIn("ValueError: boom-A", text)  # traceback נשמר
        self.assertEqual(self.of_kind(a, "access")[-1]["status"], "500")
        self.assertEqual(len({e["req"] for e in a}), 1)

    def test_wsgi_exception_is_system_error(self):
        r = self.client.get("/wsgibad/")
        self.assertEqual(r.status_code, 502)
        a = self.logs("wsgibad")
        sysev = self.of_kind(a, "system")
        self.assertEqual(len(sysev), 1)
        self.assertIn("ZeroDivisionError: wsgi-boom", sysev[0]["raw"])
        self.assertIn("run error", sysev[0]["raw"])
        self.assertIn("WSGI-OUT", " ".join(e["raw"] for e in a))
        self.assertEqual(self.of_kind(a, "access")[0]["status"], "502")
        self.assertEqual(len({e["req"] for e in a}), 1)

    def test_load_failure_attributed_to_route(self):
        r = self.client.get("/loadfail/")
        self.assertEqual(r.status_code, 502)
        a = self.logs("loadfail")
        sysev = self.of_kind(a, "system")
        self.assertEqual(len(sysev), 1)
        self.assertIn("load error", sysev[0]["raw"])
        self.assertIn("RuntimeError", sysev[0]["raw"])
        self.assertIn("LOADFAIL-OUT", " ".join(e["raw"] for e in a))  # פלט בזמן load משויך לבקשה
        for other in ("srva", "srvb", "wsgibad"):
            self.assertEqual(self.logs(other), [])

    def test_activate_failure_attributed_to_route(self):
        with self.app.app_context():
            r = db.session.get(Route, self.routes["loadfail"])
            r.pending_code = CODE_LOADFAIL
            db.session.commit()  # כמו בכל נקודות הקריאה ל-activate: הקוד הממתין כבר נשמר
            with self.assertRaises(appmod.UserError):
                appmod.activate(r)
            db.session.rollback()
        a = self.logs("loadfail")
        self.assertTrue(any("activate load error" in e["raw"] for e in self.of_kind(a, "system")))
        self.assertEqual(len({e["req"] for e in a}), 1)
        self.assertEqual(self.logs("srva"), [])

    # --- מגבלות
    def test_event_and_message_limits(self):
        appmod.MAX_EVENTS_PER_REQUEST = 5
        appmod.MAX_LOG_MESSAGE = 300
        self.client.get("/srva/spam")
        a = self.logs("srva")
        self.assertEqual(len(self.of_kind(a, "app")), 5)
        self.assertEqual(len(self.of_kind(a, "access")), 1)  # access נשמר גם מעבר למגבלה
        dropped = [e for e in self.of_kind(a, "system") if "לא נשמרו" in e["raw"]]
        self.assertEqual(len(dropped), 1)
        self.assertTrue(all(len(e["raw"]) <= 300 for e in a))

    def test_long_line_truncated(self):
        self.client.get("/srva/spam")
        self.assertTrue(all(len(e["raw"]) <= appmod.MAX_LOG_MESSAGE for e in self.logs("srva")))

    def test_pruning_keeps_row_cap(self):
        old = appmod.MAX_LOGS_PER_ROUTE
        appmod.MAX_LOGS_PER_ROUTE = 10
        try:
            with self.app.app_context():
                for i in range(30):
                    db.session.add(Log(route_id=self.routes["srvb"], message=f"Method: GET | Status: 200 | IP: {i}"))
                db.session.commit()
                appmod.prune_logs(self.routes["srvb"])
                self.assertEqual(Log.query.filter_by(route_id=self.routes["srvb"]).count(), 10)  # נשארות בדיוק MAX_LOGS_PER_ROUTE האחרונות (כמו קודם)
        finally:
            appmod.MAX_LOGS_PER_ROUTE = old

    # --- תאימות לפורמט הישן + UI
    def test_old_format_logs_still_displayed(self):
        with self.app.app_context():
            rid = self.routes["srvb"]
            db.session.add_all([
                Log(route_id=rid, message="Method: GET | Status: 200 | IP: 1.2.3.4"),
                Log(route_id=rid, message="Method: POST | Status: 502 | IP: 5.6.7.8 | load/run error"),
                Log(route_id=rid, message="some free legacy text | Status: 5 not parsed"),
            ])
            db.session.commit()
        with self.client.session_transaction() as s:
            s["user_id"] = self.uid
        r = self.client.get(f"/admin/logs/{self.routes['srvb']}")
        self.assertEqual(r.status_code, 200)
        html = r.get_data(as_text=True)
        for needle in ("1.2.3.4", "5.6.7.8", "load/run error", "POST", "some free legacy text", "st-bad"):
            self.assertIn(needle, html)
        old = self.logs("srvb")
        self.assertEqual([e["kind"] for e in old], ["access", "access", "raw"])
        self.assertEqual(old[1]["status"], "502")

    def test_new_format_rendered_in_ui(self):
        self.client.get("/srva/")
        self.client.get("/srva/boom")
        with self.client.session_transaction() as s:
            s["user_id"] = self.uid
        html = self.client.get(f"/admin/logs/{self.routes['srva']}").get_data(as_text=True)
        for needle in ("PRINT-A", "LOG-A", "WARNING", "App", "/srva/boom", "ValueError", "req "):
            self.assertIn(needle, html)

    def test_parse_log_does_not_trust_user_text(self):
        class Row:  # הודעת app שמזייפת שדות
            message = "Kind: app | Req: abc | Src: stdout | Msg: Method: GET | Status: 500 | Kind: system"
            timestamp = None
        e = appmod.parse_log(Row)
        self.assertEqual(e["kind"], "app")
        self.assertEqual(e["status"], "")


if __name__ == "__main__":
    unittest.main()
