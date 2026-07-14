"""
pipeline/visualizer.py
Feature 7 - Data Visualization
8 charts total: 4 required + 4 advanced (using nlp_analyzer and similarity)
"""

from __future__ import annotations

import logging
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd

from shared.constants import (
    ALL_CHART_PATHS,
    CHART_CODE_BY_SECTION,
    CHART_LINECOUNT_HIST,
    CHART_LINK_DIST,
    CHART_METHOD_USAGE,
    CHART_READABILITY,
    CHART_SIMILARITY,
    CHART_TFIDF_KEYWORDS,
    CHART_WORD_COUNT,
)
from shared.utils import ensure_dirs, load_code_examples, load_links, load_sections

logger = logging.getLogger(__name__)

plt.style.use("seaborn-v0_8-whitegrid")
_PRIMARY   = "#4C72B0"
_SECONDARY = "#55A868"
_ACCENT    = ["#4C72B0", "#55A868", "#C44E52", "#8172B2", "#CCB974"]
_DPI       = 150
_TOP_N     = 10


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def plot_all(
    sections: pd.DataFrame | None = None,
    links:    pd.DataFrame | None = None,
    code:     pd.DataFrame | None = None,
) -> list[Path]:
    ensure_dirs()
    sections = sections if sections is not None else load_sections()
    links    = links    if links    is not None else load_links()
    code     = code     if code     is not None else load_code_examples()

    paths = [
        # Required
        plot_top_sections_by_wordcount(sections),
        plot_code_examples_by_section(code),
        plot_link_type_distribution(links),
        plot_code_linecount_histogram(code),
        # Advanced
        plot_tfidf_vs_frequency(sections),
        plot_readability_by_section(sections),
        plot_similarity_heatmap(sections),
        plot_method_usage(code),
    ]
    logger.info("Generated %d charts", len(paths))
    return paths


# ---------------------------------------------------------------------------
# Chart 1 - Word count bar
# ---------------------------------------------------------------------------

def plot_top_sections_by_wordcount(sections, out=CHART_WORD_COUNT):
    df = sections.nlargest(_TOP_N, "word_count")[["section_title", "word_count"]]
    fig, ax = plt.subplots(figsize=(11, 6))
    bars = ax.barh(df["section_title"], df["word_count"],
                   color=_PRIMARY, edgecolor="white", linewidth=0.5)
    ax.invert_yaxis()
    for bar in bars:
        w = bar.get_width()
        ax.text(w + 5, bar.get_y() + bar.get_height() / 2,
                f"{int(w):,}", va="center", ha="left", fontsize=8)
    ax.set_xlabel("Word Count", fontsize=11)
    ax.set_title(f"Top {_TOP_N} Sections by Word Count",
                 fontsize=13, fontweight="bold", pad=12)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
    ax.set_yticklabels(
        [t[:45] + "…" if len(t) > 45 else t for t in df["section_title"]],
        fontsize=9)
    fig.tight_layout()
    fig.savefig(out, dpi=_DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"[visualizer] Saved {out.name}")
    return out


# ---------------------------------------------------------------------------
# Chart 2 - Code examples per section
# ---------------------------------------------------------------------------

def plot_code_examples_by_section(code, out=CHART_CODE_BY_SECTION):
    counts = (code.groupby("section_title").size()
                  .sort_values(ascending=False).head(_TOP_N))
    labels = [t[:30] + "…" if len(t) > 30 else t for t in counts.index]
    fig, ax = plt.subplots(figsize=(12, 5))
    bars = ax.bar(range(len(counts)), counts.values,
                  color=_PRIMARY, edgecolor="white")
    for bar in bars:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, h + 0.1,
                str(int(h)), ha="center", va="bottom", fontsize=8)
    ax.set_xticks(range(len(counts)))
    ax.set_xticklabels(labels, rotation=40, ha="right", fontsize=8)
    ax.set_ylabel("Number of Code Examples", fontsize=11)
    ax.set_title(f"Code Examples per Section (Top {_TOP_N})",
                 fontsize=13, fontweight="bold", pad=12)
    fig.tight_layout()
    fig.savefig(out, dpi=_DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"[visualizer] Saved {out.name}")
    return out


