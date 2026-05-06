from __future__ import annotations

import os
import unittest
from datetime import timedelta

from jose import JWTError

from src.utils.auth import (create_access_token, decode_access_token,
                            get_token_subject, hash_password, load_jwt_config,
                            verify_password)


class AuthUtilityTests(unittest.TestCase):
    def test_password_hash_roundtrip(self) -> None:
        password = "S3cret-password!"
        password_hash = hash_password(password)

        self.assertNotEqual(password_hash, password)
        self.assertTrue(verify_password(password, password_hash))
        self.assertFalse(verify_password("wrong-password", password_hash))

    def test_jwt_token_roundtrip(self) -> None:
        original_secret = os.getenv("JWT_SECRET_KEY")
        original_algorithm = os.getenv("JWT_ALGORITHM")
        original_expiration = os.getenv("JWT_EXPIRATION_HOURS")
        try:
            os.environ["JWT_SECRET_KEY"] = "unit-test-secret"
            os.environ["JWT_ALGORITHM"] = "HS256"
            os.environ["JWT_EXPIRATION_HOURS"] = "2"

            secret_key, algorithm, expiration_hours = load_jwt_config()
            self.assertEqual(secret_key, "unit-test-secret")
            self.assertEqual(algorithm, "HS256")
            self.assertEqual(expiration_hours, 2)

            token = create_access_token(
                subject="user-123",
                additional_claims={"role": "analyst"},
                expires_delta=timedelta(minutes=30),
            )

            payload = decode_access_token(token)
            self.assertEqual(payload["sub"], "user-123")
            self.assertEqual(payload["role"], "analyst")
            self.assertEqual(payload["type"], "access")
            self.assertEqual(get_token_subject(token), "user-123")
        finally:
            self._restore_env("JWT_SECRET_KEY", original_secret)
            self._restore_env("JWT_ALGORITHM", original_algorithm)
            self._restore_env("JWT_EXPIRATION_HOURS", original_expiration)

    def test_invalid_token_returns_none_subject(self) -> None:
        self.assertIsNone(get_token_subject("definitely-not-a-token"))
        with self.assertRaises(JWTError):
            decode_access_token("definitely-not-a-token")

    @staticmethod
    def _restore_env(name: str, value: str | None) -> None:
        if value is None:
            os.environ.pop(name, None)
        else:
            os.environ[name] = value


if __name__ == "__main__":
    unittest.main()
