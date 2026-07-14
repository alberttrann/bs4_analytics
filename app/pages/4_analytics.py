"""
app/pages/4_analytics.py
Owner: Hung (A)
Advanced analytics dashboard - fully wired with all advanced features.
"""

from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import os
import requests
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from app.config import API_BASE

st.set_page_config(page_title="Analytics - BS4 Analytics",
                   page_icon="📈", layout="wide")
st.title("📈 Analytics Dashboard")


# ---------------------------------------------------------------------------
# Fetch helpers - no caching to avoid stale data
# ---------------------------------------------------------------------------

def fetch_summary():
    r = requests.get(f"{API_BASE}/analytics/summary", timeout=15)
    r.raise_for_status()
    return r.json()

def fetch_sections():
    r = requests.get(f"{API_BASE}/sections", params={"size": 200}, timeout=10)
    r.raise_for_status()
    return r.json()["items"]

def fetch_link_stats():
    r = requests.get(f"{API_BASE}/links/stats", timeout=10)
    r.raise_for_status()
    return r.json()

def fetch_code():
    r = requests.get(f"{API_BASE}/code-examples", timeout=10)
    r.raise_for_status()
    return r.json()["items"]

try:
    summary    = fetch_summary()
    sections   = fetch_sections()
    link_stats = fetch_link_stats()
    code       = fetch_code()
except Exception as e:
    st.error(f"Cannot load data: {e}")
    st.stop()

sections_df = pd.DataFrame(sections)
code_df     = pd.DataFrame(code)

# ---------------------------------------------------------------------------
# Metric cards (stat_cards component)
# ---------------------------------------------------------------------------
st.subheader("Key metrics")
c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Sections",               summary.get("total_sections", "–"))
c2.metric("find_all() examples",    summary.get("find_all_example_count", "–"))
c3.metric("get_text() examples",    summary.get("get_text_example_count", "–"))
c4.metric("Avg words / section",    f"{summary.get('avg_words_per_section', 0):.0f}")
c5.metric("Sections (no code)",     summary.get("sections_with_no_code", "–"))
c6.metric("Readability score",
          f"{summary['adv_avg_readability_score']:.1f}"
          if summary.get("adv_avg_readability_score") else "–")

st.divider()

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "📊 Word Count",
    "💻 Code Examples",
    "🔗 Link Types",
    "📏 Line Counts",
    "🔑 Keywords (Freq)",
    "🧠 Keywords (TF-IDF)",
    "📖 Readability",
    "🔥 Similarity",
])

