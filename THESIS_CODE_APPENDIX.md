# Code Appendix: User Drop-Off Detection System

**Document Purpose**: Key code excerpts for thesis reference and reproducibility.

---

## 1. Model Training Pipeline

### File: `src/models/train_model.py`

**Purpose**: Multi-model candidate selection with cross-validation and metric tracking.

**Key Function: Feature Type Inference**
```python
def _infer_feature_types(df: pd.DataFrame) -> Tuple[List[str], List[str]]:
    """Infer numeric vs categorical features. O(k) where k=number of columns."""
    feature_df = df.drop(columns=[TARGET_COLUMN]).copy()
    numeric_features = feature_df.select_dtypes(include=["number"]).columns.tolist()
    categorical_features = [c for c in feature_df.columns if c not in numeric_features]
    return numeric_features, categorical_features
```

**Key Function: Preprocessing Pipeline Construction**
```python
def _build_preprocessor(numeric_features: List[str], categorical_features: List[str]) -> ColumnTransformer:
    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", OneHotEncoder(sparse_output=False, handle_unknown="ignore")),
        ]
    )
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_pipeline, numeric_features),
            ("cat", categorical_pipeline, categorical_features),
        ]
    )
    return preprocessor
```

**Model Candidates**:
- Logistic Regression (baseline)
- Random Forest (ensemble)
- XGBoost (optional, when available)

**Selection Metric**: ROC-AUC (threshold: 0.95 minimum)

**Output Artifacts**:
- `models/best_model.pkl` — Best performing model
- `models/final_model.pkl` — Finalized for production
- `results/model_comparison.csv` — Metrics comparison
- `results/training_summary.json` — Training metadata

---

## 2. Prediction Service

### File: `src/api/prediction_service.py`

**Purpose**: Model loading, feature engineering, prediction scoring.

**Key Function: Feature Loading**
```python
FEATURE_KEYS: List[str] = [
    "days_signup_age",
    "recency_days",
    "frequency_total",
    "session_duration_avg",
    "feature_count_used",
    "device_type",
    "os_type",
    "user_segment",
    "region",
]
```

**Key Function: Threshold Management**
```python
def load_decision_threshold() -> float:
    """Load threshold from evaluation output first, then config, then default."""
    eval_json = Path("results/evaluation_metrics.json")
    if eval_json.exists():
        try:
            payload = json.loads(eval_json.read_text(encoding="utf-8"))
            threshold = payload.get("metrics", {}).get("threshold")
            if threshold is not None:
                return float(threshold)
        except Exception:
            pass

    config = _try_load_config()
    threshold = config.get("prediction", {}).get("threshold", 0.5)
    return float(threshold)
```

**Risk Mapping**
```python
DEFAULT_RISK_LEVELS = {
    "high": 0.70,      # Dropoff probability >= 70%
    "medium": 0.40,    # Dropoff probability 40-70%
    "low": 0.0,        # Dropoff probability < 40%
}
```

**Key Function: Single Prediction**
```python
def predict_one(
    model: Any,
    payload: Dict[str, Any],
    threshold: float,
    risk_levels: Dict[str, float],
) -> Dict[str, Any]:
    """Inference for single user; returns probability + risk label."""
    # 1. Validate input schema
    validate_payload(payload)
    
    # 2. Extract & engineer features
    features_dict = {k: payload.get(k) for k in FEATURE_KEYS}
    features_df = pd.DataFrame([features_dict])
    features_engineered = engineer_features_for_inference(features_df)
    
    # 3. Predict probability
    prob = model.predict_proba(features_engineered)[0, 1]
    predicted_label = 1 if prob >= threshold else 0
    
    # 4. Map risk level
    risk_level = "low"
    for level_name, level_threshold in sorted(
        risk_levels.items(), 
        key=lambda x: x[1], 
        reverse=True
    ):
        if prob >= level_threshold:
            risk_level = level_name
            break
    
    # 5. Record metrics
    collector.record_prediction(
        model_name="best_model",
        dropoff_prob=prob,
        risk_level=risk_level
    )
    
    return {
        "dropoff_probability": float(prob),
        "predicted_label": int(predicted_label),
        "risk_level": risk_level,
        "threshold_used": threshold,
    }
```