# ---------------------------------------------------------------------------
# Chart 3 - Link type pie
# ---------------------------------------------------------------------------

def plot_link_type_distribution(links, out=CHART_LINK_DIST):
    counts = links["link_type"].value_counts()
    fig, ax = plt.subplots(figsize=(8, 7))
    wedges, _, autotexts = ax.pie(
        counts.values, labels=None,
        autopct=lambda p: f"{p:.1f}%\n({int(round(p * counts.sum() / 100))})",
        colors=_ACCENT[:len(counts)], startangle=140,
        pctdistance=0.75, wedgeprops={"linewidth": 1, "edgecolor": "white"},
    )
    for at in autotexts:
        at.set_fontsize(8)
    ax.legend(wedges,
              [f"{n}  ({c:,})" for n, c in zip(counts.index, counts.values)],
              loc="lower center", bbox_to_anchor=(0.5, -0.12), ncol=2, fontsize=9)
    ax.set_title("Link Type Distribution", fontsize=13, fontweight="bold", pad=16)
    fig.tight_layout()
    fig.savefig(out, dpi=_DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"[visualizer] Saved {out.name}")
    return out


# ---------------------------------------------------------------------------
# Chart 4 - Line count histogram
# ---------------------------------------------------------------------------

def plot_code_linecount_histogram(code, out=CHART_LINECOUNT_HIST, bins=20):
    lc     = code["line_count"].dropna()
    mean_v = float(lc.mean())
    med_v  = float(lc.median())
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.hist(lc, bins=bins, color=_PRIMARY, edgecolor="white", linewidth=0.5)
    ax.axvline(mean_v, color="#C44E52", linestyle="--", linewidth=1.5,
               label=f"Mean = {mean_v:.1f}")
    ax.axvline(med_v,  color=_SECONDARY, linestyle="-.", linewidth=1.5,
               label=f"Median = {med_v:.1f}")
    ax.set_xlabel("Number of Lines", fontsize=11)
    ax.set_ylabel("Frequency", fontsize=11)
    ax.set_title("Code Example Line Count Distribution",
                 fontsize=13, fontweight="bold", pad=12)
    ax.legend(fontsize=9)
    ax.text(0.97, 0.95,
            f"n = {len(lc)}\nMax = {int(lc.max())}\nStd = {lc.std():.1f}",
            transform=ax.transAxes, fontsize=8, va="top", ha="right",
            bbox=dict(boxstyle="round,pad=0.4", facecolor="white", alpha=0.8))
    fig.tight_layout()
    fig.savefig(out, dpi=_DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"[visualizer] Saved {out.name}")
    return out


# ---------------------------------------------------------------------------
# Chart 5 - TF-IDF vs raw frequency comparison (Advanced)
# ---------------------------------------------------------------------------

