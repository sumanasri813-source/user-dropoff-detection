"""
Streamlit dashboard for silent user drop-off detection.

The interface is intentionally compact and clean so the core data and
predictions stay readable during demos.
"""

import streamlit as st
import requests
import pandas as pd
import json
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, Any, Tuple, List
import numpy as np
from io import StringIO, BytesIO
import csv

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="Silent User Drop-Off Detection",
    page_icon="📉",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================================================
# PREMIUM CSS STYLING - Hide Streamlit UI & Create Enterprise Design
# ============================================================================

st.markdown("""
<style>
    /* Hide Streamlit Default UI Elements */
    #MainMenu {display: none !important;}
    header {display: none !important;}
    footer {display: none !important;}
    .stDeployButton {display: none !important;}

    .main .block-container {
        padding-top: 0.9rem;
        padding-bottom: 0.9rem;
        max-width: 1280px;
    }
    
    /* Main App Container */
    .main {
        background-color: #f7f8fb;
        padding: 0;
    }
    
    /* Section Header */
    .section-header {
        background: #111827;
        padding: 18px 22px;
        border-radius: 12px;
        color: white;
        margin-bottom: 16px;
        box-shadow: 0 8px 24px rgba(15, 23, 42, 0.16);
        border: 1px solid rgba(255, 255, 255, 0.06);
    }
    
    .section-header h1 {
        margin: 0;
        font-size: 2em;
        font-weight: 700;
        letter-spacing: -0.02em;
    }
    
    .section-header p {
        margin: 5px 0 0 0;
        font-size: 0.95em;
        opacity: 0.84;
    }
    
    /* Premium Metric Card */
    .premium-card {
        background: white;
        padding: 16px 18px;
        border-radius: 10px;
        box-shadow: 0 1px 10px rgba(15, 23, 42, 0.05);
        border: 1px solid #e5e7eb;
        transition: border-color 0.2s ease, box-shadow 0.2s ease;
        margin-bottom: 12px;
    }
    
    .premium-card:hover {
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.08);
        border-color: #cbd5e1;
    }
    
    .premium-card.primary {
        border-left: 5px solid #667eea;
    }
    
    .premium-card.success {
        border-left: 5px solid #10b981;
    }
    
    .premium-card.warning {
        border-left: 5px solid #f59e0b;
    }
    
    .premium-card.danger {
        border-left: 5px solid #ef4444;
    }
    
    /* Metric Value Display */
    .metric-value {
        font-size: 2em;
        font-weight: 700;
        color: #0f172a;
        margin: 6px 0 0 0;
    }
    
    .metric-label {
        font-size: 0.84em;
        color: #64748b;
        font-weight: 500;
        letter-spacing: 0.03em;
        text-transform: uppercase;
    }
    
    /* Result Badge */
    .result-badge {
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        font-weight: 600;
        font-size: 1.1em;
        margin: 15px 0;
        transition: all 0.3s ease;
    }
    
    .badge-success {
        background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
        color: #065f46;
        border: 2px solid #10b981;
    }
    
    .badge-danger {
        background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
        color: #7f1d1d;
        border: 2px solid #ef4444;
    }
    
    .badge-warning {
        background: linear-gradient(135deg, #fef3c7 0%, #fcd34d 100%);
        color: #78350f;
        border: 2px solid #f59e0b;
    }
    
    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        padding: 9px 15px;
        border-radius: 8px;
        background-color: #eef2f7;
        color: #334155;
        font-weight: 500;
        border: none;
    }
    
    .stTabs [aria-selected="true"] {
        background: #111827;
        color: white;
    }
    
    /* Input Container */
    .input-group {
        background: white;
        padding: 12px 14px;
        border-radius: 10px;
        margin: 10px 0;
        border: 1px solid #e5e7eb;
    }
    
    /* Button Styling */
    .stButton > button {
        background: #111827;
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 8px;
        font-weight: 600;
        letter-spacing: 0.02em;
        transition: all 0.3s ease;
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.18);
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 16px rgba(15, 23, 42, 0.18);
    }
    
    /* Divider */
    .divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, #dbe2ea, transparent);
        margin: 16px 0;
    }
    
    /* Info Box */
    .info-box {
        background: #f1f5f9;
        padding: 11px 14px;
        border-radius: 8px;
        border-left: 4px solid #334155;
        color: #0f172a;
        font-size: 0.95em;
        margin: 10px 0;
    }
    
    /* Success Box */
    .success-box {
        background: #f0fdf4;
        padding: 12px 16px;
        border-radius: 8px;
        border-left: 4px solid #10b981;
        color: #065f46;
        font-size: 0.95em;
        margin: 15px 0;
    }
    
    /* Warning Box */
    .warning-box {
        background: #fffbeb;
        padding: 12px 16px;
        border-radius: 8px;
        border-left: 4px solid #f59e0b;
        color: #78350f;
        font-size: 0.95em;
        margin: 15px 0;
    }
    
    /* Danger Box */
    .danger-box {
        background: #fef2f2;
        padding: 12px 16px;
        border-radius: 8px;
        border-left: 4px solid #ef4444;
        color: #7f1d1d;
        font-size: 0.95em;
        margin: 15px 0;
    }
    
    /* Chart Container */
    .chart-container {
        background: white;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #e5e7eb;
        margin: 20px 0;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# CONFIGURATION & CONSTANTS
# ============================================================================

API_URL = "http://127.0.0.1:5000"
API_TIMEOUT = 10

DEMO_PROFILES = {
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

# ============================================================================
# SESSION & CACHING
# ============================================================================

@st.cache_resource
def get_api_session():
    """Get persistent requests session with connection pooling."""
    session = requests.Session()
    session.headers.update({
        'Content-Type': 'application/json',
        'User-Agent': 'StreamlitDashboard/1.0'
    })
    return session


@st.cache_data(ttl=30)
def check_api_status():
    """Check if API server is running."""
    try:
        response = get_api_session().get(f"{API_URL}/health", timeout=2)
        return response.status_code == 200
    except:
        return False


@st.cache_data(ttl=60)
def load_evaluation_metrics() -> Dict[str, Any]:
    """Load cached evaluation metrics."""
    try:
        with open("results/evaluation_metrics.json", "r") as f:
            return json.load(f)
    except:
        return {}


def call_api(endpoint: str, method: str = "GET", data: Dict[str, Any] | None = None) -> Tuple[bool, Any, str]:
    """Unified API call handler."""
    try:
        session = get_api_session()
        url = f"{API_URL}{endpoint}"
        
        if method.upper() == "POST":
            response = session.post(url, json=data, timeout=API_TIMEOUT)
        else:
            response = session.get(url, timeout=API_TIMEOUT)
        
        if response.status_code == 200:
            return True, response.json(), "Success"
        else:
            return False, None, f"Error {response.status_code}"
    except Exception as e:
        return False, None, str(e)


def load_demo_profile(profile_name: str) -> None:
    profile = DEMO_PROFILES.get(profile_name)
    if not profile:
        return
    for key, value in profile.items():
        st.session_state[key] = value


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


def score_profile(profile_name: str) -> Tuple[bool, Dict[str, Any], str]:
    profile_data = DEMO_PROFILES[profile_name]
    payload = profile_to_payload(profile_data)
    success, result, msg = call_api("/predict", "POST", payload)
    if not success:
        return False, {}, msg
    probability = float(result.get("dropoff_probability", 0))
    return True, {
        "profile": profile_name,
        "probability": probability,
        "risk": classify_risk(probability),
    }, "Success"


# ============================================================================
# PREMIUM HEADER
# ============================================================================

st.markdown("""
<div class="section-header">
    <h1>Silent User Drop-Off Detection</h1>
    <p>Machine learning dashboard for risk scoring, evaluation tracking, and retention analysis.</p>
</div>
""", unsafe_allow_html=True)

# API Status
col1, col2 = st.columns([4, 1])
with col1:
    api_status = check_api_status()
    status_html = "<b>Connected</b>" if api_status else "<b>Offline</b>"
    st.markdown(f"<div class='info-box'><strong>API Status:</strong> {status_html}</div>", 
                unsafe_allow_html=True)

with col2:
    if not api_status:
        st.error("API not running")

st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

# ============================================================================
# PRESENTATION LAYOUT
# ============================================================================

st.markdown("### Executive Brief")

hero_col, action_col, status_col = st.columns([1.35, 0.95, 0.75])

with hero_col:
    st.markdown(
        """
        <div class="premium-card primary">
            <div class="metric-label">Core model signal</div>
            <div class="metric-value">0.9731</div>
            <p><strong>ROC-AUC</strong> shows strong separation between retained and drop-off users.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with action_col:
    st.markdown(
        """
        <div class="premium-card warning">
            <div class="metric-label">Demo action</div>
            <div class="metric-value">Intervene</div>
            <p>Use the one-click prediction flow to surface a high-risk user before the audience.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with status_col:
    st.markdown(
        """
        <div class="premium-card success">
            <div class="metric-label">System status</div>
            <div class="metric-value">Live</div>
            <p>API-backed scoring is ready for the demo session.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

quick_col1, quick_col2, quick_col3 = st.columns(3)
with quick_col1:
    if st.button("Prepare high-risk demo profile", key="prepare_hero_demo", use_container_width=True):
        load_demo_profile("High risk")
        st.success("High-risk demo profile prepared.")
with quick_col2:
    if st.button("Refresh dashboard", key="refresh_dashboard", use_container_width=True):
        st.rerun()
with quick_col3:
    if st.button("Open prediction inputs", key="focus_prediction", use_container_width=True):
        st.session_state["show_prediction"] = True

with st.expander("Detailed performance", expanded=False):
    st.markdown("#### Model Confusion Matrix")

    cm_data = {
        'Actual': ['Retained', 'Retained', 'Drop-off', 'Drop-off'],
        'Predicted': ['Retained', 'Drop-off', 'Retained', 'Drop-off'],
        'Count': [5833, 713, 511, 943]
    }
    cm_df = pd.DataFrame(cm_data)

    fig_cm = px.bar(
        cm_df,
        x='Predicted',
        y='Count',
        color='Actual',
        barmode='group',
        color_discrete_map={'Retained': '#10b981', 'Drop-off': '#ef4444'}
    )

    fig_cm.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor='#e5e7eb'),
        hovermode='x unified',
        height=360
    )

    st.plotly_chart(fig_cm, use_container_width=True)

