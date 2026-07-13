"""
app/components/network_graph.py
Owner: Hung (A)
Advanced — interactive pyvis section dependency graph.
Fetches {nodes, edges} from GET /graph and renders in Streamlit.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import requests
import streamlit as st
import streamlit.components.v1 as components

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")


def render_network_graph(height: int = 620) -> None:
    """
    Fetch the section-link graph from the API and render it as an
    interactive pyvis network embedded in the Streamlit page.
    """
    try:
        from pyvis.network import Network
    except ImportError:
        st.warning("pyvis not installed. Run: pip install pyvis")
        return

    try:
        graph = requests.get(f"{API_BASE}/graph", timeout=15).json()
    except Exception as e:
        st.error(f"Cannot load graph data: {e}")
        return

    if not graph.get("nodes"):
        st.info("No graph data — run the pipeline first.")
        return

    net = Network(
        height=f"{height}px",
        width="100%",
        directed=True,
        bgcolor="#ffffff",
        font_color="#333333",
    )
    net.set_options("""
    {
      "nodes": {"shape": "dot", "scaling": {"min": 10, "max": 30}},
      "edges": {"arrows": "to", "smooth": {"type": "curvedCW", "roundness": 0.2}},
      "physics": {"enabled": true, "stabilization": {"iterations": 100}}
    }
    """)

    for node in graph["nodes"]:
        size  = max(10, node.get("word_count", 100) // 60)
        level = node.get("level", 1)
        color = {1: "#4C72B0", 2: "#55A868", 3: "#C44E52"}.get(level, "#4C72B0")
        net.add_node(
            node["id"],
            label=node["id"][:25] + ("…" if len(node["id"]) > 25 else ""),
            title=f"{node['id']}\nLevel: {level} | Words: {node.get('word_count','?')}",
            size=size,
            color=color,
        )

    for edge in graph["edges"]:
        net.add_edge(edge["source"], edge["target"])

    with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w") as tmp:
        net.save_graph(tmp.name)
        html_content = Path(tmp.name).read_text(encoding="utf-8")

    components.html(html_content, height=height + 50, scrolling=False)
