from __future__ import annotations

import unittest

from src.api import app as api_app_module
from src.api.app import app as flask_app
from src.db import connection


class AuditAdminDeleteTests(unittest.TestCase):
    def setUp(self) -> None:
        self.original_get_database_url = connection.get_database_url
        self.original_get_engine = connection.get_engine
        self.original_get_session_factory = connection.get_session_factory

        connection.get_database_url.cache_clear()
        connection.get_engine.cache_clear()
        connection.get_session_factory.cache_clear()

        in_memory_db_url = "sqlite:///:memory:"

        def mock_get_database_url() -> str:
            return in_memory_db_url

        connection.get_database_url = mock_get_database_url
        connection.get_engine.cache_clear()
        connection.get_session_factory.cache_clear()

        api_app_module.SessionLocal = connection.get_session_factory()
        connection.init_database()
        api_app_module.require_auth = True
        api_app_module.api_key = None
        with flask_app.app_context():
            flask_app.secret_key = api_app_module.app.secret_key
        self.client = flask_app.test_client()

    def tearDown(self) -> None:
        connection.get_database_url = self.original_get_database_url
        connection.get_engine = self.original_get_engine
        connection.get_session_factory = self.original_get_session_factory
        connection.get_database_url.cache_clear()
        connection.get_engine.cache_clear()
        connection.get_session_factory.cache_clear()
        api_app_module.require_auth = False
        api_app_module.api_key = None

    def test_admin_delete_audit_log(self) -> None:
        # create admin user
        payload = {"external_user_id": "admin_del", "password": "pw", "roles": "admin"}
        from src.db.crud import create_user, log_audit_event
        with api_app_module.SessionLocal() as session:
            u = create_user(session, payload)
            # create a sample audit entry
            ev = log_audit_event(session, user_id=u["id"], action="test_event", resource_type="test", changes_summary="x")
            log_id = ev["id"]

        # login to establish admin session
        login = self.client.post("/admin/login", json={"username": "admin_del", "password": "pw"})
        self.assertEqual(login.status_code, 200)

        # fetch dashboard to receive CSRF cookie
        _ = self.client.get("/admin/dashboard")
        # read CSRF cookie from test client
        csrf_token = self.client.get_cookie("XSRF-TOKEN")

        # delete
        if csrf_token:
            # werkzeug TestClient returns a Cookie object; use its .value
            try:
                csrf_value = getattr(csrf_token, "value", csrf_token)
            except Exception:
                csrf_value = csrf_token
        else:
            csrf_value = None
        headers = {}
        if csrf_value:
            headers["X-CSRF-Token"] = csrf_value
        delete_resp = self.client.delete(f"/admin/audit-logs/{log_id}", json={"reason": "cleanup test"}, headers=headers)
        self.assertEqual(delete_resp.status_code, 200)

        # ensure gone
        logs = self.client.get("/admin/audit-logs")
        self.assertEqual(logs.status_code, 200)
        body = logs.get_json()
        matching = [l for l in body.get("logs", []) if l.get("action") == "test_event" and l.get("resource_type") == "test"]
        self.assertEqual(matching, [])


if __name__ == "__main__":
    unittest.main()