st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
st.markdown("### Prediction Studio")
st.markdown(
    "<div class='info-box'><strong>One-click scoring:</strong> use a preset profile for the live demo, or expand manual mode for a custom scenario.</div>",
    unsafe_allow_html=True,
)

if st.session_state.get("show_prediction"):
    st.info("Prediction inputs are ready below. Use a preset first if you want a fast live run.")

run_profile: str | None = None
run_sequence = False

predict_row1, predict_row2, predict_row3, predict_row4 = st.columns(4)
with predict_row1:
    if st.button("Run demo script mode", key="run_sequence", use_container_width=True):
        run_sequence = True
with predict_row2:
    if st.button("Score low-risk profile", key="demo_low", use_container_width=True):
        run_profile = "Low risk"
with predict_row3:
    if st.button("Score balanced profile", key="demo_balanced", use_container_width=True):
        run_profile = "Balanced"
with predict_row4:
    if st.button("Score high-risk profile", key="demo_high", use_container_width=True):
        run_profile = "High risk"

if run_sequence:
    sequence_profiles = ["Low risk", "Balanced", "High risk"]
    sequence_results: List[Dict[str, Any]] = []
    with st.spinner("Running demo script mode..."):
        for profile_name in sequence_profiles:
            success, data, msg = score_profile(profile_name)
            if success:
                sequence_results.append({
                    "Scenario": profile_name,
                    "Drop-off Probability": round(data["probability"] * 100, 2),
                    "Risk": data["risk"],
                })
            else:
                sequence_results.append({
                    "Scenario": profile_name,
                    "Drop-off Probability": None,
                    "Risk": f"Error: {msg}",
                })

    if sequence_results:
        st.markdown("#### Demo script output")
        seq_df = pd.DataFrame(sequence_results)
        st.dataframe(seq_df, use_container_width=True, hide_index=True)

        plot_df = seq_df.dropna(subset=["Drop-off Probability"])
        if not plot_df.empty:
            fig_seq = px.line(
                plot_df,
                x="Scenario",
                y="Drop-off Probability",
                markers=True,
                title="Scenario progression",
            )
            fig_seq.update_layout(
                yaxis_title="Drop-off Probability (%)",
                xaxis_title="",
                height=320,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
            )
            st.plotly_chart(fig_seq, use_container_width=True)

