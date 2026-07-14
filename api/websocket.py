"""
api/websocket.py
WebSocket endpoint - streams pipeline stdout to Streamlit in real time.
Registered in api/main.py as:
    app.add_api_websocket_route("/ws/pipeline-progress", pipeline_progress)
"""

from __future__ import annotations

import asyncio
import logging
import sys

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

# Suppress the cosmetic Windows ProactorEventLoop noise
_WINDOWS = sys.platform == "win32"


async def pipeline_progress(websocket: WebSocket) -> None:
    """
    Accept a WebSocket connection, spawn pipeline.pipeline as a subprocess,
    and forward each stdout line to the client until the process exits or
    the client disconnects.

    Windows note: ConnectionResetError [WinError 10054] is raised when the
    client disconnects while the subprocess is still writing. This is cosmetic
    and is caught silently below.
    """
    await websocket.accept()
    logger.info("WebSocket client connected")

    process = await asyncio.create_subprocess_exec(
        sys.executable, "-m", "pipeline.pipeline",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )

    try:
        assert process.stdout is not None
        async for raw_line in process.stdout:
            line = raw_line.decode("utf-8", errors="replace").strip()
            if line:
                try:
                    await websocket.send_text(line)
                except (WebSocketDisconnect, RuntimeError):
                    # Client disconnected mid-stream - terminate pipeline
                    logger.info("Client disconnected during pipeline stream")
                    process.terminate()
                    return

    except (WebSocketDisconnect, RuntimeError):
        logger.info("WebSocket disconnected")
        process.terminate()

    except ConnectionResetError:
        # Windows: [WinError 10054] - client closed connection abruptly.
        # This is harmless; pipeline may still be running.
        logger.debug("ConnectionResetError suppressed (Windows cosmetic)")
        process.terminate()

    except Exception as exc:
        logger.exception("WebSocket stream error: %s", exc)
        try:
            await websocket.send_text(f"[pipeline] ERROR: {exc}")
        except Exception:
            pass
        process.terminate()

    finally:
        # Ensure process is reaped even if we exit early
        try:
            await asyncio.wait_for(process.wait(), timeout=5.0)
        except asyncio.TimeoutError:
            process.kill()

        try:
            await websocket.close()
        except Exception:
            pass

        logger.info("WebSocket connection closed")