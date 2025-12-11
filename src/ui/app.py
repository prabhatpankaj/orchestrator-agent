import streamlit as st
import sys, os, traceback
import pandas as pd
import aerospike
import pymysql

# ------------------------------------------------------------------
# Ensure correct import path for Docker + host environments
# ------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.executor.execute import execute

# ------------------------------------------------------------------
# CONFIG
# ------------------------------------------------------------------
MYSQL_HOST = os.getenv("MYSQL_HOST", "mysql")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "root")
MYSQL_DB = os.getenv("MYSQL_DB", "jobs_db")

AS_HOST = os.getenv("AEROSPIKE_HOST", "aerospike")
AS_PORT = int(os.getenv("AEROSPIKE_PORT", 3000))


# ------------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------------
def get_mysql_connection():
    try:
        return pymysql.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DB,
            autocommit=True,
            cursorclass=pymysql.cursors.DictCursor
        )
    except Exception as e:
        st.error(f"MySQL Connection Error: {e}")
        return None


def get_aerospike_client():
    config = {"hosts": [(AS_HOST, AS_PORT)]}
    try:
        client = aerospike.client(config).connect()
        return client
    except Exception as e:
        st.error(f"Failed to connect to Aerospike: {e}")
        return None


# ------------------------------------------------------------------
# ORCHESTRATOR PAGE
# ------------------------------------------------------------------
def page_orchestrator():
    st.title("🤖 Hybrid Search Orchestrator")
    st.write("Enter a query. The agent will rewrite → search (BM25 + Vector) → rerank → return results.")

    query = st.text_area("Enter job search query:", height=120)

    if st.button("Run Agent"):
        if not query.strip():
            st.warning("Please enter a query.")
            return

        with st.spinner("Running orchestrator + tools..."):
            try:
                result = execute(query)

                st.success("Execution Complete!")

                # Render every step
                for step in result:
                    tool = step.get("tool", "unknown")
                    inp = step.get("input", "")
                    out = step.get("output", {})

                    with st.expander(f"Step: {tool}", expanded=False):
                        st.markdown(f"**Input:** `{inp}`")

                        # Output must be JSON/dict-like
                        if isinstance(out, (dict, list)):
                            st.json(out)
                        else:
                            st.warning("Tool returned non-JSON output:")
                            st.write(out)

            except Exception as e:
                st.error(f"Error: {e}")
                st.code(traceback.format_exc())


# ------------------------------------------------------------------
# DATA BROWSER PAGE
# ------------------------------------------------------------------
def page_data_browser():
    st.title("🗄️ Data Browser")

    tab1, tab2 = st.tabs(["MySQL (Relational)", "Aerospike (Key-Value)"])

    # ------------------ MySQL Tab --------------------
    with tab1:
        st.subheader("MySQL: jobs_db.jobs")

        if st.button("Refresh MySQL Data"):
            conn = get_mysql_connection()
            if conn:
                try:
                    with conn.cursor() as cursor:
                        cursor.execute("SELECT * FROM jobs ORDER BY job_id DESC LIMIT 50")
                        rows = cursor.fetchall()

                        if rows:
                            st.dataframe(pd.DataFrame(rows))
                        else:
                            st.info("No data found.")
                except Exception as e:
                    st.error(f"MySQL Error: {e}")
                conn.close()

    # ------------------ Aerospike Tab --------------------
    with tab2:
        st.subheader("Aerospike: test.jobs")

        job_id = st.text_input("Enter Job ID", value="1")

        if st.button("Fetch from Aerospike"):
            client = get_aerospike_client()
            if client:
                key = ("test", "jobs", str(job_id))
                try:
                    _, meta, bins = client.get(key)
                    if bins:
                        st.success("Record Found!")
                        st.json(bins)
                        st.write("**Metadata:**", meta)
                    else:
                        st.warning("Record not found.")
                except aerospike.exception.RecordNotFound:
                    st.warning("Record not found.")
                except Exception as e:
                    st.error(f"Aerospike Error: {e}")
                finally:
                    client.close()


# ------------------------------------------------------------------
# MAIN
# ------------------------------------------------------------------
st.set_page_config(page_title="Orchestrator Agent", layout="wide")

sidebar = st.sidebar
sidebar.title("Navigation")
page = sidebar.radio("Go to:", ["Orchestrator", "Data Browser"])

if page == "Orchestrator":
    page_orchestrator()
else:
    page_data_browser()