def plot_tfidf_vs_frequency(sections, out=CHART_TFIDF_KEYWORDS):
    """Side-by-side bar: raw frequency (Q5) vs TF-IDF weighted ranking."""
    import re
    from collections import Counter
    from shared.constants import STOPWORDS

    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        sklearn_available = True
    except ImportError:
        sklearn_available = False

    # Raw frequency top 10
    all_text = " ".join(sections["section_text"].fillna("")).lower()
    words    = re.findall(r"\b[a-z][a-z0-9_]{2,}\b", all_text)
    raw_counts = Counter(w for w in words if w not in STOPWORDS)
    raw_top10  = raw_counts.most_common(10)
    raw_kw, raw_vals = zip(*raw_top10)

    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    # Left - raw frequency
    ax = axes[0]
    bars = ax.barh(list(raw_kw), list(raw_vals), color=_PRIMARY, edgecolor="white")
    ax.invert_yaxis()
    for bar in bars:
        w = bar.get_width()
        ax.text(w + 2, bar.get_y() + bar.get_height() / 2,
                f"{int(w)}", va="center", ha="left", fontsize=8)
    ax.set_title("Top 10 Keywords - Raw Frequency", fontsize=12, fontweight="bold")
    ax.set_xlabel("Occurrences")

    # Right - TF-IDF
    ax2 = axes[1]
    if sklearn_available:
        vec    = TfidfVectorizer(stop_words="english", max_features=500)
        X      = vec.fit_transform(sections["section_text"].fillna(""))
        scores = X.toarray().sum(axis=0)
        terms  = vec.get_feature_names_out()
        ranked = sorted(zip(terms, scores), key=lambda x: -x[1])[:10]
        tfidf_kw, tfidf_vals = zip(*ranked)
        bars2 = ax2.barh(list(tfidf_kw), list(tfidf_vals),
                         color="#E8812A", edgecolor="white")
        ax2.invert_yaxis()
        for bar in bars2:
            w = bar.get_width()
            ax2.text(w + 0.01, bar.get_y() + bar.get_height() / 2,
                     f"{w:.2f}", va="center", ha="left", fontsize=8)
        ax2.set_title("Top 10 Keywords - TF-IDF Weighted", fontsize=12, fontweight="bold")
        ax2.set_xlabel("TF-IDF Score")
    else:
        ax2.text(0.5, 0.5, "scikit-learn not installed",
                 ha="center", va="center", transform=ax2.transAxes)

    fig.suptitle("Keyword Analysis: Raw Frequency vs TF-IDF",
                 fontsize=14, fontweight="bold", y=1.01)
    fig.tight_layout()
    fig.savefig(out, dpi=_DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"[visualizer] Saved {out.name}")
    return out


# ---------------------------------------------------------------------------
# Chart 6 - Readability by section (Advanced)
# ---------------------------------------------------------------------------

def plot_readability_by_section(sections, out=CHART_READABILITY, top_n=20):
    """Horizontal bar - top and bottom N sections by Flesch Reading Ease."""
    try:
        import textstat
    except ImportError:
        print("[visualizer] textstat not installed - skipping readability chart")
        # Create placeholder
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.text(0.5, 0.5, "textstat not installed\npip install textstat",
                ha="center", va="center", transform=ax.transAxes, fontsize=12)
        fig.savefig(out, dpi=_DPI, bbox_inches="tight")
        plt.close(fig)
        return out

    scores = sections["section_text"].fillna("").apply(textstat.flesch_reading_ease)
    df     = sections[["section_title"]].copy()
    df["score"] = scores.values
    df = df[df["section_title"] != "Unknown"].dropna()

    # Top 10 easiest + top 10 hardest
    easiest = df.nlargest(10, "score")
    hardest = df.nsmallest(10, "score")
    plot_df = pd.concat([easiest, hardest]).drop_duplicates()
    plot_df = plot_df.sort_values("score", ascending=True)

    colors = ["#C44E52" if s < 50 else "#55A868" if s > 70 else _PRIMARY
              for s in plot_df["score"]]

    fig, ax = plt.subplots(figsize=(12, 8))
    bars = ax.barh(
        [t[:40] + "…" if len(t) > 40 else t for t in plot_df["section_title"]],
        plot_df["score"],
        color=colors, edgecolor="white",
    )
    for bar in bars:
        w = bar.get_width()
        ax.text(w + 0.5, bar.get_y() + bar.get_height() / 2,
                f"{w:.1f}", va="center", ha="left", fontsize=7)

    ax.axvline(60, color="orange", linestyle="--", linewidth=1,
               label="Standard threshold (60)")
    ax.axvline(float(scores.mean()), color="purple", linestyle=":",
               linewidth=1.5, label=f"Mean ({scores.mean():.1f})")

    ax.set_xlabel("Flesch Reading Ease Score", fontsize=11)
    ax.set_title("Section Readability - Flesch Reading Ease\n"
                 "(Green > 70 Easy · Blue 50–70 Standard · Red < 50 Difficult)",
                 fontsize=12, fontweight="bold", pad=12)
    ax.legend(fontsize=9)
    ax.set_xlim(0, 110)
    fig.tight_layout()
    fig.savefig(out, dpi=_DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"[visualizer] Saved {out.name}")
    return out


# ---------------------------------------------------------------------------
# Chart 7 - Similarity heatmap (Advanced)
# ---------------------------------------------------------------------------

