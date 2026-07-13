"""
api/routes/pipeline.py
Owner: Hung (A)
POST /pipeline/run  — trigger full pipeline as background task
GET  /pipeline/status — check running state and last run time
"""

from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, BackgroundTasks

from shared.schemas import PipelineStatus
from shared.utils import utc_now_iso

router = APIRouter()
logger = logging.getLogger(__name__)

# In-memory state — sufficient for single-server dev/demo use
_state: dict = {
    "running": False,
    "last_run": None,
    "last_run_duration_seconds": None,
}


@router.post("/run", status_code=202, summary="Trigger the full ETL pipeline")
def run_pipeline(background_tasks: BackgroundTasks):
    """
    Start the pipeline in a background task and return 202 immediately.
    Monitor progress via GET /pipeline/status or connect to
    WS /ws/pipeline-progress for live stdout streaming.
    """
    if _state["running"]:
        return {"status": "already_running", "message": "Pipeline is already in progress."}

    background_tasks.add_task(_run_pipeline_background)
    return {"status": "started"}


@router.get("/status", response_model=PipelineStatus, summary="Pipeline run status")
def get_status():
    """Return whether the pipeline is currently running and when it last completed."""
    return PipelineStatus(**_state)


async def _run_pipeline_background() -> None:
    """Async wrapper that runs pipeline.run_all() in a thread pool."""
    import time
    from pipeline.pipeline import run_all
    from api.services.data_service import invalidate_cache

    _state["running"] = True
    start = time.perf_counter()
    try:
        await asyncio.to_thread(run_all)
        invalidate_cache()   # force routes to reload fresh CSVs
        logger.info("Pipeline completed successfully")
    except Exception as exc:
        logger.exception("Pipeline failed: %s", exc)
    finally:
        _state["running"] = False
        _state["last_run"] = utc_now_iso()
        _state["last_run_duration_seconds"] = round(time.perf_counter() - start, 2)
