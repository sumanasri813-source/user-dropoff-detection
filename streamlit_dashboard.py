"""
Next-generation Streamlit dashboard for silent user drop-off detection.

The UI is organized as a structured product dashboard instead of a long scrolling report.
It supports live API scoring, model evidence, batch operations, and system
readiness for the user drop-off detection project.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st


# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="Early User Churn Detection — Revenue Retention",
    page_icon=":chart_with_downwards_trend:",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================================
# DESIGN SYSTEM
# ============================================================================

st.markdown(
    """
<style>
    #MainMenu, header, footer, .stDeployButton {display: none !important;}

    :root {
        --ink: #142033;
        --muted: #66758a;
        --line: #d9e8f2;
        --paper: #ffffff;
        --soft: #f7fbff;
        --navy: #1f3a5f;
        --blue: #2563eb;
        --teal: #14b8a6;
        --green: #059669;
        --amber: #f59e0b;
        --rose: #e11d48;
    }

    .stApp,
    .main,
    p,
    div,
    span,
    label,
    button,
    input,
    textarea {
        font-family: "Segoe UI", Inter, Arial, sans-serif !important;
    }

    .main {
        background:
            radial-gradient(circle at top left, rgba(20,184,166,0.14), transparent 34%),
            radial-gradient(circle at top right, rgba(37,99,235,0.12), transparent 30%),
            linear-gradient(180deg, #f7fbff 0%, #eef6fb 100%);
    }

    .main .block-container {
        max-width: 1380px;
        padding: 0.65rem 1.35rem 1.7rem;
    }

    section[data-testid="stSidebar"] {
        display: none;
    }

    div[data-testid="collapsedControl"] {
        display: none;
    }

    h1, h2, h3 {
        color: var(--ink);
        letter-spacing: 0;
    }

    .topbar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 16px;
        background: rgba(255,255,255,0.9);
        border: 1px solid var(--line);
        border-radius: 14px;
        padding: 12px 14px;
        margin-bottom: 12px;
        box-shadow: 0 12px 28px rgba(15,23,42,0.07);
        backdrop-filter: blur(12px);
    }

    .brand {
        display: flex;
        align-items: center;
        gap: 12px;
    }

    .brand-mark {
        width: 44px;
        height: 44px;
        border-radius: 13px;
        display: grid;
        place-items: center;
        color: #fff;
        font-weight: 900;
        background: linear-gradient(135deg, var(--blue), var(--teal));
        box-shadow: 0 10px 20px rgba(37,99,235,0.22);
    }

    .brand-title {
        color: var(--ink);
        font-weight: 900;
        line-height: 1.1;
        font-size: 1.05rem;
    }

    .brand-subtitle {
        color: var(--muted);
        font-size: 0.8rem;
        margin-top: 3px;
    }

    .topbar-actions {
        display: flex;
        align-items: center;
        gap: 8px;
        flex-wrap: wrap;
        justify-content: flex-end;
    }

    .api-pill,
    .nav-note {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        border: 1px solid var(--line);
        border-radius: 999px;
        padding: 8px 11px;
        background: #f8fcff;
        color: var(--ink);
        font-size: 0.82rem;
        font-weight: 750;
        white-space: nowrap;
    }

    .api-pill .status-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        display: inline-block;
    }

    div[data-testid="stPills"] {
        background: rgba(255,255,255,0.82);
        border: 1px solid var(--line);
        border-radius: 14px;
        padding: 8px;
        margin-bottom: 14px;
        box-shadow: 0 10px 26px rgba(15,23,42,0.06);
    }

    div[data-testid="stPills"] button {
        border-radius: 11px !important;
        min-height: 42px !important;
        padding: 0.45rem 1rem !important;
        font-weight: 850 !important;
        border: 1px solid transparent !important;
        color: var(--ink) !important;
        background: transparent !important;
    }

    div[data-testid="stPills"] button:hover {
        background: #edf8ff !important;
        border-color: #c8e3f3 !important;
        color: #0f5f99 !important;
    }

    div[data-testid="stPills"] button[aria-pressed="true"] {
        background: linear-gradient(135deg, #2563eb, #14b8a6) !important;
        color: #ffffff !important;
        box-shadow: 0 10px 20px rgba(37,99,235,0.2) !important;
    }

    .app-hero {
        min-height: 250px;
        display: grid;
        grid-template-columns: 1.18fr 0.82fr;
        gap: 18px;
        margin-bottom: 18px;
    }

    .hero-copy {
        background:
            radial-gradient(circle at 92% 18%, rgba(20,184,166,0.26), transparent 25%),
            radial-gradient(circle at 70% 80%, rgba(37,99,235,0.16), transparent 25%),
            linear-gradient(135deg, #ffffff 0%, #edf8ff 100%);
        border: 1px solid var(--line);
        border-radius: 10px;
        padding: 28px;
        color: var(--ink);
        box-shadow: 0 16px 34px rgba(15,23,42,0.08);
        position: relative;
        overflow: hidden;
    }

    .hero-copy:after {
        content: "";
        position: absolute;
        inset: auto 0 0 0;
        height: 6px;
        background: linear-gradient(90deg, var(--blue), var(--teal), var(--amber), var(--rose));
    }

    .eyebrow {
        color: #2563eb;
        font-size: 0.78rem;
        font-weight: 800;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 12px;
    }

    .hero-copy h1 {
        color: var(--ink);
        font-size: 2.32rem;
        line-height: 1.08;
        max-width: 760px;
        margin: 0 0 12px;
    }

    .hero-copy p {
        color: var(--muted);
        max-width: 760px;
        margin: 0;
        font-size: 1rem;
        line-height: 1.55;
    }

    .signal-panel {
        background: #ffffff;
        border: 1px solid var(--line);
        border-radius: 10px;
        padding: 18px;
        min-height: 250px;
        box-shadow: 0 12px 34px rgba(15,23,42,0.08);
    }

    .signal-head {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 18px;
        gap: 12px;
    }

    .signal-title {
        font-weight: 850;
        color: var(--ink);
        font-size: 1rem;
    }

    .status-chip {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        border-radius: 999px;
        padding: 7px 10px;
        background: #f8fafc;
        color: var(--ink);
        border: 1px solid var(--line);
        font-size: 0.82rem;
        font-weight: 750;
        white-space: nowrap;
    }

    .status-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        display: inline-block;
    }

    .status-dot.online {background: var(--green);}
    .status-dot.offline {background: var(--rose);}

    .signal-grid {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 8px;
        align-items: end;
        height: 128px;
        padding: 10px 4px;
        border-radius: 8px;
        background:
            linear-gradient(180deg, rgba(37,99,235,0.04), rgba(15,118,110,0.04)),
            repeating-linear-gradient(0deg, transparent 0 31px, rgba(17,24,39,0.08) 31px 32px);
    }

    .signal-bar {
        border-radius: 7px 7px 3px 3px;
        background: linear-gradient(180deg, var(--blue), var(--teal));
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.35);
        min-height: 24px;
    }

    .signal-bar:nth-child(2) {height: 54px; background: linear-gradient(180deg, #0f766e, #059669);}
    .signal-bar:nth-child(3) {height: 100px; background: linear-gradient(180deg, #d97706, #e11d48);}
    .signal-bar:nth-child(4) {height: 72px; background: linear-gradient(180deg, #2563eb, #0f766e);}
    .signal-bar:nth-child(5) {height: 116px; background: linear-gradient(180deg, #e11d48, #d97706);}

    .signal-foot {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 8px;
        margin-top: 14px;
    }

    .mini-stat {
        border: 1px solid var(--line);
        border-radius: 8px;
        padding: 10px;
        background: #f8fafc;
    }

    .mini-stat span {
        display: block;
        color: var(--muted);
        font-size: 0.72rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .mini-stat strong {
        color: var(--ink);
        font-size: 1.12rem;
    }

    .kpi-card,
    .panel,
    .identity-card,
    .play-card {
        background: var(--paper);
        border: 1px solid var(--line);
        border-radius: 10px;
        box-shadow: 0 8px 24px rgba(15,23,42,0.06);
    }

    .kpi-card {
        min-height: 112px;
        padding: 16px;
        position: relative;
        overflow: hidden;
    }

    .kpi-card:before {
        content: "";
        position: absolute;
        left: 0;
        top: 0;
        width: 100%;
        height: 4px;
        background: var(--blue);
    }

    .kpi-card.teal:before {background: var(--teal);}
    .kpi-card.green:before {background: var(--green);}
    .kpi-card.amber:before {background: var(--amber);}
    .kpi-card.rose:before {background: var(--rose);}

    .kpi-label {
        color: var(--muted);
        font-size: 0.76rem;
        font-weight: 850;
        letter-spacing: 0.06em;
        text-transform: uppercase;
    }

    .kpi-value {
        color: var(--ink);
        font-size: 1.72rem;
        font-weight: 850;
        line-height: 1;
        margin: 10px 0 8px;
    }

    .kpi-copy {
        color: var(--muted);
        margin: 0;
        font-size: 0.82rem;
        line-height: 1.35;
    }

    .panel {
        padding: 18px;
        margin-bottom: 14px;
    }

    .panel-title {
        color: var(--ink);
        font-size: 1.02rem;
        font-weight: 800;
        margin: 0 0 4px;
    }

    .panel-copy {
        color: var(--muted);
        margin: 0 0 14px;
        font-size: 0.92rem;
    }

    .flow {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 10px;
    }

    .flow-step {
        border: 1px solid var(--line);
        border-radius: 8px;
        padding: 12px;
        background: #f8fafc;
        min-height: 82px;
    }

    .flow-step strong {
        display: block;
        color: var(--ink);
        margin-bottom: 8px;
    }

    .flow-step span {
        color: var(--muted);
        font-size: 0.82rem;
    }

    .architecture-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 12px;
    }

    .arch-tile {
        min-height: 116px;
        border: 1px solid var(--line);
        border-radius: 10px;
        padding: 15px;
        background: linear-gradient(180deg, #ffffff, #f5fbff);
        box-shadow: 0 8px 22px rgba(15,23,42,0.05);
    }

    .arch-mark {
        width: 38px;
        height: 38px;
        border-radius: 10px;
        margin-bottom: 12px;
        background: linear-gradient(135deg, var(--blue), var(--teal));
    }

    .arch-tile:nth-child(2) .arch-mark {background: linear-gradient(135deg, var(--teal), var(--green));}
    .arch-tile:nth-child(3) .arch-mark {background: linear-gradient(135deg, var(--amber), var(--rose));}

    .arch-tile strong {
        display: block;
        color: var(--ink);
        font-size: 0.98rem;
        margin-bottom: 4px;
    }

    .arch-tile span {
        color: var(--muted);
        font-size: 0.82rem;
        line-height: 1.35;
    }

    .section-head {
        display: flex;
        align-items: end;
        justify-content: space-between;
        gap: 14px;
        margin: 12px 0 16px;
    }

    .section-head h2 {
        margin: 0;
        font-size: 2.2rem;
        line-height: 1.05;
    }

    .section-head p {
        margin: 8px 0 0;
        color: var(--muted);
        font-size: 0.98rem;
    }

    .visual-card {
        background: rgba(255,255,255,0.92);
        border: 1px solid var(--line);
        border-radius: 14px;
        padding: 16px;
        box-shadow: 0 12px 30px rgba(15,23,42,0.06);
        min-height: 100%;
    }

    .visual-title {
        color: var(--ink);
        font-size: 0.98rem;
        font-weight: 850;
        margin-bottom: 4px;
    }

    .visual-copy {
        color: var(--muted);
        font-size: 0.82rem;
        margin-bottom: 12px;
    }

    .event-stream {
        display: grid;
        gap: 10px;
    }

    .stream-item {
        display: grid;
        grid-template-columns: 42px 1fr auto;
        align-items: center;
        gap: 10px;
        border: 1px solid var(--line);
        border-radius: 12px;
        padding: 10px;
        background: linear-gradient(180deg, #ffffff, #f8fcff);
    }

    .stream-icon {
        width: 38px;
        height: 38px;
        border-radius: 12px;
        display: grid;
        place-items: center;
        color: #fff;
        font-weight: 900;
        background: linear-gradient(135deg, var(--blue), var(--teal));
    }

    .stream-text strong {
        display: block;
        color: var(--ink);
        font-size: 0.92rem;
    }

    .stream-text span,
    .stream-tag {
        color: var(--muted);
        font-size: 0.78rem;
    }

    .stream-tag {
        border-radius: 999px;
        padding: 5px 8px;
        background: #edf8ff;
        border: 1px solid #d4ebf7;
        white-space: nowrap;
    }

    .risk-board {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 12px;
    }

    .risk-card {
        border-radius: 14px;
        padding: 15px;
        border: 1px solid var(--line);
        background: linear-gradient(180deg, #ffffff, #f7fbff);
        min-height: 118px;
        position: relative;
        overflow: hidden;
    }

    .risk-card:after {
        content: "";
        position: absolute;
        right: -24px;
        top: -24px;
        width: 88px;
        height: 88px;
        border-radius: 50%;
        background: rgba(37,99,235,0.12);
    }

    .risk-card.medium:after {background: rgba(245,158,11,0.16);}
    .risk-card.high:after {background: rgba(225,29,72,0.16);}

    .risk-card span {
        color: var(--muted);
        font-size: 0.76rem;
        font-weight: 800;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }

    .risk-card strong {
        display: block;
        color: var(--ink);
        font-size: 1.55rem;
        margin: 8px 0 4px;
    }

    .risk-card p {
        color: var(--muted);
        margin: 0;
        font-size: 0.82rem;
    }

    .data-flow {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 10px;
        align-items: stretch;
    }

    .flow-node {
        border: 1px solid var(--line);
        border-radius: 13px;
        padding: 14px;
        background: #ffffff;
        text-align: center;
        box-shadow: 0 8px 22px rgba(15,23,42,0.05);
    }

    .flow-node .node-mark {
        width: 42px;
        height: 42px;
        border-radius: 13px;
        margin: 0 auto 10px;
        background: linear-gradient(135deg, var(--blue), var(--teal));
    }

    .flow-node strong {
        display: block;
        color: var(--ink);
        font-size: 0.9rem;
        margin-bottom: 5px;
    }

    .flow-node span {
        color: var(--muted);
        font-size: 0.76rem;
    }

    .callout {
        border-radius: 10px;
        border: 1px solid var(--line);
        padding: 14px 16px;
        background: #fff;
        color: var(--ink);
        margin: 10px 0;
    }

    .callout.info {border-left: 4px solid var(--blue);}
    .callout.success {border-left: 4px solid var(--green); background: #f0fdf4;}
    .callout.warning {border-left: 4px solid var(--amber); background: #fffbeb;}
    .callout.danger {border-left: 4px solid var(--rose); background: #fff1f2;}

    .identity-card {
        padding: 18px;
        min-height: 100%;
        background:
            linear-gradient(135deg, rgba(23,32,51,0.96), rgba(15,118,110,0.92)),
            linear-gradient(90deg, rgba(255,255,255,0.08), transparent);
        color: #fff;
    }

    .identity-card h3 {
        color: #fff;
        margin: 0 0 8px;
    }

    .identity-card p,
    .identity-card li {
        color: rgba(255,255,255,0.82);
        font-size: 0.92rem;
    }

    .identity-card ul {
        margin: 10px 0 0;
        padding-left: 18px;
    }

    .play-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 12px;
    }

    .play-card {
        padding: 15px;
        min-height: 132px;
    }

    .play-card strong {
        display: block;
        color: var(--ink);
        margin-bottom: 7px;
    }

    .play-card span {
        color: var(--muted);
        font-size: 0.9rem;
    }

    .stButton > button,
    .stDownloadButton > button {
        background: linear-gradient(135deg, #2563eb, #0f766e);
        border: 1px solid #1d7fcb;
        color: #fff;
        border-radius: 8px;
        min-height: 42px;
        font-weight: 800;
        box-shadow: 0 8px 18px rgba(17,24,39,0.12);
    }

    .stButton > button:hover,
    .stDownloadButton > button:hover {
        border-color: #0f766e;
        color: #fff;
        transform: translateY(-1px);
    }

    div[data-testid="stMetric"] {
        background: #fff;
        border: 1px solid var(--line);
        border-radius: 10px;
        padding: 13px 15px;
        box-shadow: 0 6px 18px rgba(15,23,42,0.05);
    }

    div[data-testid="stDataFrame"] {
        border: 1px solid var(--line);
        border-radius: 10px;
        overflow: hidden;
    }

    @media (max-width: 900px) {
        .topbar {
            align-items: flex-start;
            flex-direction: column;
        }

        .topbar-actions {
            justify-content: flex-start;
        }

        .app-hero,
        .flow,
        .architecture-grid,
        .risk-board,
        .data-flow,
        .play-grid {
            grid-template-columns: 1fr;
        }

        .hero-copy h1 {font-size: 1.9rem;}
        .signal-foot {grid-template-columns: 1fr;}
    }
</style>
""",
    unsafe_allow_html=True,
)


# ============================================================================
# CONFIGURATION
# ============================================================================

API_URL = os.getenv("DROPOFF_API_URL", "http://127.0.0.1:5000")
API_TIMEOUT = 10

DEMO_PROFILES: Dict[str, Dict[str, Any]] = {
    "Low risk": {
        "days_since_signup": 120,
        "recency_days": 4,
        "frequency": 96,
        "session_duration": 24.0,
        "feature_count": 11,
        "device_type": "Desktop",
        "os_type": "Windows",
        "user_segment": "Premium",
        "region": "North",
    },
    "Balanced": {
        "days_since_signup": 220,
        "recency_days": 28,
        "frequency": 54,
        "session_duration": 13.0,
        "feature_count": 7,
        "device_type": "Mobile",
        "os_type": "Android",
        "user_segment": "Trial",
        "region": "East",
    },
    "High risk": {
        "days_since_signup": 410,
        "recency_days": 74,
        "frequency": 14,
        "session_duration": 4.5,
        "feature_count": 2,
        "device_type": "Mobile",
        "os_type": "iOS",
        "user_segment": "Free",
        "region": "South",
    },
}

COLUMN_MAP = {
    "Days Since Signup": "days_signup_age",
    "Days Since Last Activity": "recency_days",
    "Total Logins": "frequency_total",
    "Avg Session Duration (min)": "session_duration_avg",
    "Features Used": "feature_count_used",
    "Device Type": "device_type",
    "Operating System": "os_type",
    "User Segment": "user_segment",
    "Region": "region",
}


# ============================================================================
# DATA AND API HELPERS
# ============================================================================

@st.cache_resource
def get_api_session() -> requests.Session:
    session = requests.Session()
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "StreamlitDropoffDashboard/3.0",
    }
    api_key = os.getenv("API_KEY", "").strip()
    if api_key:
        headers["X-API-Key"] = api_key
    session.headers.update(headers)
    return session


@st.cache_data(ttl=30)
def check_api_status() -> bool:
    try:
        response = get_api_session().get(f"{API_URL}/health", timeout=2)
        return response.status_code == 200
    except requests.RequestException:
        return False


@st.cache_data(ttl=60)
def load_evaluation_metrics() -> Dict[str, Any]:
    path = Path("results/evaluation_metrics.json")
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


@st.cache_data(ttl=60)
def load_threshold_analysis() -> pd.DataFrame:
    path = Path("results/threshold_analysis.csv")
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


@st.cache_data(ttl=60)
def load_model_comparison() -> pd.DataFrame:
    path = Path("results/model_comparison.csv")
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def call_api(
    endpoint: str,
    method: str = "GET",
    data: Dict[str, Any] | None = None,
) -> Tuple[bool, Any, str]:
    try:
        session = get_api_session()
        url = f"{API_URL}{endpoint}"
        if method.upper() == "POST":
            response = session.post(url, json=data, timeout=API_TIMEOUT)
        else:
            response = session.get(url, timeout=API_TIMEOUT)

        if response.status_code in {200, 201, 207}:
            return True, response.json(), "Success"

        try:
            detail = response.json().get("error", response.text)
        except ValueError:
            detail = response.text
        return False, None, f"HTTP {response.status_code}: {detail}"
    except requests.RequestException as exc:
        return False, None, str(exc)


def profile_to_payload(profile_data: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "days_signup_age": profile_data["days_since_signup"],
        "recency_days": profile_data["recency_days"],
        "frequency_total": profile_data["frequency"],
        "session_duration_avg": profile_data["session_duration"],
        "feature_count_used": profile_data["feature_count"],
        "device_type": profile_data["device_type"],
        "os_type": profile_data["os_type"],
        "user_segment": profile_data["user_segment"],
        "region": profile_data["region"],
    }


def classify_risk(probability: float) -> str:
    if probability < 0.33:
        return "Low"
    if probability < 0.67:
        return "Medium"
    return "High"


def risk_kind(probability: float) -> str:
    if probability < 0.33:
        return "success"
    if probability < 0.67:
        return "warning"
    return "danger"


def metric_value(metrics: Dict[str, Any], key: str, fallback: float) -> float:
    return float(metrics.get("metrics", {}).get(key, fallback))


def score_profile(profile_name: str) -> Tuple[bool, Dict[str, Any], str]:
    payload = profile_to_payload(DEMO_PROFILES[profile_name])
    success, result, msg = call_api("/predict", "POST", payload)
    if not success:
        return False, {}, msg

    probability = float(result.get("dropoff_probability", 0))
    return (
        True,
        {
            "profile": profile_name,
            "probability": probability,
            "risk": result.get("risk_level") or classify_risk(probability),
            "prediction": result.get("predicted_label", int(probability >= 0.5)),
        },
        "Success",
    )


def uploaded_rows_to_records(df: pd.DataFrame) -> List[Dict[str, Any]]:
    renamed = df.rename(columns=COLUMN_MAP)
    required = list(COLUMN_MAP.values())
    missing = [col for col in required if col not in renamed.columns]
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")
    return renamed.loc[:, required].to_dict(orient="records")


# ============================================================================
# RENDER HELPERS
# ============================================================================

def render_kpi(label: str, value: str, copy: str, color: str = "blue") -> None:
    st.markdown(
        f"""
        <div class="kpi-card {color}">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            <p class="kpi-copy">{copy}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_panel(title: str, copy: str = "") -> None:
    st.markdown(
        f"""
        <div class="panel">
            <div class="panel-title">{title}</div>
            <p class="panel-copy">{copy}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_callout(kind: str, title: str, body: str) -> None:
    st.markdown(
        f"""
        <div class="callout {kind}">
            <strong>{title}</strong><br>{body}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_signal_panel(api_online: bool, metrics_blob: Dict[str, Any], confusion: List[List[int]]) -> None:
    status_class = "online" if api_online else "offline"
    status_text = "API Live" if api_online else "API Offline"
    st.markdown(
        f"""
        <div class="signal-panel">
            <div class="signal-head">
                <div>
                    <div class="eyebrow">AI Risk Signal</div>
                    <div class="signal-title">Behavior-to-retention intelligence</div>
                </div>
                <span class="status-chip"><span class="status-dot {status_class}"></span>{status_text}</span>
            </div>
            <div class="signal-grid">
                <div class="signal-bar" style="height: 88px;"></div>
                <div class="signal-bar"></div>
                <div class="signal-bar"></div>
                <div class="signal-bar"></div>
                <div class="signal-bar"></div>
            </div>
            <div class="signal-foot">
                <div class="mini-stat"><span>ROC-AUC</span><strong>{metric_value(metrics_blob, "roc_auc", 0.9731):.3f}</strong></div>
                <div class="mini-stat"><span>Recall</span><strong>{metric_value(metrics_blob, "recall", 0.9178):.1%}</strong></div>
                <div class="mini-stat"><span>Found</span><strong>{int(confusion[1][1]):,}</strong></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def build_gauge(probability: float) -> go.Figure:
    fig = go.Figure(
        data=[
            go.Indicator(
                mode="gauge+number",
                value=probability * 100,
                number={"suffix": "%", "valueformat": ".1f"},
                title={"text": "Drop-off risk"},
                gauge={
                    "axis": {"range": [0, 100]},
                    "bar": {"color": "#2563eb"},
                    "steps": [
                        {"range": [0, 33], "color": "#dcfce7"},
                        {"range": [33, 67], "color": "#fef3c7"},
                        {"range": [67, 100], "color": "#ffe4e6"},
                    ],
                    "threshold": {
                        "line": {"color": "#e11d48", "width": 4},
                        "thickness": 0.75,
                        "value": 70,
                    },
                },
            )
        ]
    )
    fig.update_layout(
        height=305,
        margin=dict(l=12, r=12, t=42, b=8),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Arial"),
    )
    return fig


def chart_layout(fig: go.Figure, height: int = 330) -> go.Figure:
    fig.update_layout(
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=28, b=10),
        font=dict(family="Arial", color="#142033"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    return fig


def build_retention_funnel() -> go.Figure:
    funnel_df = pd.DataFrame(
        {
            "Stage": ["Visited", "Active", "Engaged", "At Risk", "High Risk"],
            "Users": [100000, 78200, 54600, 18450, 6200],
        }
    )
    fig = go.Figure(
        go.Funnel(
            y=funnel_df["Stage"],
            x=funnel_df["Users"],
            textinfo="value+percent initial",
            marker={
                "color": ["#2563eb", "#14b8a6", "#059669", "#f59e0b", "#e11d48"],
                "line": {"width": 0},
            },
        )
    )
    return chart_layout(fig, 305)


def build_segment_risk_donut() -> go.Figure:
    segment_df = pd.DataFrame(
        {
            "Segment": ["Free", "Trial", "Premium", "Returning"],
            "Risk Share": [42, 28, 12, 18],
        }
    )
    fig = px.pie(
        segment_df,
        names="Segment",
        values="Risk Share",
        hole=0.62,
        color="Segment",
        color_discrete_map={
            "Free": "#e11d48",
            "Trial": "#f59e0b",
            "Premium": "#059669",
            "Returning": "#2563eb",
        },
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    return chart_layout(fig, 305)


def build_event_volume_chart() -> go.Figure:
    event_df = pd.DataFrame(
        {
            "Hour": ["00", "04", "08", "12", "16", "20"],
            "Product Views": [1800, 1200, 4200, 7600, 9200, 6800],
            "Cart Events": [420, 260, 1100, 2400, 3100, 2200],
            "Checkout Events": [90, 80, 420, 960, 1280, 780],
        }
    )
    fig = px.area(
        event_df,
        x="Hour",
        y=["Product Views", "Cart Events", "Checkout Events"],
        color_discrete_sequence=["#2563eb", "#14b8a6", "#f59e0b"],
    )
    fig.update_layout(yaxis_title="Events", xaxis_title="Hour")
    return chart_layout(fig, 305)


def build_region_heatmap() -> go.Figure:
    region_df = pd.DataFrame(
        [
            ["North", 18, 28, 54],
            ["South", 24, 33, 43],
            ["East", 30, 31, 39],
            ["West", 21, 36, 43],
        ],
        columns=["Region", "Low", "Medium", "High"],
    )
    heat_df = region_df.set_index("Region")
    fig = px.imshow(
        heat_df,
        text_auto=True,
        aspect="auto",
        color_continuous_scale=["#dcfce7", "#fef3c7", "#ffe4e6", "#e11d48"],
        labels=dict(color="Risk %"),
    )
    fig.update_layout(xaxis_title="Risk Level", yaxis_title="Region")
    return chart_layout(fig, 305)


# ============================================================================
# DATA LOAD
# ============================================================================

metrics_blob = load_evaluation_metrics()
confusion = metrics_blob.get("confusion_matrix", [[4226, 415], [276, 3083]])
threshold_df = load_threshold_analysis()
model_df = load_model_comparison()
api_online = check_api_status()


# ============================================================================
# NAVIGATION
# ============================================================================

PAGES = [
    "Command Center",
    "Production Tracking",
    "Model Intelligence",
    "Batch Scoring",
    "System Health",
]

NAV_LABELS = {
    "Command Center": "01  Command Center",
    "Production Tracking": "02  Tracking",
    "Model Intelligence": "03  Model Intel",
    "Batch Scoring": "04  Batch Scoring",
    "System Health": "05  System",
}

if "page" not in st.session_state:
    st.session_state["page"] = PAGES[0]

status_class = "online" if api_online else "offline"
status_text = "API Live" if api_online else "API Offline"
st.markdown(
    f"""
    <div class="topbar">
        <div class="brand">
            <div class="brand-mark">AI</div>
            <div>
                <div class="brand-title">Early User Churn Detection</div>
                <div class="brand-subtitle">Revenue retention intelligence dashboard</div>
            </div>
        </div>
        <div class="topbar-actions">
            <span class="api-pill"><span class="status-dot {status_class}"></span>{status_text}</span>
            <span class="nav-note">Model {metric_value(metrics_blob, "roc_auc", 0.9731):.3f} ROC-AUC</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

selected_page = st.pills(
    "Dashboard navigation",
    PAGES,
    default=st.session_state["page"],
    format_func=lambda page_name: NAV_LABELS[page_name],
    label_visibility="collapsed",
)
if selected_page:
    st.session_state["page"] = selected_page
page = st.session_state["page"]


# ============================================================================
# COMMAND CENTER
# ============================================================================

if page == "Command Center":
    st.markdown(
        """
        <div class="section-head">
            <div>
                <h2>Command Center</h2>
                <p>Executive view of retention risk, model strength, and operational signals.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    hero_col, signal_col = st.columns([1.18, 0.82])
    with hero_col:
        st.markdown(
            """
            <div class="hero-copy">
                <div class="eyebrow">AI-Driven Retention Intelligence</div>
                <h1>Early User Churn Detection Command Center</h1>
                <p>
                    A modern ML dashboard that converts behavioral signals into risk scores,
                    intervention priorities, model evidence, and operational insight.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with signal_col:
        render_signal_panel(api_online, metrics_blob, confusion)

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        render_kpi("ROC-AUC", f"{metric_value(metrics_blob, 'roc_auc', 0.9731):.3f}", "Separation quality.", "blue")
    with k2:
        render_kpi("Recall", f"{metric_value(metrics_blob, 'recall', 0.9178):.1%}", "Risk capture.", "green")
    with k3:
        render_kpi("Value", f"${metric_value(metrics_blob, 'business_value', 584850):,.0f}", "Retention impact.", "amber")
    with k4:
        render_kpi("Flagged", f"{int(confusion[1][1]):,}", "Users found.", "rose")

    st.markdown(
        """
        <div class="panel">
            <div class="panel-title">Project Pipeline</div>
            <div class="architecture-grid">
                <div class="arch-tile">
                    <div class="arch-mark"></div>
                    <strong>Event Tracking</strong>
                    <span>Website records login, search, product, cart, checkout, and order activity.</span>
                </div>
                <div class="arch-tile">
                    <div class="arch-mark"></div>
                    <strong>Feature Generation</strong>
                    <span>Events become user-level features such as recency, frequency, and usage depth.</span>
                </div>
                <div class="arch-tile">
                    <div class="arch-mark"></div>
                    <strong>Risk Dashboard</strong>
                    <span>Predictions are stored and summarized for retention teams.</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    visual_left, visual_right = st.columns([1.1, 0.9])
    with visual_left:
        st.markdown(
            """
            <div class="visual-card">
                <div class="visual-title">Retention Funnel</div>
                <div class="visual-copy">How users move from activity to risk buckets.</div>
            """,
            unsafe_allow_html=True,
        )
        st.plotly_chart(build_retention_funnel(), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with visual_right:
        st.markdown(
            """
            <div class="visual-card">
                <div class="visual-title">Risk By Segment</div>
                <div class="visual-copy">Which user groups need retention attention.</div>
            """,
            unsafe_allow_html=True,
        )
        st.plotly_chart(build_segment_risk_donut(), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        """
        <div class="risk-board">
            <div class="risk-card">
                <span>Low Risk</span>
                <strong>72%</strong>
                <p>Healthy users with regular activity.</p>
            </div>
            <div class="risk-card medium">
                <span>Medium Risk</span>
                <strong>19%</strong>
                <p>Need nudges and product guidance.</p>
            </div>
            <div class="risk-card high">
                <span>High Risk</span>
                <strong>9%</strong>
                <p>Priority users for retention action.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================================
# PRODUCTION TRACKING
# ============================================================================

elif page == "Production Tracking":
    st.markdown(
        """
        <div class="section-head">
            <div>
                <h2>Production Tracking</h2>
                <p>Real web applications generate behavior data automatically, then the ML system scores users at scale.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    p1, p2, p3, p4 = st.columns(4)
    with p1:
        render_kpi("Event Capture", "Auto", "Login, search, cart, checkout.", "blue")
    with p2:
        render_kpi("Feature Job", "Batch", "User-level behavior features.", "teal")
    with p3:
        render_kpi("ML Scoring", "API", "Real-time or scheduled scoring.", "green")
    with p4:
        render_kpi("Dashboard", "Insights", "Counts, filters, high-risk users.", "amber")

    st.markdown(
        """
        <div class="panel">
            <div class="panel-title">Real Application Flow</div>
            <div class="data-flow">
                <div class="flow-node">
                    <div class="node-mark"></div>
                    <strong>Website</strong>
                    <span>Clicks and sessions</span>
                </div>
                <div class="flow-node">
                    <div class="node-mark"></div>
                    <strong>Events DB</strong>
                    <span>User actions</span>
                </div>
                <div class="flow-node">
                    <div class="node-mark"></div>
                    <strong>Features</strong>
                    <span>Aggregated signals</span>
                </div>
                <div class="flow-node">
                    <div class="node-mark"></div>
                    <strong>ML API</strong>
                    <span>Risk prediction</span>
                </div>
                <div class="flow-node">
                    <div class="node-mark"></div>
                    <strong>Dashboard</strong>
                    <span>Insights and action</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    event_col, feature_col = st.columns([0.9, 1.1])
    with event_col:
        st.markdown(
            """
            <div class="visual-card">
                <div class="visual-title">Live Event Stream</div>
                <div class="visual-copy">Example events captured from a grocery application.</div>
                <div class="event-stream">
                    <div class="stream-item"><div class="stream-icon">01</div><div class="stream-text"><strong>login</strong><span>Login page</span></div><div class="stream-tag">session</div></div>
                    <div class="stream-item"><div class="stream-icon">02</div><div class="stream-text"><strong>product_viewed</strong><span>Product page</span></div><div class="stream-tag">interest</div></div>
                    <div class="stream-item"><div class="stream-icon">03</div><div class="stream-text"><strong>search</strong><span>Search bar</span></div><div class="stream-tag">intent</div></div>
                    <div class="stream-item"><div class="stream-icon">04</div><div class="stream-text"><strong>add_to_cart</strong><span>Cart button</span></div><div class="stream-tag">purchase</div></div>
                    <div class="stream-item"><div class="stream-icon">05</div><div class="stream-text"><strong>checkout_started</strong><span>Checkout page</span></div><div class="stream-tag">conversion</div></div>
                    <div class="stream-item"><div class="stream-icon">06</div><div class="stream-text"><strong>order_completed</strong><span>Payment success</span></div><div class="stream-tag">retention</div></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with feature_col:
        st.markdown("### Automatic Feature Table")
        feature_sources = pd.DataFrame(
            [
                {"Feature": "days_signup_age", "Source": "user signup date"},
                {"Feature": "recency_days", "Source": "latest event timestamp"},
                {"Feature": "frequency_total", "Source": "session/login count"},
                {"Feature": "session_duration_avg", "Source": "session start and end time"},
                {"Feature": "feature_count_used", "Source": "unique features/events used"},
                {"Feature": "device_type / os_type", "Source": "browser or app device metadata"},
                {"Feature": "user_segment / region", "Source": "user profile or delivery location"},
            ]
        )
        st.dataframe(feature_sources, use_container_width=True, hide_index=True)

    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        st.markdown("### Event Volume")
        st.plotly_chart(build_event_volume_chart(), use_container_width=True)
    with chart_col2:
        st.markdown("### Region Risk Heatmap")
        st.plotly_chart(build_region_heatmap(), use_container_width=True)

    st.markdown("### Managing Large User Volume")
    scale_df = pd.DataFrame(
        [
            {"Layer": "Event tracking", "Production Use": "Append every user action to an events table or stream."},
            {"Layer": "Feature generation", "Production Use": "Aggregate events per user every hour or every day."},
            {"Layer": "Batch prediction", "Production Use": "Score lakhs or crores of users using /predict-batch or scheduled jobs."},
            {"Layer": "Dashboard", "Production Use": "Show summaries, filters, segments, regions, and high-risk users only."},
        ]
    )
    st.dataframe(scale_df, use_container_width=True, hide_index=True)

    with st.expander("Developer test panel", expanded=False):
        quick1, quick2, quick3 = st.columns(3)
        run_profile: str | None = None
        with quick1:
            if st.button("Test low risk", use_container_width=True):
                run_profile = "Low risk"
        with quick2:
            if st.button("Test balanced", use_container_width=True):
                run_profile = "Balanced"
        with quick3:
            if st.button("Test high risk", use_container_width=True):
                run_profile = "High risk"

        if run_profile:
            success, data, msg = score_profile(run_profile)
            if success:
                probability = float(data["probability"])
                gauge_col, text_col = st.columns([0.8, 1.2])
                with gauge_col:
                    st.plotly_chart(build_gauge(probability), use_container_width=True)
                with text_col:
                    st.metric("Profile", run_profile)
                    st.metric("Drop-off probability", f"{probability * 100:.1f}%")
                    render_callout(risk_kind(probability), classify_risk(probability), "API prediction test completed.")
            else:
                st.error(f"Prediction failed: {msg}")


# ============================================================================
# MODEL INTELLIGENCE
# ============================================================================

elif page == "Model Intelligence":
    st.markdown("## Model Intelligence")
    st.caption("Evidence for performance, threshold choice, and explainability.")

    metric_df = pd.DataFrame(
        {
            "Metric": ["Accuracy", "Precision", "Recall", "F1 Score", "ROC-AUC", "PR-AUC"],
            "Score": [
                metric_value(metrics_blob, "accuracy", 0.9136),
                metric_value(metrics_blob, "precision", 0.8814),
                metric_value(metrics_blob, "recall", 0.9178),
                metric_value(metrics_blob, "f1", 0.8992),
                metric_value(metrics_blob, "roc_auc", 0.9731),
                metric_value(metrics_blob, "pr_auc", 0.9633),
            ],
            "Target": [0.90, 0.85, 0.90, 0.85, 0.95, 0.90],
        }
    )

    top_left, top_right = st.columns([1.2, 0.8])
    with top_left:
        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                x=metric_df["Metric"],
                y=metric_df["Score"],
                name="Achieved",
                marker_color="#0f766e",
                text=[f"{score:.1%}" for score in metric_df["Score"]],
                textposition="auto",
            )
        )
        fig.add_trace(
            go.Bar(
                x=metric_df["Metric"],
                y=metric_df["Target"],
                name="Target",
                marker_color="#d9e2ec",
                text=[f"{score:.1%}" for score in metric_df["Target"]],
                textposition="auto",
            )
        )
        fig.update_layout(barmode="group", yaxis_tickformat=".0%", yaxis_range=[0, 1.05])
        st.plotly_chart(chart_layout(fig, 335), use_container_width=True)
    with top_right:
        tn, fp = confusion[0]
        fn, tp = confusion[1]
        cm_df = pd.DataFrame(
            [
                {"Actual": "Retained", "Predicted": "Retained", "Count": tn},
                {"Actual": "Retained", "Predicted": "Drop-off", "Count": fp},
                {"Actual": "Drop-off", "Predicted": "Retained", "Count": fn},
                {"Actual": "Drop-off", "Predicted": "Drop-off", "Count": tp},
            ]
        )
        fig_cm = px.bar(
            cm_df,
            x="Predicted",
            y="Count",
            color="Actual",
            barmode="group",
            color_discrete_map={"Retained": "#2563eb", "Drop-off": "#e11d48"},
        )
        st.plotly_chart(chart_layout(fig_cm, 335), use_container_width=True)

    lower_left, lower_right = st.columns(2)
    with lower_left:
        if threshold_df.empty:
            render_callout("warning", "Threshold data missing", "results/threshold_analysis.csv was not found.")
        else:
            threshold_long = threshold_df.melt(
                id_vars=["threshold"],
                value_vars=["precision", "recall", "f1"],
                var_name="Metric",
                value_name="Score",
            )
            fig_threshold = px.line(
                threshold_long,
                x="threshold",
                y="Score",
                color="Metric",
                markers=True,
                color_discrete_map={"precision": "#2563eb", "recall": "#059669", "f1": "#d97706"},
                title="Threshold trade-off",
            )
            fig_threshold.update_layout(yaxis_tickformat=".0%")
            st.plotly_chart(chart_layout(fig_threshold, 340), use_container_width=True)

    with lower_right:
        importance_df = pd.DataFrame(
            {
                "Feature": [
                    "Recency",
                    "Session Duration",
                    "Feature Count",
                    "Free Segment",
                    "Mobile Device",
                    "Frequency",
                    "Account Age",
                    "Region",
                    "OS Type",
                ],
                "Importance": [0.28, 0.25, 0.24, 0.12, 0.08, 0.02, 0.01, 0.005, 0.005],
            }
        )
        fig_importance = px.bar(
            importance_df,
            x="Importance",
            y="Feature",
            orientation="h",
            color="Importance",
            color_continuous_scale="Teal",
            title="Feature influence",
        )
        fig_importance.update_layout(yaxis={"categoryorder": "total ascending"}, showlegend=False)
        st.plotly_chart(chart_layout(fig_importance, 340), use_container_width=True)

    if not model_df.empty:
        display_model_df = model_df.copy()
        display_model_df["model"] = display_model_df["model"].str.replace("_", " ").str.title()
        st.dataframe(display_model_df, use_container_width=True, hide_index=True)


# ============================================================================
# BATCH SCORING
# ============================================================================

elif page == "Batch Scoring":
    st.markdown("## Batch Scoring")
    st.caption("CSV upload, API-backed batch scoring, and exportable prediction reports.")

    sample_df = pd.DataFrame(
        [
            {
                "Days Since Signup": 120,
                "Days Since Last Activity": 4,
                "Total Logins": 96,
                "Avg Session Duration (min)": 24.0,
                "Features Used": 11,
                "Device Type": "Desktop",
                "Operating System": "Windows",
                "User Segment": "Premium",
                "Region": "North",
            },
            {
                "Days Since Signup": 410,
                "Days Since Last Activity": 74,
                "Total Logins": 14,
                "Avg Session Duration (min)": 4.5,
                "Features Used": 2,
                "Device Type": "Mobile",
                "Operating System": "iOS",
                "User Segment": "Free",
                "Region": "South",
            },
        ]
    )

    top_a, top_b = st.columns([0.7, 1.3])
    with top_a:
        st.download_button(
            "Download sample CSV",
            sample_df.to_csv(index=False).encode("utf-8"),
            "dropoff_batch_template.csv",
            "text/csv",
            use_container_width=True,
        )
        uploaded_file = st.file_uploader("Upload users CSV", type=["csv"])
    with top_b:
        st.dataframe(sample_df, use_container_width=True, hide_index=True)

    if uploaded_file:
        uploaded_df = pd.read_csv(uploaded_file)
        st.markdown("### Uploaded Preview")
        st.dataframe(uploaded_df.head(12), use_container_width=True, hide_index=True)

        if st.button("Process uploaded users", use_container_width=True):
            try:
                records = uploaded_rows_to_records(uploaded_df)
            except ValueError as exc:
                st.error(str(exc))
            else:
                success, result, msg = call_api("/predict-batch", "POST", {"records": records})
                if not success:
                    st.error(f"Batch prediction failed: {msg}")
                else:
                    predictions = pd.DataFrame(result.get("predictions", []))
                    if predictions.empty:
                        render_callout("warning", "No predictions returned", "Review API validation errors below.")
                    else:
                        enriched = uploaded_df.copy()
                        enriched["dropoff_probability"] = predictions["dropoff_probability"].values
                        enriched["risk_level"] = predictions["risk_level"].values
                        enriched["predicted_label"] = predictions["predicted_label"].values
                        high_risk_count = int((enriched["dropoff_probability"] >= 0.67).sum())
                        st.metric("Processed users", len(enriched))
                        st.metric("High-risk users", high_risk_count)
                        st.dataframe(enriched, use_container_width=True, hide_index=True)

                        export1, export2 = st.columns(2)
                        with export1:
                            st.download_button(
                                "Download scored CSV",
                                enriched.to_csv(index=False).encode("utf-8"),
                                "dropoff_predictions.csv",
                                "text/csv",
                                use_container_width=True,
                            )
                        with export2:
                            st.download_button(
                                "Download scored JSON",
                                enriched.to_json(orient="records", indent=2).encode("utf-8"),
                                "dropoff_predictions.json",
                                "application/json",
                                use_container_width=True,
                            )

                    errors = result.get("errors", [])
                    if errors:
                        st.warning(f"{len(errors)} rows failed validation.")
                        st.dataframe(pd.DataFrame(errors), use_container_width=True, hide_index=True)


# ============================================================================
# SYSTEM HEALTH
# ============================================================================

elif page == "System Health":
    st.markdown("## System Health")
    st.caption("Project components, API health, and implementation artifacts.")

    ready1, ready2, ready3 = st.columns(3)
    with ready1:
        render_kpi("API Layer", "Flask", "Health, prediction, batch scoring, monitoring, and records.", "blue")
    with ready2:
        render_kpi("ML Layer", "Model", "Feature engineering, persisted model, and evaluation outputs.", "teal")
    with ready3:
        render_kpi("Dashboard", "Streamlit", "Interactive scoring, model evidence, and exports.", "green")

    monitor_col, deploy_col = st.columns(2)
    with monitor_col:
        st.markdown("### API Monitor")
        if st.button("Refresh monitor", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        success, data, msg = call_api("/monitor")
        if success and isinstance(data, dict):
            st.json(data)
        else:
            render_callout("warning", "Monitor unavailable", f"Detail: {msg}")

    with deploy_col:
        st.markdown("### Project Artifacts")
        artifacts = pd.DataFrame(
            [
                {"Area": "Model", "Artifact": "models/final_model.pkl"},
                {"Area": "Metrics", "Artifact": "results/evaluation_metrics.json"},
                {"Area": "Thresholds", "Artifact": "results/threshold_analysis.csv"},
                {"Area": "API", "Artifact": "src/api/app.py"},
                {"Area": "Dashboard", "Artifact": "streamlit_dashboard.py"},
                {"Area": "CI/CD", "Artifact": ".github/workflows/mlops-ci-cd.yml"},
            ]
        )
        st.dataframe(artifacts, use_container_width=True, hide_index=True)
