"""
api/main.py
Owner: ALL MEMBERS
Task : Uncomment router once route file is ready.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from shared.constants import CHARTS_DIR
from shared.utils import ensure_dirs


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_dirs()
    yield


app = FastAPI(title="BS4 Documentation Analytics API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static/charts", StaticFiles(directory=str(CHARTS_DIR)), name="charts")

# Router wiring - mọi người tự uncomment lúc route file ok nhá

from api.routes import sections     # Dat
from api.routes import links        # Phuc
# from api.routes import code         # Hung
# from api.routes import analytics    # Duong
from api.routes import pipeline     # Hung
from api.routes import search       # Hung 
from api.routes import graph        # Hung 

# app.include_router(sections.router,  prefix="/sections",      tags=["sections"])
# app.include_router(links.router,     prefix="/links",         tags=["links"])
app.include_router(code.router,      prefix="/code-examples", tags=["code"])
app.include_router(sections.router,  prefix="/sections",      tags=["sections"])
app.include_router(links.router,     prefix="/links",         tags=["links"])
# app.include_router(code.router,      prefix="/code-examples", tags=["code"])
# app.include_router(analytics.router, prefix="/analytics",     tags=["analytics"])
app.include_router(pipeline.router,  prefix="/pipeline",      tags=["pipeline"])
app.include_router(search.router,    prefix="/search",        tags=["search"])
app.include_router(graph.router,     prefix="/graph",         tags=["graph"])


@app.get("/health", tags=["health"])
def health():
    from shared.utils import pipeline_has_run, data_files_status
    return {
        "status": "ok",
        "pipeline_ever_run": pipeline_has_run(),
        "data_files_present": data_files_status(),
    }
