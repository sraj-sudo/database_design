import streamlit as st
import requests
import pandas as pd
from urllib.parse import urljoin

st.set_page_config(page_title="Prod-Test Sync", layout="wide")

API_BASE = st.sidebar.text_input("API base URL", value="http://localhost:5000")

def get_json(path):
    try:
        r = requests.get(urljoin(API_BASE, path), timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"Error calling {path}: {e}")
        return []

st.title("Prod ↔ Test Sync — Visualizer")

col1, col2 = st.columns(2)

with col1:
    st.header("Production (prod)")
    prod = get_json("/prod")
    if prod:
        df_prod = pd.DataFrame(prod)
        st.dataframe(df_prod)
    else:
        st.write("No prod rows or error fetching prod.")

with col2:
    st.header("Test (test)")
    test = get_json("/test")
    if test:
        df_test = pd.DataFrame(test)
        st.dataframe(df_test)
    else:
        st.write("No test rows or error fetching test.")

st.markdown("---")
st.header("Actions")

with st.form("pull_form"):
    st.subheader("Pull filtered Prod → Test")
    region = st.text_input("region (exact match)", value="TEST")
    spec = st.text_input("spec (exact match)", value="S1")
    submitted = st.form_submit_button("Pull")
    if submitted:
        payload = {}
        if region: payload["region"] = region
        if spec: payload["spec"] = spec
        try:
            r = requests.post(urljoin(API_BASE, "/pull/prod-to-test"), json=payload, timeout=10)
            r.raise_for_status()
            st.success(f"Pulled: {r.json()}")
        except Exception as e:
            st.error(f"Error pulling: {e}")

with st.form("push_form"):
    st.subheader("Replicate Test → Prod (push all test rows)")
    submitted2 = st.form_submit_button("Replicate")
    if submitted2:
        try:
            r = requests.post(urljoin(API_BASE, "/replicate/test-to-prod"), timeout=10)
            r.raise_for_status()
            st.success(f"Pushed: {r.json()}")
        except Exception as e:
            st.error(f"Error replicating: {e}")

st.markdown("---")
st.info("Notes: The Flask API must be reachable at the API base URL. When running in Docker using the provided Dockerfile, both services run in the same container and you can use http://localhost:5000 as the API base URL from the host.")
