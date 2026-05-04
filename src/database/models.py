"""
Database models for User Dropoff Detection system.
Handles users, predictions, audit logs, and system state.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, Enum, Index
from sqlalchemy.orm import declarative_base, relationship
import enum

Base = declarative_base()


class User(Base):
    """User account model for API access and prediction tracking."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255))
    
    # Account status
    is_active = Column(Boolean, default=True, index=True)
    is_admin = Column(Boolean, default=False)
    role = Column(String(50), default="user")  # user, analyst, admin
    
    # API credentials
    api_key = Column(String(255), unique=True, index=True)
    api_key_active = Column(Boolean, default=True)
    
    # Membership
    organization = Column(String(255))
    department = Column(String(255))
    
    # Timestamps
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), index=True
    )
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
        onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
    )
    last_login = Column(DateTime)
    
    # Relationships
    predictions = relationship("Prediction", back_populates="user", cascade="all, delete-orphan")
    api_calls = relationship("APICall", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('ix_user_email_active', 'email', 'is_active'),
        Index('ix_user_api_key_active', 'api_key', 'api_key_active'),
    )


class Prediction(Base):
    """Model predictions stored for tracking and analytics."""
    __tablename__ = "predictions"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Input data
    session_duration = Column(Float, nullable=False)
    pages_visited = Column(Integer, nullable=False)
    items_added = Column(Integer, nullable=False)
    items_removed = Column(Integer, nullable=False)
    price_views = Column(Integer, nullable=False)
    time_spent_product = Column(Float, nullable=False)
    
    # Prediction results
    dropoff_probability = Column(Float, nullable=False, index=True)  # 0.0 to 1.0
    risk_level = Column(String(20), nullable=False)  # low, medium, high
    confidence_score = Column(Float, nullable=False)
    
    # Intervention tracking
    intervention_offered = Column(Boolean, default=False)
    intervention_type = Column(String(100))  # discount, free_shipping, etc.
    user_responded = Column(Boolean)
    conversion_after_intervention = Column(Boolean)
    
    # Additional context
    device_type = Column(String(50))  # desktop, mobile, tablet, app
    country = Column(String(100))
    utm_source = Column(String(100))
    utm_campaign = Column(String(100))
    
    # Metadata
    model_version = Column(String(50), default="1.0.0")
    prediction_latency_ms = Column(Float)
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), index=True
    )
    
    # Relationships
    user = relationship("User", back_populates="predictions")
    
    __table_args__ = (
        Index('ix_prediction_user_created', 'user_id', 'created_at'),
        Index('ix_prediction_risk_level', 'risk_level', 'created_at'),
    )


class APICall(Base):
    """Track all API calls for monitoring and billing."""
    __tablename__ = "api_calls"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Request details
    endpoint = Column(String(255), nullable=False, index=True)
    method = Column(String(10), nullable=False)  # GET, POST, etc.
    request_path = Column(Text)
    
    # Response details
    status_code = Column(Integer, nullable=False, index=True)
    response_time_ms = Column(Float, nullable=False)
    
    # Usage tracking
    request_size_bytes = Column(Integer)
    response_size_bytes = Column(Integer)
    cached_result = Column(Boolean, default=False)
    
    # Error tracking
    error_message = Column(Text)
    error_type = Column(String(100))
    
    # Metrics
    ip_address = Column(String(50))
    user_agent = Column(Text)
    
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), index=True
    )
    
    # Relationships
    user = relationship("User", back_populates="api_calls")
    
    __table_args__ = (
        Index('ix_api_call_user_created', 'user_id', 'created_at'),
        Index('ix_api_call_endpoint_status', 'endpoint', 'status_code', 'created_at'),
    )


class AuditLog(Base):
    """Track all system changes for compliance and debugging."""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Action details
    action = Column(String(100), nullable=False, index=True)  # create, update, delete, login, etc.
    resource_type = Column(String(100), nullable=False)  # User, Prediction, etc.
    resource_id = Column(Integer)
    
    # Change details
    old_values = Column(Text)  # JSON
    new_values = Column(Text)  # JSON
    changes_summary = Column(Text)
    
    # Context
    ip_address = Column(String(50))
    user_agent = Column(Text)
    reason = Column(String(500))
    
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), index=True
    )
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
    
    __table_args__ = (
        Index('ix_audit_user_action', 'user_id', 'action', 'created_at'),
        Index('ix_audit_resource', 'resource_type', 'resource_id', 'created_at'),
    )


class ModelMetrics(Base):
    """Track model performance over time for drift detection."""
    __tablename__ = "model_metrics"
    
    id = Column(Integer, primary_key=True)
    
    # Model info
    model_version = Column(String(50), nullable=False, index=True)
    
    # Performance metrics
    accuracy = Column(Float)
    precision = Column(Float)
    recall = Column(Float)
    f1_score = Column(Float)
    roc_auc = Column(Float)
    
    # Data metrics
    total_predictions = Column(Integer)
    true_positives = Column(Integer)
    true_negatives = Column(Integer)
    false_positives = Column(Integer)
    false_negatives = Column(Integer)
    
    # Data quality
    data_drift_score = Column(Float)  # 0.0 to 1.0 (0 = no drift)
    feature_drift = Column(Text)  # JSON with individual feature drift scores
    
    # Baseline comparison
    compared_to_version = Column(String(50))  # baseline model version
    metrics_change = Column(Text)  # JSON with metric changes
    
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), index=True
    )
    evaluation_date = Column(DateTime)
    
    __table_args__ = (
        Index('ix_model_metrics_version_date', 'model_version', 'evaluation_date'),
    )


class SystemConfig(Base):
    """Store system configuration and feature flags."""
    __tablename__ = "system_config"
    
    id = Column(Integer, primary_key=True)
    
    # Configuration keys
    config_key = Column(String(255), unique=True, nullable=False, index=True)
    config_value = Column(Text, nullable=False)  # JSON
    description = Column(Text)
    
    # Feature flags
    is_feature_flag = Column(Boolean, default=False)
    is_enabled = Column(Boolean, default=True)
    rollout_percentage = Column(Integer, default=100)  # 0-100 for gradual rollout
    
    # Management
    updated_by = Column(String(255))
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
        onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
    )
    
    __table_args__ = (
        Index('ix_config_key_enabled', 'config_key', 'is_enabled'),
    )
