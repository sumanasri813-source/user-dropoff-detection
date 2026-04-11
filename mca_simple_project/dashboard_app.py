import streamlit as st
import requests

st.set_page_config(page_title="MCA Drop-Off Demo", layout="centered")
st.title("Silent User Drop-Off Detection")
st.caption("Simple MCA Major Project Demo")

api_url = st.text_input("API URL", value="http://127.0.0.1:5050/predict")

col1, col2 = st.columns(2)
with col1:
    days_signup_age = st.number_input("Days Since Signup", min_value=1, value=200)
    recency_days = st.number_input("Recency Days", min_value=0, value=20)
    frequency_total = st.number_input("Total Activity Count", min_value=1, value=10)
with col2:
    session_duration_avg = st.number_input("Avg Session Duration (min)", min_value=0.1, value=8.5)
    feature_count_used = st.number_input("Features Used Count", min_value=1, value=4)

if st.button("Predict Drop-Off Risk"):
    payload = {
        "days_signup_age": days_signup_age,
        "recency_days": recency_days,
        "frequency_total": frequency_total,
        "session_duration_avg": session_duration_avg,
        "feature_count_used": feature_count_used,
    }

    try:
        resp = requests.post(api_url, json=payload, timeout=10)
        data = resp.json()

        if resp.status_code == 200:
            st.success("Prediction successful")
            st.write(data)
        else:
            st.error(f"API Error ({resp.status_code}): {data}")
    except Exception as exc:
        st.error(f"Could not call API: {exc}")
