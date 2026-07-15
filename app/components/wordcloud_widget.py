"""
app/components/wordcloud_widget.py
Advanced - keyword wordcloud rendered with the `wordcloud` library + matplotlib.
Uses `wordcloud` package (pip install wordcloud), NOT streamlit-wordcloud.
"""
from __future__ import annotations
import sys
from pathlib import Path
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import io

import matplotlib.pyplot as plt
import streamlit as st


def render_wordcloud(keywords: list[dict], title: str = "Keyword Cloud") -> None:
    """
    Render a wordcloud from a list of {"keyword": str, "count": float} dicts.
    Displayed inline in Streamlit via st.image().

    Parameters
    ----------
    keywords : list[dict]
        Each dict must have "keyword" (str) and "count" (float | int).
        Typically from AnalyticsSummary.top_10_keywords or adv_top_tfidf_keywords.
    title : str
        Section header shown above the wordcloud.
    """
    try:
        from wordcloud import WordCloud
    except ImportError:
        st.warning("wordcloud not installed. Run: `pip install wordcloud`")
        return

    if not keywords:
        st.info("No keyword data - run the pipeline first.")
        return

    # Build frequency dict from the keyword list
    freq = {item["keyword"]: float(item["count"]) for item in keywords}

    wc = WordCloud(
        width=800,
        height=400,
        background_color="white",
        colormap="Blues",
        max_words=50,
        prefer_horizontal=0.9,
        collocations=False,
    ).generate_from_frequencies(freq)

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.imshow(wc, interpolation="bilinear")
    ax.axis("off")
    fig.tight_layout(pad=0)

    # Convert matplotlib figure to PNG bytes for st.image
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)

    st.subheader(title)
    st.image(buf, use_column_width=True)