def plot_similarity_heatmap(sections, out=CHART_SIMILARITY, top_n=30):
    """Heatmap of cosine similarity between top N sections by word count."""
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
    except ImportError:
        print("[visualizer] scikit-learn not installed - skipping similarity chart")
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.text(0.5, 0.5, "scikit-learn not installed\npip install scikit-learn",
                ha="center", va="center", transform=ax.transAxes, fontsize=12)
        fig.savefig(out, dpi=_DPI, bbox_inches="tight")
        plt.close(fig)
        return out

    # Use top_n sections by word count (most content-rich, most interesting)
    top_secs = sections.nlargest(top_n, "word_count").reset_index(drop=True)
    texts    = top_secs["section_text"].fillna("").tolist()
    titles   = [t[:25] + "…" if len(t) > 25 else t
                for t in top_secs["section_title"].tolist()]

    vec    = TfidfVectorizer(stop_words="english")
    X      = vec.fit_transform(texts)
    matrix = cosine_similarity(X)

    fig, ax = plt.subplots(figsize=(14, 12))
    im = ax.imshow(matrix, cmap="Blues", vmin=0, vmax=1, aspect="auto")
    plt.colorbar(im, ax=ax, shrink=0.8, label="Cosine Similarity")

    ax.set_xticks(range(len(titles)))
    ax.set_yticks(range(len(titles)))
    ax.set_xticklabels(titles, rotation=45, ha="right", fontsize=7)
    ax.set_yticklabels(titles, fontsize=7)

    # Annotate cells with values for top pairs
    for i in range(len(titles)):
        for j in range(len(titles)):
            if i != j and matrix[i, j] > 0.6:
                ax.text(j, i, f"{matrix[i,j]:.2f}",
                        ha="center", va="center", fontsize=5,
                        color="white" if matrix[i, j] > 0.8 else "black")

    ax.set_title(f"Section Cosine Similarity Heatmap (Top {top_n} sections by word count)",
                 fontsize=12, fontweight="bold", pad=12)
    fig.tight_layout()
    fig.savefig(out, dpi=_DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"[visualizer] Saved {out.name}")
    return out


# ---------------------------------------------------------------------------
# Chart 8 - Method usage (Advanced)
# ---------------------------------------------------------------------------

def plot_method_usage(code, out=CHART_METHOD_USAGE):
    """Grouped bar: count and percentage of code examples using each BS4 method."""
    method_cols   = ["contains_find_all", "contains_find", "contains_select",
                     "contains_get_text", "contains_requests"]
    method_labels = ["find_all()", "find()", "select()", "get_text()", "requests"]

    total  = len(code)
    counts = [int(code[c].astype(bool).sum()) for c in method_cols]
    pcts   = [c / total * 100 for c in counts]

    x   = np.arange(len(method_labels))
    fig, ax1 = plt.subplots(figsize=(10, 6))
    ax2 = ax1.twinx()

    bars = ax1.bar(x - 0.2, counts, width=0.35,
                   color=_PRIMARY, label="Count", edgecolor="white")
    ax2.bar(x + 0.2, pcts, width=0.35,
            color=_SECONDARY, alpha=0.8, label="% of total", edgecolor="white")

    for bar, count in zip(bars, counts):
        ax1.text(bar.get_x() + bar.get_width() / 2,
                 bar.get_height() + 0.3,
                 str(count), ha="center", va="bottom", fontsize=9, fontweight="bold")

    ax1.set_xlabel("BS4 Method", fontsize=11)
    ax1.set_ylabel("Number of Code Examples", fontsize=11, color=_PRIMARY)
    ax2.set_ylabel("% of All Code Examples", fontsize=11, color=_SECONDARY)
    ax1.set_xticks(x)
    ax1.set_xticklabels(method_labels, fontsize=11)
    ax1.set_title("BS4 Method Usage Across All Code Examples",
                  fontsize=13, fontweight="bold", pad=12)

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper right", fontsize=9)

    fig.tight_layout()
    fig.savefig(out, dpi=_DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"[visualizer] Saved {out.name}")
    return out


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    paths = plot_all()
    for p in paths:
        print(f"  → {p}")