---

## 3. Flask API Server

### File: `src/api/app.py`

**Purpose**: REST API endpoints for prediction, user management, health checks, monitoring.

**API Endpoints**:

| Endpoint | Method | Purpose | Auth |
|----------|--------|---------|------|
| `/health` | GET | Service health check | Optional |
| `/predict` | POST | Single user prediction | Optional |
| `/predict-batch` | POST | Batch predictions | Optional |
| `/users` | GET | List users | Optional |
| `/users` | POST | Create user | Optional |
| `/users/{id}` | GET | Get user details | Optional |
| `/users/{id}` | PUT | Update user | Optional |
| `/users/{id}` | DELETE | Delete user | Optional |
| `/predictions` | GET | List predictions | Optional |
| `/monitor` | GET | Runtime metrics snapshot | Optional |
| `/monitor/persist` | POST | Persist metrics to disk | Optional |

**Key Function: Single Prediction Endpoint**
```python
@app.route("/predict", methods=["POST"])
@require_api_key
@with_circuit_breaker(name="predict")
def handle_predict() -> tuple[Dict[str, Any], int]:
    """Single user prediction endpoint."""
    request_id = str(uuid.uuid4())
    request_id_var.set(request_id)
    
    # Rate limit check
    api_key_header = request.headers.get("X-API-Key", "anonymous")
    if not rate_limiter.allow_request(api_key_header):
        raise RateLimitError("Rate limit exceeded")
    
    # Parse & validate payload
    payload = request.get_json() or {}
    try:
        validate_payload(payload)
    except Exception as e:
        return handle_error(e, 400)
    
    # Perform prediction
    try:
        result = predict_one(model, payload, threshold, risk_levels)
    except Exception as e:
        return handle_error(e, 500)
    
    # Store prediction record
    try:
        user_id = None
        external_id = payload.get("external_user_id")
        if external_id:
            user = get_user(SessionLocal(), external_id=external_id)
            if user:
                user_id = user.id
        
        pred_record = create_prediction_record(
            SessionLocal(),
            user_id=user_id,
            request_id=request_id,
            dropoff_probability=result["dropoff_probability"],
            predicted_label=result["predicted_label"],
            risk_level=result["risk_level"],
            threshold_used=result["threshold_used"],
            payload_json=json.dumps(payload),
        )
    except Exception as e:
        logger.error("db_insert_failed", error=str(e))
    
    return jsonify(result), 200
```

**Monitoring & Background Worker**
```python
def run_monitoring_cycle() -> None:
    """Run periodic monitoring and alerting. O(k) where k=small constant metrics operations."""
    persisted = collector.maybe_persist(force=False)
    if persisted:
        logger.info("metrics_persisted", **persisted)

    health_status = HealthChecker.run_full_check().status
    alerts = evaluate_alert_rules(collector.get_api_snapshot(), health_status=health_status)
    alert_path = persist_alerts(alerts, throttle_minutes=alert_throttle_minutes)
    if alert_path and alerts:
        logger.warning("alerts_triggered", alert_count=len(alerts), alert_path=alert_path)

def start_monitoring_worker(interval_seconds: float = 30.0) -> None:
    global monitor_worker
    if monitor_worker and monitor_worker.is_running():
        return
    
    monitor_worker = BackgroundMonitorWorker(
        cycle_fn=run_monitoring_cycle,
        interval_seconds=interval_seconds,
        worker_name="api_monitor"
    )
    monitor_worker.start()
    atexit.register(lambda: monitor_worker.stop(timeout_seconds=5.0))
```

---

## 4. Database Layer

### File: `src/db/models.py`

**Purpose**: SQLAlchemy ORM models for user profiles and prediction records.

