"""
api/main.py
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from shared.constants import CHARTS_DIR
from shared.utils import ensure_dirs


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_dirs()
    yield


app = FastAPI(
    title="BS4 Documentation Analytics API",
    description=(
        "REST API serving analytics extracted from the BeautifulSoup documentation. "
        "Run `python -m pipeline.pipeline` to generate all data files before querying."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount(
    "/static/charts",
    StaticFiles(directory=str(CHARTS_DIR)),
    name="charts",
)


from api.routes import sections        
from api.routes import links           
from api.routes import code            
from api.routes import analytics       
from api.routes import pipeline as pipeline_route  
from api.routes import search          
from api.routes import graph           

app.include_router(sections.router,          prefix="/sections",      tags=["sections"])
app.include_router(links.router,             prefix="/links",         tags=["links"])
app.include_router(code.router,              prefix="/code-examples", tags=["code"])
app.include_router(analytics.router,         prefix="/analytics",     tags=["analytics"])
app.include_router(pipeline_route.router,    prefix="/pipeline",      tags=["pipeline"])
app.include_router(search.router,            prefix="/search",        tags=["search"])
app.include_router(graph.router,             prefix="/graph",         tags=["graph"])

from api.websocket import pipeline_progress
app.add_api_websocket_route("/ws/pipeline-progress", pipeline_progress)


@app.get("/health", tags=["health"])
def health():
    """Always returns 200. Frontend uses this to check connectivity."""
    from shared.utils import data_files_status, pipeline_has_run
    return {
        "status": "ok",
        "pipeline_ever_run": pipeline_has_run(),
        "data_files_present": data_files_status(),
    }
