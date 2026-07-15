"""
api/routes/pipeline.py
POST /pipeline/run, GET /pipeline/status
"""

from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, BackgroundTasks
from shared.utils import utc_now_iso

router = APIRouter()
logger = logging.getLogger(__name__)

_state: dict = {
    "running":                   False,
    "current_stage":             "",
    "stages_done":               0,
    "total_stages":              7,
    "last_run":                  None,
    "last_run_duration_seconds": None,
}


@router.post("/run", status_code=202)
def run_pipeline(background_tasks: BackgroundTasks):
    if _state["running"]:
        return {"status": "already_running"}
    background_tasks.add_task(_run_pipeline_background)
    return {"status": "started"}


@router.get("/status")
def get_status():
    return _state


async def _run_pipeline_background() -> None:
    import time
    from api.services.data_service import invalidate_cache
    from pipeline.pipeline import (
        _stage_collect, _stage_parse, _stage_extract,
        _stage_analyze, _stage_visualize, _stage_report, _stage_advanced,
    )

    stage_fns = [
        ("Collecting HTML",    lambda: _stage_collect(False)),
        ("Parsing HTML",       _stage_parse),
        ("Extracting data",    _stage_extract),
        ("Running analytics",  _stage_analyze),
        ("Generating charts",  _stage_visualize),
        ("Generating report",  _stage_report),
        ("Advanced analytics", _stage_advanced),
    ]

    _state["running"]      = True
    _state["stages_done"]  = 0
    _state["current_stage"] = "Starting..."
    start = time.perf_counter()

    try:
        for label, fn in stage_fns:
            _state["current_stage"] = label
            await asyncio.to_thread(fn)
            _state["stages_done"] += 1
        invalidate_cache()
        _state["current_stage"] = "Complete"
    except Exception as exc:
        logger.exception("Pipeline failed: %s", exc)
        _state["current_stage"] = f"Error: {exc}"
    finally:
        _state["running"]                    = False
        _state["last_run"]                   = utc_now_iso()
        _state["last_run_duration_seconds"]  = round(time.perf_counter() - start, 2)