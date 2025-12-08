import os
import sys

# Fix Python path so Streamlit can import correctly
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from executor.execute import execute
import streamlit as st

st.title("Local AI Orchestrator (Qwen2.5-3B)")

query = st.text_area("Ask something:")

if st.button("Run"):
    results = execute(query)
    st.json(results)
