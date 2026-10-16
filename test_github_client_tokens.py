"""בדיקות לטיפול ב-installation token: פינוי מה-cache אחרי כשל אימות/הרשאה, וניסיון חוזר אחד לכל היותר.

לא מייבא את app.py (ולכן לא תלוי ב-Flask-SQLAlchemy / authlib), ורץ גם בסביבה מצומצמת.
הרצה:  python -m unittest test_github_client_tokens
"""
import os
import time
import unittest
from unittest import mock

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
PEM = _KEY.private_bytes(
    serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()
).decode()

import github_client as gc  # noqa: E402

CFG = {"slug": "sh-test-app", "client_id": "Iv1.testclient", "client_secret": "shh-client-secret", "private_key": PEM}
FUTURE = time.time() + 3600
SOON = time.time() + 100  # בתוך שולי הרענון (5 דקות): חייבים להנפיק מחדש
EXP = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() + 3600))


class FakeResp:
    def __init__(self, status=200, data=None, headers=None):
        self.status_code, self._data, self.headers = status, data if data is not None else {}, headers or {}

    def json(self):
        return self._data


def issued(token="ghs_new"):
    return FakeResp(201, {"token": token, "expires_at": EXP})


class InstallationTokenIssuanceTest(unittest.TestCase):
    def setUp(self):
        gc._token_cache.clear()
        gc._token_cache[7] = ("ghs_stale", SOON)  # יפוג בקרוב: ההנפקה תיגש ל-GitHub

    def issue(self, *responses):
        with mock.patch.object(gc.requests, "request", side_effect=list(responses)) as req:
            try:
                return gc.installation_token(7, CFG), req
            except gc.GithubError as e:
                return e, req

    def test_401_then_success_retries_exactly_once(self):
        result, req = self.issue(FakeResp(401), issued("ghs_fresh"))
        self.assertEqual(result, "ghs_fresh")
        self.assertEqual(req.call_count, 2)
        self.assertEqual(gc._token_cache[7][0], "ghs_fresh")

    def test_401_twice_stops_after_one_retry_and_evicts(self):
        err, req = self.issue(FakeResp(401), FakeResp(401), issued())  # השלישית לא אמורה להיקרא
        self.assertIsInstance(err, gc.GithubError)
        self.assertEqual(req.call_count, 2)
        self.assertNotIn(7, gc._token_cache)

    def test_403_not_retried_and_evicts(self):
        err, req = self.issue(FakeResp(403), issued())
        self.assertIsInstance(err, gc.GithubError)
        self.assertNotIsInstance(err, gc.InstallationGone)
        self.assertEqual(req.call_count, 1)
        self.assertNotIn(7, gc._token_cache)

    def test_404_evicts_and_is_installation_gone(self):
        err, req = self.issue(FakeResp(404), issued())
        self.assertIsInstance(err, gc.InstallationGone)
        self.assertEqual(req.call_count, 1)
        self.assertNotIn(7, gc._token_cache)

    def test_500_not_retried_and_cache_kept_for_other_installations(self):
        gc._token_cache[8] = ("ghs_other", FUTURE)
        err, req = self.issue(FakeResp(500), issued())
        self.assertIsInstance(err, gc.GithubError)
        self.assertEqual(req.call_count, 1)
        self.assertIn(8, gc._token_cache)  # פינוי רק של ההתקנה הרלוונטית

    def test_errors_do_not_expose_tokens_or_secrets(self):
        for status in (401, 403, 404, 500):
            gc._token_cache[7] = ("ghs_stale", SOON)
            err, _ = self.issue(FakeResp(status), FakeResp(status))
            text = str(err)
            for secret in ("ghs_stale", "ghs_new", "shh-client-secret", "PRIVATE KEY", PEM[:40]):
                self.assertNotIn(secret, text)

    def test_valid_cached_token_still_served_without_request(self):
        gc._token_cache[7] = ("ghs_ok", FUTURE)
        with mock.patch.object(gc.requests, "request") as req:
            self.assertEqual(gc.installation_token(7, CFG), "ghs_ok")
        req.assert_not_called()


class TokenRejectedAtUseTest(unittest.TestCase):
    """GitHub דוחה טוקן שנמצא ב-cache בשימוש: הוא מפונה, והבקשה הבאה מנפיקה חדש. בלי ניסיון חוזר אוטומטי כאן."""

    def setUp(self):
        gc._token_cache.clear()
        gc._token_cache[7] = ("ghs_cached", FUTURE)
        gc._token_cache[8] = ("ghs_other", FUTURE)

    def call(self, fn, status, headers=None):
        with mock.patch.object(gc.requests, "get", return_value=FakeResp(status, headers=headers)) as g:
            with self.assertRaises(gc.GithubError) as cm:
                fn("ghs_cached")
            self.assertEqual(g.call_count, 1)  # אין retry
        return str(cm.exception)

    def fetch_file(self, token):
        return gc.fetch_file("a/b", "app.py", "", token)

    def fetch_repo(self, token):
        return gc.fetch_repo("a/b", "", "", token)

    def test_401_evicts_only_the_rejected_token(self):
        for fn in (self.fetch_file, self.fetch_repo):
            gc._token_cache[7] = ("ghs_cached", FUTURE)
            msg = self.call(fn, 401)
            self.assertNotIn(7, gc._token_cache)
            self.assertIn(8, gc._token_cache)
            self.assertNotIn("ghs_cached", msg)

    def test_403_permission_evicts(self):
        for fn in (self.fetch_file, self.fetch_repo):
            gc._token_cache[7] = ("ghs_cached", FUTURE)
            self.call(fn, 403)
            self.assertNotIn(7, gc._token_cache)

    def test_403_rate_limit_does_not_evict(self):
        for fn in (self.fetch_file, self.fetch_repo):
            self.call(fn, 403, headers={"X-RateLimit-Remaining": "0"})
            self.assertIn(7, gc._token_cache)

    def test_404_and_500_do_not_evict(self):
        for status in (404, 500):
            for fn in (self.fetch_file, self.fetch_repo):
                self.call(fn, status)
                self.assertIn(7, gc._token_cache)

    def test_pat_never_matches_cache(self):
        with mock.patch.object(gc.requests, "get", return_value=FakeResp(401)):
            with self.assertRaises(gc.GithubError):
                gc.fetch_file("a/b", "app.py", "", "github_pat_whatever")
        self.assertEqual(set(gc._token_cache), {7, 8})

    def test_forget_token_handles_none_and_empty(self):
        gc.forget_token(None)
        gc.forget_token("")
        self.assertEqual(set(gc._token_cache), {7, 8})

    def test_next_request_after_eviction_issues_a_new_token(self):
        self.call(self.fetch_file, 401)
        with mock.patch.object(gc.requests, "request", return_value=issued("ghs_renewed")) as req:
            self.assertEqual(gc.installation_token(7, CFG), "ghs_renewed")
        self.assertEqual(req.call_count, 1)


if __name__ == "__main__":
    unittest.main()
