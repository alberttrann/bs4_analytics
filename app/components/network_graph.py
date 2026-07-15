"""
app/components/network_graph.py
Advanced - interactive pyvis section dependency graph.
Fetches {nodes, edges} from GET /graph and renders in Streamlit.
"""
from __future__ import annotations
import sys
from pathlib import Path
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import os
import tempfile
from pathlib import Path

import requests
import streamlit as st
import streamlit.components.v1 as components

from app.config import API_BASE, WS_BASE


def render_network_graph(height: int = 900) -> None:
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
        st.info("No graph data - run the pipeline first.")
        return

    net = Network(
        height=f"{height}px",
        width="100%",
        directed=True,
        bgcolor="#1a1a2e",
        font_color="#ffffff",
    )

    # Physics - spread nodes out so they don't squash together
    net.set_options("""
    {
      "physics": {
        "enabled": true,
        "forceAtlas2Based": {
          "gravitationalConstant": -80,
          "centralGravity": 0.005,
          "springLength": 200,
          "springConstant": 0.08,
          "damping": 0.4,
          "avoidOverlap": 1
        },
        "maxVelocity": 50,
        "minVelocity": 0.1,
        "solver": "forceAtlas2Based",
        "stabilization": {
          "enabled": true,
          "iterations": 200,
          "updateInterval": 25
        }
      },
      "nodes": {
        "shape": "dot",
        "scaling": { "min": 10, "max": 35 },
        "font": { "size": 11, "face": "Arial" }
      },
      "edges": {
        "arrows": "to",
        "color": { "opacity": 0.5 },
        "smooth": { "type": "dynamic" },
        "width": 0.8
      },
      "interaction": {
        "hover": true,
        "navigationButtons": true,
        "keyboard": true,
        "zoomView": true
      }
    }
    """)

    for node in graph["nodes"]:
        size  = max(10, node.get("word_count", 100) // 50)
        level = node.get("level", 1)
        color = {1: "#e94560", 2: "#0f3460", 3: "#16213e"}.get(level, "#0f3460")
        label = node["id"]
        net.add_node(
            node["id"],
            label=label[:20] + ("…" if len(label) > 20 else ""),
            title=f"{node['id']}\nLevel: H{level} | Words: {node.get('word_count','?')}",
            size=size,
            color=color,
        )

    for edge in graph["edges"]:
        net.add_edge(edge["source"], edge["target"], color="#ffffff30")

    with tempfile.NamedTemporaryFile(suffix=".html", delete=False,
                                     mode="w", encoding="utf-8") as tmp:
        net.save_graph(tmp.name)
        html_content = Path(tmp.name).read_text(encoding="utf-8")

    # Make it fill the container properly
    html_content = html_content.replace(
        'style="width: 100%;height: 900px"',
        'style="width: 100%; height: 900px; border: none;"'
    )

    components.html(html_content, height=920, scrolling=False)