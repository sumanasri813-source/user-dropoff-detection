from __future__ import annotations

import unittest

from src.api import app as api_app_module
from src.api.app import app as flask_app
from src.db import connection


class AuditAdminTests(unittest.TestCase):
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
        # enable auth enforcement for role checks
        api_app_module.require_auth = True
        api_app_module.api_key = None
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

    def test_admin_can_view_audit_logs(self) -> None:
        # create admin user directly via DB helper (auth is enabled for endpoints)
        payload = {
            "external_user_id": "admin_user",
            "password": "adminpw",
            "roles": "admin",
        }
        from src.db.crud import create_user

        with api_app_module.SessionLocal() as session:
            user = create_user(session, payload)
            self.assertIn("id", user)

        # login to create a refresh token (which logs issuance)
        login = self.client.post(
            "/auth/login",
            json={"external_user_id": "admin_user", "password": "adminpw"},
        )
        self.assertEqual(login.status_code, 200)
        token = login.get_json()["access_token"]

        # fetch audit logs
        logs = self.client.get(
            "/admin/audit-logs", headers={"Authorization": f"Bearer {token}"}
        )
        self.assertEqual(logs.status_code, 200)
        body = logs.get_json()
        self.assertIn("logs", body)
        self.assertGreaterEqual(body.get("total", 0), 1)


if __name__ == "__main__":
    unittest.main()
