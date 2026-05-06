from __future__ import annotations

import unittest

from src.database import (
    APICall,
    AuditLog,
    Base,
    DatabaseConfig,
    ModelMetrics,
    Prediction,
    SystemConfig,
    User,
)


class DatabaseModelTests(unittest.TestCase):
    def test_expected_tables_are_registered(self) -> None:
        table_names = set(Base.metadata.tables.keys())
        self.assertSetEqual(
            table_names,
            {
                "users",
                "predictions",
                "api_calls",
                "audit_logs",
                "model_metrics",
                "system_config",
            },
        )

    def test_core_models_expose_table_names(self) -> None:
        self.assertEqual(User.__tablename__, "users")
        self.assertEqual(Prediction.__tablename__, "predictions")
        self.assertEqual(APICall.__tablename__, "api_calls")
        self.assertEqual(AuditLog.__tablename__, "audit_logs")
        self.assertEqual(ModelMetrics.__tablename__, "model_metrics")
        self.assertEqual(SystemConfig.__tablename__, "system_config")

    def test_database_url_uses_environment_configuration(self) -> None:
        original_host = DatabaseConfig.DB_HOST
        original_port = DatabaseConfig.DB_PORT
        original_name = DatabaseConfig.DB_NAME
        original_user = DatabaseConfig.DB_USER
        original_password = DatabaseConfig.DB_PASSWORD
        try:
            DatabaseConfig.DB_HOST = "db.example.com"
            DatabaseConfig.DB_PORT = "5433"
            DatabaseConfig.DB_NAME = "dropoff_test"
            DatabaseConfig.DB_USER = "test_user"
            DatabaseConfig.DB_PASSWORD = "secret"

            self.assertEqual(
                DatabaseConfig.get_database_url(),
                "postgresql://test_user:secret@db.example.com:5433/dropoff_test",
            )
        finally:
            DatabaseConfig.DB_HOST = original_host
            DatabaseConfig.DB_PORT = original_port
            DatabaseConfig.DB_NAME = original_name
            DatabaseConfig.DB_USER = original_user
            DatabaseConfig.DB_PASSWORD = original_password


if __name__ == "__main__":
    unittest.main()
