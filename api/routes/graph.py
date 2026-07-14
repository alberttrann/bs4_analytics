"""
api/routes/graph.py
Advanced - GET /graph → D3-compatible {nodes, edges} section network JSON.
"""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/", summary="Section-link network graph")
def get_graph():
    """
    Return the documentation section-link network as D3-compatible JSON.
    Nodes are sections; edges are internal/documentation links between them.
    Consumed by app/components/network_graph.py.
    """
    from pipeline.advanced.graph_builder import build_graph
    from shared.utils import load_links, load_sections

    return build_graph(load_sections(), load_links())
