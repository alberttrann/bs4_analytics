"""
pipeline/advanced/graph_builder.py
Owner: Hung (A)
Advanced — builds a directed section-link network as a networkx DiGraph
           and exports it as D3-compatible JSON for the /graph API endpoint.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


def build_graph(sections: pd.DataFrame, links: pd.DataFrame) -> dict:
    """
    Build a {nodes, edges} dict from sections and internal/documentation links.

    Nodes : one per section — id, level, word_count attributes
    Edges : one per internal_anchor or documentation_link that resolves
            to a known section title

    Returns
    -------
    dict  {"nodes": [...], "edges": [...]}
    """
    import networkx as nx
    from shared.constants import LINK_TYPE_INTERNAL_ANCHOR, LINK_TYPE_DOCUMENTATION

    G = nx.DiGraph()

    for _, row in sections.iterrows():
        G.add_node(
            row["section_title"],
            level=int(row["section_level"]),
            word_count=int(row["word_count"]),
        )

    known_titles = set(sections["section_title"].tolist())
    internal_links = links[
        links["link_type"].isin([LINK_TYPE_INTERNAL_ANCHOR, LINK_TYPE_DOCUMENTATION])
    ]

    for _, row in internal_links.iterrows():
        source = row["section_title"]
        target = _resolve_href(row["href"], known_titles)
        if target and source in G and target in G and source != target:
            G.add_edge(source, target, link_type=row["link_type"])

    nodes = [{"id": n, **G.nodes[n]} for n in G.nodes]
    edges = [{"source": u, "target": v, **G.edges[u, v]} for u, v in G.edges]

    logger.info("Graph: %d nodes, %d edges", len(nodes), len(edges))
    return {"nodes": nodes, "edges": edges}


def _resolve_href(href: str, known_titles: set[str]) -> str | None:
    """
    Attempt to map an anchor href (e.g. '#quick-start') to a section title.
    Returns None if no match found.
    """
    if not href or not href.startswith("#"):
        return None
    slug = href.lstrip("#").lower().replace("-", " ")
    for title in known_titles:
        if title.lower() == slug or slug in title.lower():
            return title
    return None


def save_graph_json(graph: dict, dest: Path) -> Path:
    """Serialise graph dict to a JSON file. Returns dest."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(graph, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("Graph JSON saved → %s (%d nodes, %d edges)",
                dest.name, len(graph["nodes"]), len(graph["edges"]))
    return dest
