"""
app/main.pyStreamlit entry point — page config, sidebar navigation, API health check.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import os
import requests
import streamlit as st

from app.config import API_BASE

st.set_page_config(
    page_title="BS4 Documentation Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

if "pipeline_running" not in st.session_state:
    st.session_state["pipeline_running"] = False

# Sidebar
with st.sidebar:
    st.title("📊 BS4 Analytics")
    st.caption("BeautifulSoup Documentation Analytics System")
    st.divider()

    try:
        health = requests.get(f"{API_BASE}/health", timeout=3).json()
        if health.get("status") == "ok":
            st.success("API connected ✓")
            files     = health.get("data_files_present", {})
            all_ready = all(files.values())
            if all_ready:
                st.info("Pipeline data ready ✓")
            else:
                missing = [k for k, v in files.items() if not v]
                st.warning(f"Missing: {', '.join(missing)}")
    except Exception:
        st.error(f"API unreachable — is uvicorn running?\n`{API_BASE}`")

    st.divider()
    st.caption(f"API: `{API_BASE}`")

# Landing content
st.title("📊 BeautifulSoup Documentation Analytics")
st.markdown(
    "This system scrapes, parses, and analyses the official "
    "[BeautifulSoup 4 documentation](https://www.crummy.com/software/BeautifulSoup/bs4/doc/). "
    "Use the sidebar to navigate between pages."
)

col1, col2 = st.columns(2)
with col1:
    st.markdown("""
| Page | What you'll find |
|------|-----------------|
| 🏠 **Home** | Run the pipeline, live progress, health dashboard |
| 📄 **Sections** | Browse all documentation sections |
| 🔗 **Links** | Explore extracted hyperlinks by type |
""")
with col2:
    st.markdown("""
| Page | What you'll find |
|------|-----------------|
| 💻 **Code** | Browse code examples, filter by BS4 method |
| 📈 **Analytics** | Interactive charts, 10 analysis questions |
| 📥 **Report** | Download Markdown report, Excel workbook, charts |
""")

st.divider()
st.info("💡 First time? Go to the **Home** page and click **▶ Run Pipeline** to generate all data.")
