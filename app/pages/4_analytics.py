"""
app/pages/4_analytics.py
Owner: Hung (A)
Advanced — Interactive analytics dashboard with Plotly charts.
Replaces the static matplotlib PNGs with interactive visualisations.
"""

from __future__ import annotations

import os

import requests
import streamlit as st

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")

st.set_page_config(page_title="Analytics — BS4 Analytics",
                   page_icon="📈", layout="wide")
st.title("📈 Analytics Dashboard")

# Fetch data
@st.cache_data(ttl=120)
def fetch_summary():
    return requests.get(f"{API_BASE}/analytics/summary", timeout=15).json()

@st.cache_data(ttl=120)
def fetch_sections():
    return requests.get(f"{API_BASE}/sections", params={"size": 200}, timeout=10).json()["items"]

@st.cache_data(ttl=120)
def fetch_link_stats():
    return requests.get(f"{API_BASE}/links/stats", timeout=10).json()

@st.cache_data(ttl=120)
def fetch_code():
    return requests.get(f"{API_BASE}/code-examples", timeout=10).json()["items"]

try:
    summary    = fetch_summary()
    sections   = fetch_sections()
    link_stats = fetch_link_stats()
    code       = fetch_code()
except Exception as e:
    st.error(f"Cannot load analytics data — is the API running and pipeline complete? ({e})")
    st.stop()

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

sections_df = pd.DataFrame(sections)
code_df     = pd.DataFrame(code)

# Metric cards
st.subheader("Key metrics")
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total sections",           summary["total_sections"])
c2.metric("find_all() examples",      summary["find_all_example_count"])
c3.metric("get_text() examples",      summary["get_text_example_count"])
c4.metric("Avg words / section",      f"{summary['avg_words_per_section']:.0f}")
c5.metric("Sections with no code",    summary["sections_with_no_code"])

st.divider()

# Tabs — one per chart / analysis type
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Word Count",
    "💻 Code Examples",
    "🔗 Link Types",
    "📏 Line Counts",
    "🔑 Keywords",
    "🔥 Similarity",
])

with tab1:
    st.subheader("Top 10 sections by word count")
    top10 = sections_df.nlargest(10, "word_count")[["section_title","word_count"]]
    fig   = px.bar(top10, x="word_count", y="section_title", orientation="h",
                   color="word_count", color_continuous_scale="Blues",
                   labels={"word_count":"Word count","section_title":"Section"})
    fig.update_layout(yaxis={"categoryorder":"total ascending"}, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("Code examples per section")
    counts = code_df.groupby("section_title").size().sort_values(ascending=False).reset_index()
    counts.columns = ["section_title", "count"]
    fig = px.bar(counts, x="section_title", y="count",
                 labels={"section_title":"Section","count":"Examples"},
                 color="count", color_continuous_scale="Teal")
    fig.update_xaxes(tickangle=45)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Method usage across all code examples")
    method_cols   = ["contains_find_all","contains_find","contains_select",
                     "contains_get_text","contains_requests"]
    method_labels = ["find_all()","find()","select()","get_text()","requests"]
    method_counts = [int(code_df[c].sum()) for c in method_cols]
    fig2 = px.bar(x=method_labels, y=method_counts,
                  labels={"x":"Method","y":"# examples using it"},
                  color=method_counts, color_continuous_scale="Purples")
    st.plotly_chart(fig2, use_container_width=True)

with tab3:
    st.subheader("Link type distribution")
    fig = px.pie(values=list(link_stats.values()),
                 names=list(link_stats.keys()),
                 color_discrete_sequence=px.colors.qualitative.Set2)
    fig.update_traces(textposition="inside", textinfo="percent+label")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Link type counts")
    st.dataframe(
        pd.DataFrame(list(link_stats.items()), columns=["Link type","Count"])
          .sort_values("Count", ascending=False),
        use_container_width=True, hide_index=True,
    )

with tab4:
    st.subheader("Code example line count distribution")
    fig = px.histogram(code_df, x="line_count", nbins=20,
                       labels={"line_count":"Lines of code","count":"Frequency"},
                       color_discrete_sequence=["#4C72B0"])
    mean   = code_df["line_count"].mean()
    median = code_df["line_count"].median()
    fig.add_vline(x=mean,   line_dash="dash",  line_color="red",
                  annotation_text=f"Mean {mean:.1f}", annotation_position="top right")
    fig.add_vline(x=median, line_dash="dashdot", line_color="orange",
                  annotation_text=f"Median {median:.1f}", annotation_position="top left")
    st.plotly_chart(fig, use_container_width=True)

with tab5:
    st.subheader("Top 10 keywords (raw frequency)")
    kw_df = pd.DataFrame(summary["top_10_keywords"])
    fig   = px.bar(kw_df, x="count", y="keyword", orientation="h",
                   color="count", color_continuous_scale="Greens",
                   labels={"count":"Frequency","keyword":"Keyword"})
    fig.update_layout(yaxis={"categoryorder":"total ascending"}, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    if summary.get("adv_top_tfidf_keywords"):
        st.subheader("Top keywords (TF-IDF weighted)")
        tfidf_df = pd.DataFrame(summary["adv_top_tfidf_keywords"])
        fig2 = px.bar(tfidf_df, x="count", y="keyword", orientation="h",
                      color="count", color_continuous_scale="Oranges",
                      labels={"count":"TF-IDF score","keyword":"Keyword"})
        fig2.update_layout(yaxis={"categoryorder":"total ascending"}, showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)

with tab6:
    if summary.get("adv_top_similar_pairs"):
        st.subheader("Most similar section pairs (cosine similarity)")
        pairs_df = pd.DataFrame(
            summary["adv_top_similar_pairs"],
            columns=["Section A","Section B","Similarity"],
        )
        pairs_df["Similarity"] = pairs_df["Similarity"].round(3)
        st.dataframe(pairs_df, use_container_width=True, hide_index=True)

        # Heatmap — requires advanced pipeline to have run
        try:
            from pipeline.advanced.similarity import compute_similarity_matrix
            from shared.utils import load_sections as _ls
            import numpy as np
            sdf    = _ls()
            matrix = compute_similarity_matrix(sdf)
            titles = sdf["section_title"].tolist()
            fig_hm = go.Figure(data=go.Heatmap(
                z=matrix, x=titles, y=titles,
                colorscale="Blues", showscale=True,
            ))
            fig_hm.update_layout(
                title="Section Cosine Similarity Heatmap",
                xaxis_tickangle=45,
                height=700,
            )
            st.plotly_chart(fig_hm, use_container_width=True)
        except Exception:
            st.info("Similarity heatmap requires the advanced pipeline to have run.")
    else:
        st.info("Run the advanced pipeline (Hung) to see section similarity data.")
