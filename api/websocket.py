"""
api/websocket.py
Owner: Hung (A)
Advanced — WebSocket endpoint that streams pipeline stdout to the Streamlit
           frontend in real time, powering the live progress bar on the home page.

Register in api/main.py:
    from api.websocket import pipeline_progress
    app.add_websocket_route("/ws/pipeline-progress", pipeline_progress)
"""

from __future__ import annotations

import asyncio
import logging

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


async def pipeline_progress(websocket: WebSocket) -> None:
    """
    Accept a WebSocket connection, spawn pipeline/pipeline.py as a subprocess,
    and forward each stdout line to the client until the process exits.

    Client (app/pages/0_home.py) connects with:
        ws = websocket.create_connection("ws://localhost:8000/ws/pipeline-progress")

    Protocol:
        Server → Client : plain-text lines, one per pipeline stage
        Client → Server : nothing (read-only stream)
        Connection closes when pipeline finishes or client disconnects.
    """
    await websocket.accept()
    logger.info("WebSocket client connected for pipeline progress")

    process = await asyncio.create_subprocess_exec(
        "python", "-m", "pipeline.pipeline",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )

    try:
        assert process.stdout is not None
        async for raw_line in process.stdout:
            line = raw_line.decode("utf-8", errors="replace").strip()
            if line:
                await websocket.send_text(line)
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected — terminating pipeline")
        process.terminate()
    except Exception as exc:
        logger.exception("WebSocket error: %s", exc)
    finally:
        await process.wait()
        try:
            await websocket.close()
        except Exception:
            pass
        logger.info("WebSocket connection closed")
