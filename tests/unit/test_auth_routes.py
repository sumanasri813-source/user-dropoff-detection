from __future__ import annotations

import unittest
from typing import Any, Dict

from src.api import app as api_app_module
from src.api.app import app as flask_app
from src.db import connection


class AuthRouteTests(unittest.TestCase):
    def setUp(self) -> None:
        # Use in-memory SQLite for tests
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
        # Ensure auth guard is disabled for user creation
        api_app_module.require_auth = False
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

    def test_login_and_protected_route_with_token(self) -> None:
        # Create a user with password
        payload = {
            "external_user_id": "auth_user_1",
            "email": "auth@example.com",
            "password": "s3cret",
        }
        create_resp = self.client.post("/users", json=payload)
        self.assertEqual(create_resp.status_code, 201)

        # Login
        login_resp = self.client.post(
            "/auth/login",
            json={"external_user_id": "auth_user_1", "password": "s3cret"},
        )
        self.assertEqual(login_resp.status_code, 200)
        body = login_resp.get_json()
        self.assertIn("access_token", body)
        token = body["access_token"]

        # Enable auth so guard enforces token checks and expose subject
        api_app_module.require_auth = True
        api_app_module.api_key = None

        # Access protected sample route using Bearer token
        protected = self.client.get(
            "/protected", headers={"Authorization": f"Bearer {token}"}
        )
        self.assertEqual(protected.status_code, 200)
        pbody = protected.get_json()
        self.assertTrue(pbody.get("protected"))
        self.assertIsNotNone(pbody.get("token_subject"))

    def test_refresh_and_logout_flow(self) -> None:
        # create user
        payload = {"external_user_id": "auth_user_2", "password": "pw"}
        create_resp = self.client.post("/users", json=payload)
        self.assertEqual(create_resp.status_code, 201)

        login_resp = self.client.post(
            "/auth/login", json={"external_user_id": "auth_user_2", "password": "pw"}
        )
        self.assertEqual(login_resp.status_code, 200)
        body = login_resp.get_json()
        self.assertIn("refresh_token", body)
        refresh = body["refresh_token"]

        # Refresh
        refresh_resp = self.client.post(
            "/auth/refresh", json={"refresh_token": refresh}
        )
        self.assertEqual(refresh_resp.status_code, 200)
        rbody = refresh_resp.get_json()
        self.assertIn("access_token", rbody)
        self.assertIn("refresh_token", rbody)

        # Logout (revoke)
        logout_resp = self.client.post(
            "/auth/logout", json={"refresh_token": rbody["refresh_token"]}
        )
        self.assertEqual(logout_resp.status_code, 200)
        # subsequent refresh should fail
        fail_resp = self.client.post(
            "/auth/refresh", json={"refresh_token": rbody["refresh_token"]}
        )
        self.assertEqual(fail_resp.status_code, 401)

    def test_api_key_allows_sensitive_endpoints(self) -> None:
        # enable auth with API key
        api_app_module.require_auth = True
        api_app_module.api_key = "test-key"

        # Without key should be unauthorized
        resp = self.client.get("/users")
        self.assertEqual(resp.status_code, 401)

        # With key should be allowed
        resp2 = self.client.get("/users", headers={"X-API-Key": "test-key"})
        self.assertEqual(resp2.status_code, 200)


if __name__ == "__main__":
    unittest.main()