**Model: UserProfile**
```python
class UserProfile(Base):
    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    external_user_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    user_segment: Mapped[str | None] = mapped_column(String(50), nullable=True)
    device_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    os_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    region: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    predictions: Mapped[list[PredictionRecord]] = relationship(back_populates="user", cascade="all, delete-orphan")
```

**Model: PredictionRecord**
```python
class PredictionRecord(Base):
    __tablename__ = "prediction_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("user_profiles.id"), nullable=True, index=True)
    request_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    dropoff_probability: Mapped[float] = mapped_column(Float)
    predicted_label: Mapped[int] = mapped_column(Integer)
    risk_level: Mapped[str] = mapped_column(String(20))
    threshold_used: Mapped[float] = mapped_column(Float)
    payload_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    user: Mapped[UserProfile | None] = relationship(back_populates="predictions")
```

### File: `src/db/connection.py`

**Purpose**: Database connection pooling, session factory, async fallback.

**Sync Connection**
```python
@lru_cache(maxsize=1)
def get_database_url() -> str:
    return _build_database_url(_load_database_config())

@lru_cache(maxsize=1)
def get_engine() -> Engine:
    """Create SQLAlchemy engine with optimized connection pooling."""
    db_cfg = _load_database_config()
    db_url = get_database_url()
    echo = bool(db_cfg.get("echo", False))
    
    engine_kwargs = {
        "echo": echo,
        "pool_pre_ping": True,
        "future": True,
    }
    
    if not db_url.startswith("sqlite://"):
        engine_kwargs["pool_size"] = 10
        engine_kwargs["max_overflow"] = 20
        engine_kwargs["pool_recycle"] = 3600
    
    return create_engine(db_url, **engine_kwargs)

@lru_cache(maxsize=1)
def get_session_factory() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), autoflush=False, autocommit=False, expire_on_commit=False)
```

**Async Fallback** (NEW)
```python
@lru_cache(maxsize=1)
def get_async_engine() -> AsyncEngine | None:
    """Create async SQLAlchemy engine when async driver is available."""
    if create_async_engine is None:
        return None
    
    db_cfg = _load_database_config()
    async_db_url = get_async_database_url()
    echo = bool(db_cfg.get("echo", False))
    
    if not _has_required_async_driver(async_db_url):
        return None
    
    engine_kwargs = {
        "echo": echo,
        "pool_pre_ping": True,
        "future": True,
    }
    
    if not async_db_url.startswith("sqlite+aiosqlite://"):
        engine_kwargs["pool_size"] = 10
        engine_kwargs["max_overflow"] = 20
        engine_kwargs["pool_recycle"] = 3600
    
    return create_async_engine(async_db_url, **engine_kwargs)

@asynccontextmanager
async def get_async_session() -> AsyncIterator[AsyncSession | Session]:
    """Yield an async session when available, else fall back to sync Session."""
    async_factory = get_async_session_factory()
    if async_factory is not None:
        async with async_factory() as async_session:
            yield async_session
        return
    
    sync_session = get_session_factory()()
    try:
        yield sync_session
    finally:
        sync_session.close()
```

---

## 5. Feature Engineering

### File: `src/features/build_features.py`

**Purpose**: Transform raw features for model inference.

**Key Features Engineered**:
- Recency-normalized engagement
- Session intensity score
- Device-OS combination patterns
- Region-segment interaction terms

---

## 6. Data Pipeline

### File: `src/data/generate_synthetic_data.py`

**Purpose**: Generate realistic synthetic user behavior data for training and testing.

**Key Data Characteristics**:
- 1000+ synthetic users with behavioral patterns
- Imbalanced positive/negative class distribution (~30% dropoff)
- Multiple feature dimensions: temporal, device, segmentation, geographic

---

## 7. Test Suite

### File: `tests/contract/test_crud_operations.py`

