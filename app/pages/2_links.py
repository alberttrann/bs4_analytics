"""
app/pages/2_links.py
Link explorer - type filter, pie chart, data table, calls GET /links and /links/stats.
"""
from __future__ import annotations
import sys
from pathlib import Path
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import os

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

from shared.constants import LINK_TYPES

from app.config import API_BASE, WS_BASE

st.set_page_config(page_title="Links - BS4 Analytics",
                   page_icon="🔗", layout="wide")
st.title("🔗 Extracted Links")

# Fetch link stats for the pie chart
@st.cache_data(ttl=60, show_spinner=False)
def fetch_stats():
    try:
        return requests.get(f"{API_BASE}/links/stats", timeout=8).json()
    except Exception as e:
        return {"error": str(e)}

stats = fetch_stats()
if "error" not in stats:
    total_links = sum(stats.values())
    st.caption(f"Total links extracted: **{total_links:,}**")

    col_pie, col_table = st.columns([2, 1])
    with col_pie:
        fig = px.pie(
            values=list(stats.values()),
            names=list(stats.keys()),
            title="Link Type Distribution",
            color_discrete_sequence=px.colors.qualitative.Set2,
            hole=0.35,
        )
        fig.update_traces(textposition="inside", textinfo="percent+label")
        fig.update_layout(showlegend=False, margin=dict(t=40, b=0, l=0, r=0))
        st.plotly_chart(fig, use_container_width=True)

    with col_table:
        st.markdown("**Counts by type**")
        df_stats = pd.DataFrame(
            [(k, v, f"{v/total_links*100:.1f}%") for k, v in sorted(stats.items(), key=lambda x: -x[1])],
            columns=["Type", "Count", "%"],
        )
        st.dataframe(df_stats, hide_index=True, use_container_width=True)

st.divider()

# Controls for the link table
col_type, col_search = st.columns([2, 3])
with col_type:
    selected_type = st.selectbox("Filter by link type", ["All"] + LINK_TYPES)
with col_search:
    search_q = st.text_input("🔍 Search link text or URL", placeholder="e.g. pypi.org")

# Fetch and display link table
@st.cache_data(ttl=60, show_spinner=False)
def fetch_links(lt, sq):
    params = {}
    if lt and lt != "All": params["link_type"] = lt
    if sq:                 params["search"]    = sq
    try:
        r = requests.get(f"{API_BASE}/links", params=params, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}

link_data = fetch_links(selected_type, search_q)

if "error" in link_data:
    st.error(f"Cannot load links: {link_data['error']}")
else:
    items = link_data.get("items", [])
    st.caption(f"Showing {len(items)} link(s)")
    if items:
        df = pd.DataFrame(items)
        # Make href clickable
        df["href_display"] = df["href"].apply(
            lambda h: f"[{h[:60]}...]({h})" if len(h) > 60 else f"[{h}]({h})"
            if h.startswith("http") else h
        )
if items:
    df = pd.DataFrame(items)
    
    BS4_DOC_URL = "https://www.crummy.com/software/BeautifulSoup/bs4/doc/"
    
    # Internal anchors get prefixed with the real docs URL
    df["url_display"] = df["href"].apply(
        lambda h: BS4_DOC_URL + h if h.startswith("#") else h
    )
    
    st.dataframe(
        df[["link_text", "url_display", "link_type", "section_title"]],
        use_container_width=True,
        hide_index=True,
        column_config={
            "link_text":     st.column_config.TextColumn("Link Text"),
            "url_display":   st.column_config.LinkColumn("URL"),
            "link_type":     st.column_config.TextColumn("Type"),
            "section_title": st.column_config.TextColumn("Section"),
        },
    )
else:
    st.info("No links match the current filters.")
