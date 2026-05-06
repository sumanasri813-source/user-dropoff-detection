"""initial database schema

Revision ID: 0001_initial
Revises: 
Create Date: 2026-05-04 00:00:00.000000
"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("username", sa.String(length=100), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255)),
        sa.Column(
            "is_active", sa.Boolean(), nullable=True, server_default=sa.text("true")
        ),
        sa.Column(
            "is_admin", sa.Boolean(), nullable=True, server_default=sa.text("false")
        ),
        sa.Column("role", sa.String(length=50), nullable=True, server_default="user"),
        sa.Column("api_key", sa.String(length=255)),
        sa.Column(
            "api_key_active",
            sa.Boolean(),
            nullable=True,
            server_default=sa.text("true"),
        ),
        sa.Column("organization", sa.String(length=255)),
        sa.Column("department", sa.String(length=255)),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("last_login", sa.DateTime()),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("username"),
        sa.UniqueConstraint("api_key"),
    )

    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_username", "users", ["username"])
    op.create_index("ix_users_api_key", "users", ["api_key"])
    op.create_index("ix_users_is_active", "users", ["is_active"])
    op.create_index("ix_user_email_active", "users", ["email", "is_active"])
    op.create_index("ix_user_api_key_active", "users", ["api_key", "api_key_active"])

    op.create_table(
        "predictions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("session_duration", sa.Float(), nullable=False),
        sa.Column("pages_visited", sa.Integer(), nullable=False),
        sa.Column("items_added", sa.Integer(), nullable=False),
        sa.Column("items_removed", sa.Integer(), nullable=False),
        sa.Column("price_views", sa.Integer(), nullable=False),
        sa.Column("time_spent_product", sa.Float(), nullable=False),
        sa.Column("dropoff_probability", sa.Float(), nullable=False),
        sa.Column("risk_level", sa.String(length=20), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.Column(
            "intervention_offered",
            sa.Boolean(),
            nullable=True,
            server_default=sa.text("false"),
        ),
        sa.Column("intervention_type", sa.String(length=100)),
        sa.Column("user_responded", sa.Boolean()),
        sa.Column("conversion_after_intervention", sa.Boolean()),
        sa.Column("device_type", sa.String(length=50)),
        sa.Column("country", sa.String(length=100)),
        sa.Column("utm_source", sa.String(length=100)),
        sa.Column("utm_campaign", sa.String(length=100)),
        sa.Column(
            "model_version", sa.String(length=50), nullable=True, server_default="1.0.0"
        ),
        sa.Column("prediction_latency_ms", sa.Float()),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )

    op.create_index("ix_predictions_user_id", "predictions", ["user_id"])
    op.create_index(
        "ix_predictions_dropoff_probability", "predictions", ["dropoff_probability"]
    )
    op.create_index("ix_predictions_risk_level", "predictions", ["risk_level"])
    op.create_index(
        "ix_prediction_user_created", "predictions", ["user_id", "created_at"]
    )
    op.create_index(
        "ix_prediction_risk_level", "predictions", ["risk_level", "created_at"]
    )

    op.create_table(
        "api_calls",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("endpoint", sa.String(length=255), nullable=False),
        sa.Column("method", sa.String(length=10), nullable=False),
        sa.Column("request_path", sa.Text()),
        sa.Column("status_code", sa.Integer(), nullable=False),
        sa.Column("response_time_ms", sa.Float(), nullable=False),
        sa.Column("request_size_bytes", sa.Integer()),
        sa.Column("response_size_bytes", sa.Integer()),
        sa.Column(
            "cached_result",
            sa.Boolean(),
            nullable=True,
            server_default=sa.text("false"),
        ),
        sa.Column("error_message", sa.Text()),
        sa.Column("error_type", sa.String(length=100)),
        sa.Column("ip_address", sa.String(length=50)),
        sa.Column("user_agent", sa.Text()),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )

    op.create_index("ix_api_calls_user_id", "api_calls", ["user_id"])
    op.create_index("ix_api_calls_endpoint", "api_calls", ["endpoint"])
    op.create_index("ix_api_calls_status_code", "api_calls", ["status_code"])
    op.create_index("ix_api_call_user_created", "api_calls", ["user_id", "created_at"])
    op.create_index(
        "ix_api_call_endpoint_status",
        "api_calls",
        ["endpoint", "status_code", "created_at"],
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("resource_type", sa.String(length=100), nullable=False),
        sa.Column("resource_id", sa.Integer()),
        sa.Column("old_values", sa.Text()),
        sa.Column("new_values", sa.Text()),
        sa.Column("changes_summary", sa.Text()),
        sa.Column("ip_address", sa.String(length=50)),
        sa.Column("user_agent", sa.Text()),
        sa.Column("reason", sa.String(length=500)),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )

    op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_resource_type", "audit_logs", ["resource_type"])
    op.create_index(
        "ix_audit_user_action", "audit_logs", ["user_id", "action", "created_at"]
    )
    op.create_index(
        "ix_audit_resource",
        "audit_logs",
        ["resource_type", "resource_id", "created_at"],
    )

    op.create_table(
        "model_metrics",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("model_version", sa.String(length=50), nullable=False),
        sa.Column("accuracy", sa.Float()),
        sa.Column("precision", sa.Float()),
        sa.Column("recall", sa.Float()),
        sa.Column("f1_score", sa.Float()),
        sa.Column("roc_auc", sa.Float()),
        sa.Column("total_predictions", sa.Integer()),
        sa.Column("true_positives", sa.Integer()),
        sa.Column("true_negatives", sa.Integer()),
        sa.Column("false_positives", sa.Integer()),
        sa.Column("false_negatives", sa.Integer()),
        sa.Column("data_drift_score", sa.Float()),
        sa.Column("feature_drift", sa.Text()),
        sa.Column("compared_to_version", sa.String(length=50)),
        sa.Column("metrics_change", sa.Text()),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("evaluation_date", sa.DateTime()),
    )

    op.create_index(
        "ix_model_metrics_model_version", "model_metrics", ["model_version"]
    )
    op.create_index(
        "ix_model_metrics_version_date",
        "model_metrics",
        ["model_version", "evaluation_date"],
    )

    op.create_table(
        "system_config",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("config_key", sa.String(length=255), nullable=False),
        sa.Column("config_value", sa.Text(), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column(
            "is_feature_flag",
            sa.Boolean(),
            nullable=True,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "is_enabled", sa.Boolean(), nullable=True, server_default=sa.text("true")
        ),
        sa.Column(
            "rollout_percentage",
            sa.Integer(),
            nullable=True,
            server_default=sa.text("100"),
        ),
        sa.Column("updated_by", sa.String(length=255)),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("config_key"),
    )

    op.create_index("ix_system_config_config_key", "system_config", ["config_key"])
    op.create_index(
        "ix_config_key_enabled", "system_config", ["config_key", "is_enabled"]
    )


def downgrade():
    op.drop_index("ix_system_config_config_key", table_name="system_config")
    op.drop_index("ix_config_key_enabled", table_name="system_config")
    op.drop_table("system_config")

    op.drop_index("ix_model_metrics_model_version", table_name="model_metrics")
    op.drop_index("ix_model_metrics_version_date", table_name="model_metrics")
    op.drop_table("model_metrics")

    op.drop_index("ix_audit_logs_resource_type", table_name="audit_logs")
    op.drop_index("ix_audit_logs_action", table_name="audit_logs")
    op.drop_index("ix_audit_logs_user_id", table_name="audit_logs")
    op.drop_index("ix_audit_resource", table_name="audit_logs")
    op.drop_index("ix_audit_user_action", table_name="audit_logs")
    op.drop_table("audit_logs")

    op.drop_index("ix_api_calls_status_code", table_name="api_calls")
    op.drop_index("ix_api_calls_endpoint", table_name="api_calls")
    op.drop_index("ix_api_calls_user_id", table_name="api_calls")
    op.drop_index("ix_api_call_endpoint_status", table_name="api_calls")
    op.drop_index("ix_api_call_user_created", table_name="api_calls")
    op.drop_table("api_calls")

    op.drop_index("ix_predictions_risk_level", table_name="predictions")
    op.drop_index("ix_predictions_dropoff_probability", table_name="predictions")
    op.drop_index("ix_predictions_user_id", table_name="predictions")
    op.drop_index("ix_prediction_risk_level", table_name="predictions")
    op.drop_index("ix_prediction_user_created", table_name="predictions")
    op.drop_table("predictions")

    op.drop_index("ix_users_is_active", table_name="users")
    op.drop_index("ix_users_api_key", table_name="users")
    op.drop_index("ix_users_username", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_index("ix_user_api_key_active", table_name="users")
    op.drop_index("ix_user_email_active", table_name="users")
    op.drop_table("users")