**Sample Contract Test**
```python
def test_users_create_success(self) -> None:
    payload = {
        "external_user_id": "user_001",
        "email": "user@example.com",
        "user_segment": "premium"
    }
    resp = self.client.post("/users", json=payload)
    
    self.assertEqual(resp.status_code, 201)
    body = resp.get_json()
    self.assertIn("id", body)
    self.assertEqual(body["external_user_id"], "user_001")
```

**Sample Auth Test**
```python
def test_db_endpoints_require_api_key_when_enabled(self) -> None:
    api_app_module.require_auth = True
    api_app_module.api_key = "test-key"
    
    unauthorized = self.client.get("/users")
    self.assertEqual(unauthorized.status_code, 401)
    
    authorized = self.client.get("/users", headers={"X-API-Key": "test-key"})
    self.assertEqual(authorized.status_code, 200)
```

### File: `tests/integration/test_connection_async_fallback.py`

**Async Fallback Test**
```python
def test_get_async_session_falls_back_to_sync_session(self) -> None:
    def mock_get_database_url() -> str:
        return "sqlite:///:memory:"
    
    connection.get_database_url = mock_get_database_url
    # ... cache clearing ...
    
    async def _acquire_session_type_name() -> str:
        async with connection.get_async_session() as session:
            return type(session).__name__
    
    session_type_name = asyncio.run(_acquire_session_type_name())
    self.assertEqual(session_type_name, "Session")  # Falls back gracefully
```

---

## 8. Configuration

### File: `config.yaml`

**Structure**:
```yaml
database:
  type: sqlite
  database: mlops/dev.db
  echo: false

prediction:
  threshold: 0.5
  risk_levels:
    high: 0.70
    medium: 0.40
    low: 0.0

security:
  require_auth: false
  api_key: dev-local-key

monitoring:
  metrics_persist_interval_seconds: 300
  alert_throttle_minutes: 5
```

---

## 9. Dashboard UI

### File: `streamlit_dashboard.py`

**Pages**:
1. **Overview** — System status, API health, recent metrics
2. **Users** — Create, list, search user profiles
3. **Predictions** — View prediction history with filters
4. **Model** — Current model info, decision threshold, risk levels
5. **Evaluate** — Model performance metrics, ROC curves
6. **Data** — Data pipeline status, feature distributions
7. **Logs** — API and system logs

**Key Components**:
- Real-time health checks (API + DB)
- Interactive user & prediction tables
- Dynamic model switching
- Metric charting with Plotly

---

## Key Design Patterns

### 1. Modular Architecture
- **Data**: generation, preprocessing, feature engineering
- **Models**: training, evaluation, persistence
- **API**: Flask routes, prediction service, CRUD operations
- **DB**: ORM models, connection pooling, async fallback
- **Monitoring**: metrics collection, alerting, health checks

### 2. Error Handling
- Custom exception hierarchy (MLPipelineError, DatabaseError, RateLimitError)
- Circuit breaker pattern for API resilience
- Graceful degradation (e.g., async fallback to sync)

### 3. Performance & Reliability
- LRU caching for config/DB connection reuse
- Connection pooling with pre-ping
- Rate limiting per API key
- Background monitoring worker
- Request ID tracking for traceability

### 4. Testing Strategy
- Contract tests for API guarantees (28+ passing)
- Integration tests for database operations (18+ passing)
- Async fallback validation
- Full test suite runs in CI/CD

---

## Reproducibility

All artifacts are version-controlled and timestamped:
- `models/best_model.pkl` — Trained model (ROC-AUC ≈ 0.9738)
- `results/model_comparison.csv` — Candidate metrics
- `results/training_summary.json` — Training metadata
- `results/evaluation_metrics.json` — Threshold analysis
- `results/plots/*.png` — Metric visualizations

**To reproduce locally**:
```bash
python -m src.data.run_data_step
python -m src.features.build_features
python -m src.models.train_model
python -m src.evaluation.evaluate_model
python -m src.api.app
```

Or use one-click:
```bash
powershell -ExecutionPolicy Bypass -File run_final_process.ps1
```

---

**Document Version**: May 7, 2026  
**Last Updated**: Async DB fallback implementation complete
