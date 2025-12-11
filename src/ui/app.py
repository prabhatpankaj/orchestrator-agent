import streamlit as st
import sys, os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from src.executor.execute import execute

st.title("Hybrid Search Orchestrator")

query = st.text_area("Enter job search query:")

if st.button("Run"):
    result = execute(query)
    st.json(result)