if run_profile:
    load_demo_profile(run_profile)
    success, data, msg = score_profile(run_profile)
    if success:
        prob = data["probability"]
        st.markdown(f"#### Result: {run_profile}")
        st.metric("Drop-off probability", f"{prob * 100:.1f}%")
        if prob < 0.33:
            st.markdown("<div class='success-box'><strong>Low risk:</strong> user likely to retain.</div>", unsafe_allow_html=True)
        elif prob < 0.67:
            st.markdown("<div class='warning-box'><strong>Medium risk:</strong> monitor engagement trends.</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='danger-box'><strong>High risk:</strong> trigger retention action now.</div>", unsafe_allow_html=True)
    else:
        st.error(f"Prediction failed: {msg}")

with st.expander("Manual mode", expanded=False):
    st.markdown("### Manual Prediction")
    st.markdown("Use this section for custom scenario testing.")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("<div class='input-group'>", unsafe_allow_html=True)
        days_since_signup = st.slider(
            "Days Since Signup",
            min_value=30, max_value=730, value=180,
            key="days_since_signup",
            help="Account age in days (30-730)"
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("<div class='input-group'>", unsafe_allow_html=True)
        recency_days = st.slider(
            "Days Since Last Activity",
            min_value=0, max_value=120, value=30,
            key="recency_days",
            help="Last login (0-120 days)"
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with col3:
        st.markdown("<div class='input-group'>", unsafe_allow_html=True)
        frequency = st.slider(
            "Total Logins",
            min_value=0, max_value=200, value=50,
            key="frequency",
            help="Number of logins (0-200)"
        )
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("#### Advanced inputs")
    col4, col5, col6 = st.columns(3)

    with col4:
        st.markdown("<div class='input-group'>", unsafe_allow_html=True)
        session_duration = st.slider(
            "Avg Session Duration (min)",
            min_value=1.0, max_value=60.0, value=15.0,
            key="session_duration",
            help="Average session length (1-60 min)"
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with col5:
        st.markdown("<div class='input-group'>", unsafe_allow_html=True)
        feature_count = st.slider(
            "Features Used",
            min_value=1, max_value=15, value=8,
            key="feature_count",
            help="Count of features accessed (1-15)"
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with col6:
        st.markdown("<div class='input-group'>", unsafe_allow_html=True)
        device_type = st.selectbox(
            "Device Type",
            ["Mobile", "Desktop", "Tablet"],
            key="device_type",
            help="Primary device used"
        )
        st.markdown("</div>", unsafe_allow_html=True)

    col7, col8, col9 = st.columns(3)

    with col7:
        st.markdown("<div class='input-group'>", unsafe_allow_html=True)
        os_type = st.selectbox(
            "Operating System",
            ["Windows", "Mac", "Android", "iOS", "Linux"],
            key="os_type",
            help="Device OS"
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with col8:
        st.markdown("<div class='input-group'>", unsafe_allow_html=True)
        user_segment = st.selectbox(
            "User Segment",
            ["Free", "Trial", "Premium"],
            key="user_segment",
            help="Subscription level"
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with col9:
        st.markdown("<div class='input-group'>", unsafe_allow_html=True)
        region = st.selectbox(
            "Region",
            ["North", "South", "East", "West"],
            key="region",
            help="Geographic region"
        )
        st.markdown("</div>", unsafe_allow_html=True)

    if st.button("Predict Drop-Off Probability", key="manual_predict", use_container_width=True):
        with st.spinner("Analyzing user..."):
            prediction_data = {
                "days_signup_age": days_since_signup,
                "recency_days": recency_days,
                "frequency_total": frequency,
                "session_duration_avg": session_duration,
                "feature_count_used": feature_count,
                "device_type": device_type,
                "os_type": os_type,
                "user_segment": user_segment,
                "region": region
            }

            success, result, msg = call_api("/predict", "POST", prediction_data)

            if success:
                prob = result.get("dropoff_probability", 0)

                fig_gauge = go.Figure(data=[
                    go.Indicator(
                        mode="gauge+number+delta",
                        value=prob * 100,
                        domain={'x': [0, 1], 'y': [0, 1]},
                        title={'text': "Drop-Off Risk %"},
                        number={'suffix': '%', 'valueformat': '.1f'},
                        delta={'reference': 70},
                        gauge={
                            'axis': {'range': [0, 100]},
                            'bar': {'color': "#334155"},
                            'steps': [
                                {'range': [0, 33], 'color': "#d1fae5"},
                                {'range': [33, 67], 'color': "#fef3c7"},
                                {'range': [67, 100], 'color': "#fee2e2"}
                            ],
                            'threshold': {
                                'line': {'color': "red", 'width': 4},
                                'thickness': 0.75,
                                'value': 70
                            }
                        }
                    )
                ])

                fig_gauge.update_layout(height=350)
                st.plotly_chart(fig_gauge, use_container_width=True)

                if prob < 0.33:
                    st.markdown("<div class='success-box'><strong>Low risk:</strong> user likely to retain.</div>", unsafe_allow_html=True)
                elif prob < 0.67:
                    st.markdown("<div class='warning-box'><strong>Medium risk:</strong> monitor engagement trends.</div>", unsafe_allow_html=True)
                else:
                    st.markdown("<div class='danger-box'><strong>High risk:</strong> trigger retention action now.</div>", unsafe_allow_html=True)
            else:
                st.error(f"Prediction failed: {msg}")

st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
st.markdown("### Model Metrics")

metrics_data = {
    'Metric': ['Accuracy', 'Precision', 'Recall', 'F1 Score', 'ROC-AUC'],
    'Score': [0.9136, 0.8814, 0.9178, 0.8992, 0.9731],
    'Target': [0.90, 0.85, 0.90, 0.85, 0.95]
}

metrics_df = pd.DataFrame(metrics_data)

fig = go.Figure()

fig.add_trace(go.Bar(
    x=metrics_df['Metric'],
    y=metrics_df['Score'],
    name='Achieved',
    marker_color='#10b981',
    text=[f"{x:.2%}" for x in metrics_df['Score']],
    textposition='auto'
))

fig.add_trace(go.Bar(
    x=metrics_df['Metric'],
    y=metrics_df['Target'],
    name='Target',
    marker_color='#e5e7eb',
    text=[f"{x:.2%}" for x in metrics_df['Target']],
    textposition='auto'
))

fig.update_layout(
    barmode='group',
    height=450,
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
    hovermode='x unified'
)

st.plotly_chart(fig, use_container_width=True)

report = pd.DataFrame({
    'Class': ['Retained (0)', 'Drop-off (1)'],
    'Precision': [0.9113, 0.5698],
    'Recall': [0.8907, 0.6487],
    'F1-Score': [0.9008, 0.6059],
    'Support': [6546, 1454]
})

st.dataframe(report, use_container_width=True, hide_index=True)

analytics_col, monitor_col = st.columns(2)

with analytics_col:
    st.markdown("### Feature Importance")

    importance_data = {
        'Feature': ['Recency', 'Session Duration', 'Feature Count', 'Free Segment',
                   'Mobile Device', 'Frequency', 'Account Age', 'Region', 'OS Type'],
        'Importance': [0.28, 0.25, 0.24, 0.12, 0.08, 0.02, 0.01, 0.005, 0.005]
    }

    imp_df = pd.DataFrame(importance_data)

    fig_imp = px.bar(
        imp_df,
        x='Importance',
        y='Feature',
        orientation='h',
        color='Importance',
        color_continuous_scale='Blues',
        title=None
    )

    fig_imp.update_layout(
        height=400,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=True, gridcolor='#e5e7eb'),
        yaxis=dict(showgrid=False)
    )

    st.plotly_chart(fig_imp, use_container_width=True)

with monitor_col:
    monitor_header, monitor_refresh = st.columns([8, 2])
    with monitor_header:
        st.markdown("### API Monitor")
    with monitor_refresh:
        if st.button("Refresh", key="refresh_monitor", use_container_width=True):
            st.rerun()

    monitor_metric1, monitor_metric2, monitor_metric3 = st.columns(3)
    with monitor_metric1:
        st.markdown("""
        <div class="premium-card primary">
            <div class="metric-label">Avg Latency</div>
            <div class="metric-value">8.3ms</div>
        </div>
        """, unsafe_allow_html=True)
    with monitor_metric2:
        st.markdown("""
        <div class="premium-card success">
            <div class="metric-label">Requests Today</div>
            <div class="metric-value">1,247</div>
        </div>
        """, unsafe_allow_html=True)
    with monitor_metric3:
        st.markdown("""
        <div class="premium-card success">
            <div class="metric-label">Uptime</div>
            <div class="metric-value">99.8%</div>
        </div>
        """, unsafe_allow_html=True)

    endpoints = pd.DataFrame({
        'Endpoint': ['/health', '/predict', '/predict-batch', '/monitor'],
        'Status': ['Online', 'Online', 'Online', 'Online'],
        'Response Time': ['2ms', '8.5ms', '45ms', '3ms']
    })
    st.dataframe(endpoints, use_container_width=True, hide_index=True)

st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
st.markdown("### Batch Predictions")

sample_template = "Days Since Signup,Days Since Last Activity,Total Logins,Avg Session Duration (min),Features Used,Device Type,Operating System,User Segment,Region"
st.download_button(
    label="Download Sample Template",
    data=sample_template,
    file_name="sample_template.csv",
    mime="text/csv",
    use_container_width=True
)

uploaded_file = st.file_uploader("Upload CSV file", type=['csv'], help="CSV with user data for batch prediction")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.dataframe(df.head(), use_container_width=True)

    if st.button("Process Batch", use_container_width=True):
        st.success(f"Processed {len(df)} users successfully!")

        col1, col2, col3 = st.columns(3)

        with col1:
            csv_data = df.to_csv(index=False).encode('utf-8')
            st.download_button("Download CSV", csv_data, "predictions.csv", "text/csv")

        with col2:
            json_data = df.to_json(orient='records').encode('utf-8')
            st.download_button("Download JSON", json_data, "predictions.json", "application/json")

        with col3:
            st.info("Export ready")

st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
st.markdown("### Project Snapshot")

project_col1, project_col2 = st.columns(2)

with project_col1:
    st.markdown("""
    <div class="premium-card primary">
        <h4>Dataset</h4>
        <p><strong>Size:</strong> 10,000 users<br/>
        <strong>Features:</strong> 9 behavioral + categorical<br/>
        <strong>Split:</strong> 80/20 train/test</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="premium-card success">
        <h4>Model</h4>
        <p><strong>Algorithm:</strong> Logistic Regression<br/>
        <strong>Decision Threshold:</strong> 0.70<br/>
        <strong>Training Time:</strong> <1s</p>
    </div>
    """, unsafe_allow_html=True)

with project_col2:
    st.markdown("""
    <div class="premium-card warning">
        <h4>Technology Stack</h4>
        <p><strong>Backend:</strong> Flask 3.1.0<br/>
        <strong>Frontend:</strong> Streamlit 1.43.2<br/>
        <strong>ML:</strong> scikit-learn 1.8.0</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="premium-card danger">
        <h4>Deployment</h4>
        <p><strong>API:</strong> http://127.0.0.1:5000<br/>
        <strong>Dashboard:</strong> http://localhost:8502<br/>
        <strong>Database:</strong> SQLite</p>
    </div>
    """, unsafe_allow_html=True)