# ── Tab 1 - Word Count ──────────────────────────────────────────────────────
with tab1:
    st.subheader("Top 10 sections by word count")
    top10 = sections_df.nlargest(10, "word_count")[["section_title", "word_count"]]
    fig = px.bar(top10, x="word_count", y="section_title", orientation="h",
                 color="word_count", color_continuous_scale="Blues",
                 labels={"word_count": "Word count", "section_title": "Section"})
    fig.update_layout(yaxis={"categoryorder": "total ascending"}, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

# ── Tab 2 - Code Examples ───────────────────────────────────────────────────
with tab2:
    st.subheader("Code examples per section (top 10)")
    counts = (code_df.groupby("section_title").size()
                     .sort_values(ascending=False).head(10).reset_index())
    counts.columns = ["section_title", "count"]
    fig = px.bar(counts, x="section_title", y="count",
                 labels={"section_title": "Section", "count": "Examples"},
                 color="count", color_continuous_scale="Teal")
    fig.update_xaxes(tickangle=40)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Method usage across all code examples")
    method_labels = ["find_all()", "find()", "select()", "get_text()", "requests"]
    method_cols   = ["contains_find_all", "contains_find", "contains_select",
                     "contains_get_text", "contains_requests"]
    method_counts = [int(code_df[c].astype(bool).sum()) for c in method_cols]
    fig2 = px.bar(x=method_labels, y=method_counts,
                  labels={"x": "Method", "y": "# examples"},
                  color=method_counts, color_continuous_scale="Purples")
    st.plotly_chart(fig2, use_container_width=True)

# ── Tab 3 - Link Types ──────────────────────────────────────────────────────
with tab3:
    st.subheader("Link type distribution")
    fig = px.pie(values=list(link_stats.values()),
                 names=list(link_stats.keys()),
                 color_discrete_sequence=px.colors.qualitative.Set2,
                 hole=0.35)
    fig.update_traces(textposition="inside", textinfo="percent+label")
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(
        pd.DataFrame(list(link_stats.items()), columns=["Link type", "Count"])
          .sort_values("Count", ascending=False),
        use_container_width=True, hide_index=True,
    )

# ── Tab 4 - Line Counts ─────────────────────────────────────────────────────
with tab4:
    st.subheader("Code example line count distribution")
    mean_v   = code_df["line_count"].mean()
    median_v = code_df["line_count"].median()
    fig = px.histogram(code_df, x="line_count", nbins=20,
                       labels={"line_count": "Lines", "count": "Frequency"},
                       color_discrete_sequence=["#4C72B0"])
    fig.add_vline(x=mean_v,   line_dash="dash",   line_color="red",
                  annotation_text=f"Mean {mean_v:.1f}")
    fig.add_vline(x=median_v, line_dash="dashdot", line_color="green",
                  annotation_text=f"Median {median_v:.1f}")
    st.plotly_chart(fig, use_container_width=True)

# ── Tab 5 - Keywords (raw frequency) ───────────────────────────────────────
with tab5:
    st.subheader("Top 10 keywords - raw frequency")
    kw_data = summary.get("top_10_keywords", [])
    if kw_data:
        kw_df = pd.DataFrame(kw_data)
        fig = px.bar(kw_df, x="count", y="keyword", orientation="h",
                     color="count", color_continuous_scale="Greens",
                     labels={"count": "Frequency", "keyword": "Keyword"})
        fig.update_layout(yaxis={"categoryorder": "total ascending"}, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Run the pipeline to see keyword data.")

# ── Tab 6 - TF-IDF Keywords + Wordcloud ────────────────────────────────────
with tab6:
    tfidf_data = summary.get("adv_top_tfidf_keywords")
    if tfidf_data:
        st.subheader("Top keywords - TF-IDF weighted")
        tfidf_df = pd.DataFrame(tfidf_data[:20])
        fig = px.bar(tfidf_df, x="count", y="keyword", orientation="h",
                     color="count", color_continuous_scale="Oranges",
                     labels={"count": "TF-IDF score", "keyword": "Keyword"})
        fig.update_layout(yaxis={"categoryorder": "total ascending"}, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

        st.divider()
        st.subheader("Keyword wordcloud")
        try:
            from app.components.wordcloud_widget import render_wordcloud
            render_wordcloud(tfidf_data, title="")
        except Exception as e:
            st.warning(f"Wordcloud unavailable: {e}")
    else:
        st.info("Run `python -m pipeline.pipeline --skip-fetch` to generate TF-IDF data.")

# ── Tab 7 - Readability ─────────────────────────────────────────────────────
with tab7:
    avg_score = summary.get("adv_avg_readability_score")
    if avg_score:
        st.subheader("Flesch Reading Ease - per section")
        st.metric("Mean readability score", f"{avg_score:.1f} / 100")
        st.caption(
            "**Scale:** 90–100 = Very Easy · 70–90 = Easy · "
            "60–70 = Standard · 30–60 = Difficult · 0–30 = Very Difficult"
        )

        # Compute per-section scores live
        try:
            from pipeline.advanced.nlp_analyzer import compute_readability
            from shared.utils import load_sections
            sdf    = load_sections()
            scores = compute_readability(sdf)
            sdf    = sdf.copy()
            sdf["readability"] = scores.values

            fig = px.bar(
                sdf.sort_values("readability", ascending=False).head(20),
                x="readability", y="section_title", orientation="h",
                color="readability",
                color_continuous_scale="RdYlGn",
                range_color=[0, 100],
                labels={"readability": "Flesch score", "section_title": "Section"},
                title="Top 20 sections by readability",
            )
            fig.update_layout(yaxis={"categoryorder": "total ascending"}, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

            col_easy, col_hard = st.columns(2)
            col_easy.success(f"**Easiest:** {sdf.loc[scores.idxmax(), 'section_title']}"
                             f" ({scores.max():.1f})")
            col_hard.error(f"**Hardest:** {sdf.loc[scores.idxmin(), 'section_title']}"
                           f" ({scores.min():.1f})")
        except Exception as e:
            st.warning(f"Could not compute per-section scores: {e}")
    else:
        st.info("Run `python -m pipeline.pipeline --skip-fetch` to generate readability data.")

# ── Tab 8 - Similarity ──────────────────────────────────────────────────────
with tab8:
    pairs_data = summary.get("adv_top_similar_pairs")
    if pairs_data:
        st.subheader("Most similar section pairs")
        pairs_df = pd.DataFrame(pairs_data, columns=["Section A", "Section B", "Score"])
        pairs_df["Score"] = pairs_df["Score"].round(3)
        st.dataframe(pairs_df, use_container_width=True, hide_index=True)

        st.divider()
        st.subheader("Section similarity heatmap")
        try:
            from pipeline.advanced.similarity import compute_similarity_matrix
            from shared.utils import load_sections
            sdf    = load_sections()
            matrix = compute_similarity_matrix(sdf)
            titles = sdf["section_title"].tolist()
            fig_hm = go.Figure(data=go.Heatmap(
                z=matrix, x=titles, y=titles,
                colorscale="Blues",
                showscale=True,
            ))
            fig_hm.update_layout(
                title="Full Section Cosine Similarity Matrix",
                xaxis_tickangle=45,
                height=800,
                xaxis={"tickfont": {"size": 8}},
                yaxis={"tickfont": {"size": 8}},
            )
            st.plotly_chart(fig_hm, use_container_width=True)
        except Exception as e:
            st.warning(f"Could not render heatmap: {e}")

        st.divider()
        st.subheader("Section dependency network")
        try:
            from app.components.network_graph import render_network_graph
            render_network_graph()
        except Exception as e:
            st.warning(f"Network graph unavailable: {e}")
    else:
        st.info("Run `python -m pipeline.pipeline --skip-fetch` to generate similarity data.")