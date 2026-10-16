"""בדיקות לחיבור GitHub App: JWT, installation token + cache, ושיוך מאובטח של התקנה למשתמש. הכול עם mock, בלי רשת.

הרצה:  python -m unittest test_github_app   (או pytest)
"""
import base64
import json
import os
import tempfile
import time
import unittest
from unittest import mock

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

_tmp = tempfile.mkdtemp()
os.environ["FLASK_SECRET_KEY"] = "test-secret"
os.environ["ENCRYPTION_KEY"] = Fernet.generate_key().decode()
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}/test_gh.db"
os.environ["INSECURE_COOKIES"] = "1"

_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
PEM = _KEY.private_bytes(
    serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()
).decode()
os.environ.update({
    "GITHUB_APP_SLUG": "sh-test-app",
    "GITHUB_APP_CLIENT_ID": "Iv1.testclient",
    "GITHUB_APP_CLIENT_SECRET": "shh",
    "GITHUB_APP_PRIVATE_KEY": PEM.replace("\n", "\\n"),  # כמו שמדביקים במשתנה סביבה
})

import app as appmod  # noqa: E402
import github_client as gc  # noqa: E402
from models import ApiKey, Route, RouteSource, User, db  # noqa: E402


def _b64d(part):
    return base64.urlsafe_b64decode(part + "=" * (-len(part) % 4))


class FakeResp:
    def __init__(self, status=200, data=None, headers=None):
        self.status_code, self._data, self.headers = status, data if data is not None else {}, headers or {}

    def json(self):
        return self._data


class GithubClientTest(unittest.TestCase):
    def setUp(self):
        gc._token_cache.clear()

    def test_config_reads_escaped_newlines(self):
        cfg = gc.app_config()
        self.assertEqual(cfg["slug"], "sh-test-app")
        self.assertIn("\n", cfg["private_key"])

    def test_config_missing_returns_none(self):
        with mock.patch.dict(os.environ, {"GITHUB_APP_SLUG": ""}):
            self.assertIsNone(gc.app_config())

    def test_jwt_is_valid_rs256(self):
        now = 1_700_000_000
        tok = gc.make_app_jwt("Iv1.testclient", PEM, now=now)
        h, p, sig = tok.split(".")
        self.assertEqual(json.loads(_b64d(h)), {"alg": "RS256", "typ": "JWT"})
        payload = json.loads(_b64d(p))
        self.assertEqual(payload["iss"], "Iv1.testclient")
        self.assertEqual(payload["exp"] - payload["iat"], 600)
        _KEY.public_key().verify(_b64d(sig), f"{h}.{p}".encode(), padding.PKCS1v15(), hashes.SHA256())

    def test_jwt_bad_key(self):
        with self.assertRaises(gc.GithubError):
            gc.make_app_jwt("x", "not a key")

    def test_installation_token_cached_and_refreshed(self):
        exp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() + 3600))
        with mock.patch.object(gc.requests, "request",
                               return_value=FakeResp(201, {"token": "ghs_a", "expires_at": exp})) as req:
            self.assertEqual(gc.installation_token(7), "ghs_a")
            self.assertEqual(gc.installation_token(7), "ghs_a")
            self.assertEqual(req.call_count, 1)
            self.assertEqual(req.call_args.kwargs["json"], {"permissions": {"contents": "read", "metadata": "read"}})
        soon = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() + 100))  # פחות מ-5 דקות: מנפיקים מחדש
        gc._token_cache[7] = ("ghs_old", gc._expiry_epoch(soon))
        with mock.patch.object(gc.requests, "request",
                               return_value=FakeResp(201, {"token": "ghs_b", "expires_at": exp})):
            self.assertEqual(gc.installation_token(7), "ghs_b")

    def test_installation_gone(self):
        with mock.patch.object(gc.requests, "request", return_value=FakeResp(404)):
            with self.assertRaises(gc.InstallationGone):
                gc.installation_token(9)

    def test_exchange_code_failure(self):
        with mock.patch.object(gc.requests, "request",
                               return_value=FakeResp(200, {"error": "bad_verification_code"})):
            with self.assertRaises(gc.GithubError):
                gc.exchange_code("c", gc.app_config())


class CallbackTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = appmod.app
        with cls.app.app_context():
            for name in ("alice", "mallory"):
                u = User(username=name, is_approved=True)
                db.session.add(u)
            db.session.commit()
            cls.alice = User.query.filter_by(username="alice").first().id
            cls.mallory = User.query.filter_by(username="mallory").first().id

    def setUp(self):
        # בלי לשנות את ההגדרה המשותפת לצמיתות: משנים לבדיקה הזו בלבד ומשחזרים בסיומה
        had, old = "WTF_CSRF_ENABLED" in self.app.config, self.app.config.get("WTF_CSRF_ENABLED")
        self.app.config["WTF_CSRF_ENABLED"] = False
        self.addCleanup(lambda: self.app.config.__setitem__("WTF_CSRF_ENABLED", old) if had
                        else self.app.config.pop("WTF_CSRF_ENABLED", None))
        self.client = self.app.test_client()
        gc._token_cache.clear()
        with self.app.app_context():
            ApiKey.query.delete()
            db.session.commit()

    def login(self, uid, state="st1", age=0, state_uid=None):
        with self.client.session_transaction() as s:
            s["user_id"] = uid
            if state:
                s["gh_app_state"] = {"s": state, "u": state_uid or uid, "t": int(time.time()) - age}

    def link(self, uid):
        with self.app.app_context():
            u = db.session.get(User, uid)
            return appmod.get_github_app_link(u)

    def callback(self, **params):
        base = {"code": "c1", "installation_id": "55", "state": "st1", "setup_action": "install"}
        base.update(params)
        return self.client.get("/settings/github/app/callback", query_string=base)

    def patches(self, installs=(55,), login="alice", info=None):
        info = info or {"login": "alice", "type": "User", "repository_selection": "selected"}
        return mock.patch.multiple(
            gc,
            exchange_code=mock.Mock(return_value="ghu_user"),
            user_login=mock.Mock(return_value=login),
            user_installation_ids=mock.Mock(return_value=set(installs)),
            installation_info=mock.Mock(return_value=info),
        )

    # --- connect
    def test_connect_redirects_with_state(self):
        self.login(self.alice, state=None)
        r = self.client.post("/settings/github/app/connect")
        self.assertEqual(r.status_code, 302)
        self.assertTrue(r.location.startswith("https://github.com/apps/sh-test-app/installations/new?state="))
        with self.client.session_transaction() as s:
            self.assertIn(s["gh_app_state"]["s"], r.location)
            self.assertEqual(s["gh_app_state"]["u"], self.alice)

    def test_connect_requires_login(self):
        r = self.client.post("/settings/github/app/connect")
        self.assertIn("/login", r.location)

    # --- callback: happy path
    def test_happy_path_stores_encrypted_link(self):
        self.login(self.alice)
        with self.patches():
            r = self.callback()
        self.assertEqual(r.status_code, 302)
        self.assertTrue(r.location.endswith("/account"))
        self.assertEqual(self.link(self.alice), {"installation_id": 55, "login": "alice", "type": "User"})
        with self.app.app_context():
            row = ApiKey.query.filter_by(user_id=self.alice, provider="github_app").first()
            self.assertNotIn("alice", row.encrypted_key)  # מוצפן
        with self.client.session_transaction() as s:
            self.assertNotIn("gh_app_state", s)  # חד-פעמי

    # --- callback: דחיות
    def test_foreign_installation_rejected(self):
        """משתמש זדוני עם state תקף משלו ו-installation_id של מישהו אחר: ההתקנה לא ברשימה של הטוקן שלו."""
        self.login(self.mallory)
        with self.patches(installs=(99,), login="mallory"):
            self.callback(installation_id="55")
        self.assertIsNone(self.link(self.mallory))

    def test_bad_state_rejected(self):
        self.login(self.alice)
        with self.patches():
            self.callback(state="other")
        self.assertIsNone(self.link(self.alice))

    def test_state_bound_to_user(self):
        self.login(self.mallory, state_uid=self.alice)
        with self.patches(login="mallory", info={"login": "mallory", "type": "User"}):
            self.callback()
        self.assertIsNone(self.link(self.mallory))

    def test_expired_state_rejected(self):
        self.login(self.alice, age=601)
        with self.patches():
            self.callback()
        self.assertIsNone(self.link(self.alice))

    def test_state_is_single_use(self):
        self.login(self.alice)
        with self.patches():
            self.callback()
            with self.app.app_context():
                ApiKey.query.delete()
                db.session.commit()
            self.callback()  # אותה כתובת שוב
        self.assertIsNone(self.link(self.alice))

    def test_missing_state_param_only_message(self):
        self.login(self.alice, state=None)
        with self.patches() as _:
            r = self.callback(state="", setup_action="update", code="")
        self.assertEqual(r.status_code, 302)
        self.assertIsNone(self.link(self.alice))

    def test_request_action_no_link(self):
        self.login(self.alice)
        r = self.callback(setup_action="request", code="")
        self.assertEqual(r.status_code, 302)
        self.assertIsNone(self.link(self.alice))

    def test_org_installation_rejected(self):
        self.login(self.alice)
        with self.patches(info={"login": "acme", "type": "Organization", "repository_selection": "all"}):
            self.callback()
        self.assertIsNone(self.link(self.alice))

    def test_personal_installation_of_other_login_rejected(self):
        self.login(self.alice)
        with self.patches(info={"login": "someoneelse", "type": "User"}):
            self.callback()
        self.assertIsNone(self.link(self.alice))

    def test_missing_code_rejected(self):
        self.login(self.alice)
        with self.patches():
            self.callback(code="")
        self.assertIsNone(self.link(self.alice))

    def test_requires_login(self):
        r = self.callback()
        self.assertIn("/login", r.location)

    # --- disconnect + get_github_token
    def test_disconnect(self):
        self.login(self.alice)
        with self.patches():
            self.callback()
        self.assertIsNotNone(self.link(self.alice))
        r = self.client.post("/settings/github/app/disconnect")
        self.assertEqual(r.status_code, 302)
        self.assertIsNone(self.link(self.alice))

    # --- תיקון 1: get_github_token לא נופל בשקט ל-PAT כשיש חיבור App
    def _add_pat(self, uid, value=b"pat_123"):
        with self.app.app_context():
            db.session.add(ApiKey(user_id=uid, provider="github", encrypted_key=appmod.fernet.encrypt(value).decode()))
            db.session.commit()

    def _link_app(self, uid):
        self.login(uid)
        with self.patches():
            self.callback()
        self.assertIsNotNone(self.link(uid))

    def _token(self, uid):
        with self.app.app_context():
            return appmod.get_github_token(db.session.get(User, uid))

    def test_token_pat_used_only_when_no_app_link(self):
        self._add_pat(self.alice)
        self.assertEqual(self._token(self.alice), "pat_123")
        self.assertIsNone(self._token(self.mallory))  # בלי PAT ובלי App

    def test_token_prefers_app_when_linked(self):
        self._add_pat(self.alice)
        self._link_app(self.alice)
        with mock.patch.object(gc, "installation_token", return_value="ghs_x") as m:
            self.assertEqual(self._token(self.alice), "ghs_x")
            m.assert_called_once_with(55)

    def test_token_revoked_installation_raises_not_pat(self):
        self._add_pat(self.alice)
        self._link_app(self.alice)
        with mock.patch.object(gc, "installation_token", side_effect=gc.InstallationGone("gone")):
            with self.assertRaises(appmod.UserError) as cm:
                self._token(self.alice)
        self.assertIn("הוסרה", str(cm.exception))

    def test_token_issuance_failure_raises_not_pat(self):
        self._add_pat(self.alice)
        self._link_app(self.alice)
        with mock.patch.object(gc, "installation_token", side_effect=gc.GithubError("boom 500")):
            with self.assertRaises(appmod.UserError) as cm:
                self._token(self.alice)
        self.assertIn("boom 500", str(cm.exception))
        self.assertNotIn("pat_123", str(cm.exception))

    def test_token_app_not_configured_raises_not_pat(self):
        self._add_pat(self.alice)
        self._link_app(self.alice)
        with mock.patch.object(gc, "app_config", return_value=None):
            with self.assertRaises(appmod.UserError):
                self._token(self.alice)

    def test_token_corrupt_app_link_raises_not_pat(self):
        self._add_pat(self.alice)
        with self.app.app_context():
            db.session.add(ApiKey(user_id=self.alice, provider="github_app", encrypted_key="not-a-fernet-token"))
            db.session.commit()
        with self.assertRaises(appmod.UserError):
            self._token(self.alice)

    def test_sync_route_with_revoked_app_does_not_fetch_with_pat(self):
        """הנתיב המלא (POST /sync/<id>): UserError מגיע למשתמש כהפניה עם הודעה, ושום קריאה ל-GitHub לא נעשית עם ה-PAT."""
        self._add_pat(self.alice)
        self._link_app(self.alice)
        with self.app.app_context():
            r = Route(user_id=self.alice, route_name="syncme", full_path="/syncme", status="active",
                      live_code="from flask import Flask\napp = Flask(__name__)\n", live_version=1)
            db.session.add(r)
            db.session.commit()
            db.session.add(RouteSource(route_id=r.id, repo="a/b", path="app.py", ref="", sha="old"))
            db.session.commit()
            rid = r.id
        try:
            self.login(self.alice, state=None)
            with mock.patch.object(gc, "installation_token", side_effect=gc.InstallationGone("gone")), \
                    mock.patch.object(gc, "fetch_file") as ff, mock.patch.object(gc, "fetch_repo") as fr:
                resp = self.client.post(f"/sync/{rid}")
            self.assertEqual(resp.status_code, 302)
            ff.assert_not_called()
            fr.assert_not_called()
        finally:
            with self.app.app_context():
                db.session.delete(db.session.get(Route, rid))
                db.session.commit()

    # --- תיקון 2: gh_app_state נצרך רק כשיש state בבקשה
    def _pending_state(self):
        with self.client.session_transaction() as s:
            return s.get("gh_app_state")

    def test_stray_callback_without_state_keeps_pending_state(self):
        self.login(self.alice)
        for params in ({"state": "", "setup_action": "update", "code": ""},
                       {"state": "", "setup_action": "request", "code": ""},
                       {"state": "", "code": "", "installation_id": ""}):
            self.callback(**params)
            self.assertIsNotNone(self._pending_state(), params)
            self.assertEqual(self._pending_state()["s"], "st1")
        with self.patches():  # והחיבור שהיה בתהליך עדיין מצליח
            self.callback()
        self.assertEqual(self.link(self.alice)["installation_id"], 55)
        self.assertIsNone(self._pending_state())

    def test_callback_with_wrong_state_still_consumes_state(self):
        self.login(self.alice)
        with self.patches():
            self.callback(state="other")
        self.assertIsNone(self._pending_state())
        self.assertIsNone(self.link(self.alice))

    def test_callback_with_state_consumes_and_checks_user_and_expiry(self):
        for kwargs in ({"state_uid": self.mallory}, {"age": 601}):
            self.login(self.alice, **kwargs)
            with self.patches():
                self.callback()
            self.assertIsNone(self._pending_state(), kwargs)
            self.assertIsNone(self.link(self.alice), kwargs)

    def test_account_page_renders_states(self):
        self.login(self.alice, state=None)
        html = self.client.get("/account").get_data(as_text=True)
        self.assertIn("Connect GitHub", html)
        self.login(self.alice)
        with self.patches():
            self.callback()
        html = self.client.get("/account").get_data(as_text=True)
        self.assertIn("@alice", html)
        self.assertIn("github.com/settings/installations/55", html)
        self.assertNotIn("Connect GitHub", html)


if __name__ == "__main__":
    unittest.main()
