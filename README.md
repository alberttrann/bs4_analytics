# BeautifulSoup Documentation Analytics

End-to-end data engineering and analytics pipeline that collects, parses, analyses, and visualises the official [BeautifulSoup 4 documentation](https://www.crummy.com/software/BeautifulSoup/bs4/doc/).

**Stack:** Python 3.11–3.13 · FastAPI · Streamlit · BeautifulSoup4 · Pandas · NumPy · Matplotlib · scikit-learn · NLTK

---

## Table of Contents

1. [Overview](#1-overview)
2. [Team](#2-team)
3. [Architecture](#3-architecture)
4. [Repository Structure](#4-repository-structure)
5. [Pipeline](#5-pipeline)
6. [Analytics](#6-analytics)
7. [API](#7-api)
8. [Streamlit App](#8-streamlit-app)
9. [Tests](#9-tests)
10. [Configuration](#10-configuration)
11. [Quick Start](#11-quick-start)
12. [Limitations](#12-limitations)

---

## 1. Overview

The system:

1. **Collects** the BS4 docs via HTTP
2. **Parses** HTML into a structured section tree (BeautifulSoup4)
3. **Extracts** three datasets: sections, links, and code examples
4. **Analyses** 10 core questions plus advanced NLP metrics
5. **Visualises** results with 8 charts (4 required + 4 NLP)
6. **Reports** findings as Markdown and a 5-sheet Excel workbook
7. **Serves** data through a FastAPI REST API (20+ endpoints)
8. **Presents** findings in a 7-page Streamlit dashboard

Each pipeline stage is independently runnable, testable, and maintainable.

---

## 2. Team

| Member | Pipeline | API | Frontend | Features |
|--------|----------|-----|----------|----------|
| **Dat (B)** | `collector.py`, `parser.py` | `main.py`, `data_service.py`, `/sections` | — | F1, F2 |
| **Phuc (C)** | `extractor.py`, `link_classifier.py` | `/links` | `main.py`, pages 1–3 | F3, F4 |
| **Duong (D)** | `analyzer.py`, `visualizer.py` | `/analytics` | `tests/`, `config/` | F6, F7 |
| **Hung (A)** | `code_extractor.py`, `reporter.py`, `pipeline.py`, `advanced/` | `/code`, `/pipeline`, `/search`, `/graph` | pages 0, 4, 5, `components/` | F5, F8 + advanced |

Shared contracts (`shared/schemas.py`, `shared/constants.py`, `shared/utils.py`) define Pydantic models, paths, and column names. All modules import from these — nothing is hardcoded elsewhere.

---

## 3. Architecture

```
Web (BS4 docs)
      │
      ▼
 pipeline/  ──►  data/processed/*.csv + output/
      │
      ▼
 api/ (FastAPI :8001)  ──►  app/ (Streamlit :8501)
```

**Why FastAPI + Streamlit**

- Clear separation: pipeline writes CSVs → API serves them → UI consumes the API
- Swagger UI at `/docs` with no extra work
- Pipeline and API are independently testable

**Pipeline flow**

```
collector → parser → extractor + code_extractor → analyzer → visualizer → reporter
                                                                      (+ advanced NLP)
```

Progress is streamed over WebSocket (`WS /ws/pipeline-progress`), with HTTP polling (`GET /pipeline/status`) as a fallback. Use `--skip-fetch` to reuse cached HTML during development.

---

## 4. Repository Structure

```
bs4_analytics/
├── shared/                 # Schemas, constants, shared helpers
├── pipeline/               # ETL stages (one module per stage)
│   └── advanced/           # TF-IDF, readability, similarity, graph
├── api/                    # FastAPI backend (port 8001)
│   ├── routes/
│   ├── services/
│   └── websocket.py
├── app/                    # Streamlit frontend (port 8501)
│   ├── pages/
│   └── components/
├── tests/
├── config/                 # Settings & logging
├── notebooks/
│   └── BeautifulSoup_Documentation_Analytics.ipynb
├── data/                   # Generated (raw HTML + processed CSVs)
├── output/                 # Generated (charts + reports)
├── docker/
├── .github/workflows/ci.yml
├── requirements.txt
└── .env.example
```

---

## 5. Pipeline

| Stage | Module | Feature | Output |
|-------|--------|---------|--------|
| 1 | `collector.py` | F1 | `data/raw/beautifulsoup_doc.html` |
| 2 | `parser.py` | F2 | Section tree (in-memory) |
| 3 | `extractor.py` + `link_classifier.py` | F3, F4 | `sections.csv`, `links.csv` |
| 4 | `code_extractor.py` | F5 | `code_examples.csv` |
| 5 | `analyzer.py` | F6 | `summary_stats.json` |
| 6 | `visualizer.py` | F7 | 8 PNGs in `output/charts/` |
| 7 | `reporter.py` | F8 | `final_report.md`, `summary_tables.xlsx` |

**Link types** (priority order): `empty_or_invalid` → `image_link` → `internal_anchor` → `documentation_link` → `external_link`

**Code example flags:** `contains_find_all`, `contains_find`, `contains_select`, `contains_get_text`, `contains_requests`

### Advanced NLP (`pipeline/advanced/`)

| Module | Technique | Output |
|--------|-----------|--------|
| `nlp_analyzer.py` | TF-IDF keywords, Flesch readability | `adv_*` fields in summary |
| `similarity.py` | Cosine similarity between sections | Top similar pairs + heatmap |
| `graph_builder.py` | networkx section-link graph | D3 JSON via `GET /graph` |

---

## 6. Analytics

Representative results from a full pipeline run:

| # | Question | Result |
|---|----------|--------|
| Q1 | Total sections | 113 |
| Q2 | Highest word count | "Searching the tree" (4,711) |
| Q3 | Most code examples | "Multi-valued attributes" (13) |
| Q4 | Most links | "Table of Contents" (128) |
| Q5 | Top keywords | soup, tag, class, html, example, … |
| Q6 | Link types | internal_anchor 91.0%, external 5.6%, … |
| Q7 | `find_all()` examples | 41 / 220 |
| Q8 | `get_text()` examples | 4 / 220 |
| Q9 | Avg words/section | 363.28 |
| Q10 | Sections with no code | 22 |
| ADV | Mean Flesch score | 56.0 (Standard) |
| ADV | Top TF-IDF term | `tag` |
| ADV | Most similar pair | Low-level search ↔ Custom element filtering |

**Charts:** word count, code by section, link-type pie, line-count histogram, TF-IDF vs frequency, readability, similarity heatmap, method usage.

---

## 7. API

**Base URL:** `http://localhost:8001`  
**Swagger:** `http://localhost:8001/docs`

| Prefix | Endpoints | Owner |
|--------|-----------|-------|
| `/sections` | List (paginated), get by ID | Dat |
| `/links` | List (filtered), `/stats` | Phuc |
| `/code-examples` | List (method/section filter), get by ID | Hung |
| `/analytics` | `/summary`, `/charts`, `/link-types` | Duong |
| `/pipeline` | `POST /run`, `GET /status` | Hung |
| `/search` | Fuzzy query across targets | Hung |
| `/graph` | Section dependency graph (D3 JSON) | Hung |

Static charts: `/static/charts/{filename}.png`

---

## 8. Streamlit App

| Page | File | Description |
|------|------|-------------|
| Home | `0_home.py` | Pipeline trigger, progress, health metrics |
| Sections | `1_sections.py` | Fuzzy search (rapidfuzz) |
| Links | `2_links.py` | Link explorer + type distribution |
| Code | `3_code.py` | Code browser with method filters |
| Analytics | `4_analytics.py` | 8-tab Plotly dashboard |
| Report | `5_report.py` | Download MD, XLSX, chart PNGs |

---

## 9. Tests

**120 test cases** across 7 files:

| File | Count | Strategy |
|------|------:|----------|
| `test_collector.py` | 6 | Mocked HTTP |
| `test_parser.py` | 9 | Inline HTML fixture |
| `test_link_classifier.py` | 25 | Parametrized href cases |
| `test_extractor.py` | 12 | Fixture + path monkeypatch |
| `test_analyzer.py` | 12 | Synthetic DataFrames |
| `test_api_routes.py` | 28 | TestClient + cache fixture |
| `test_pipeline_output.py` | 28 | Real data (`@skip_if_no_data`) |

```bash
pytest tests/ -v
pytest tests/ -v -k "not pipeline_output"          # offline only
pytest tests/ -v --cov=pipeline --cov=api --cov-report=term-missing
```

---

## 10. Configuration

Copy `.env.example` → `.env`:

```ini
API_HOST=0.0.0.0
API_PORT=8001
LOG_LEVEL=INFO
API_BASE_URL=http://localhost:8001
SKIP_FETCH=false
```

`config/settings.py` uses `pydantic-settings`. Streamlit reads `.env` via `app/config.py`.

---

## 11. Quick Start

### Prerequisites

- Python 3.11–3.13
- Ports 8001 (API) and 8501 (Streamlit) available

### Setup

```bash
git clone <repo-url>
cd bs4_analytics

python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux

pip install -r requirements.txt

copy .env.example .env          # Windows
# cp .env.example .env          # macOS/Linux
```

### Run

```bash
# Full pipeline
python -m pipeline.pipeline

# Re-run without re-downloading HTML
python -m pipeline.pipeline --skip-fetch

# API (terminal 1)
uvicorn api.main:app --reload --port 8001

# Streamlit (terminal 2)
streamlit run app/main.py
```

| Service | URL |
|---------|-----|
| API / Swagger | http://localhost:8001/docs |
| Streamlit | http://localhost:8501 |

### Individual stages

```bash
python -m pipeline.collector
python -m pipeline.parser
python -m pipeline.extractor
python -m pipeline.code_extractor
python -m pipeline.analyzer
python -m pipeline.visualizer
python -m pipeline.reporter
```

### Docker

```bash
docker-compose -f docker/docker-compose.yml up --build
```

> Docker maps the API to port **8000** by default. Adjust `.env` / compose ports if needed.

---

## 12. Limitations

| ID | Limitation |
|----|------------|
| L1 | Content before the first heading is attributed to `"Unknown"` |
| L2 | Example data (e.g. "sister") inflates raw keyword counts; TF-IDF partially mitigates this |
| L3 | Readability scores include code tokens, which deflate Flesch scores |
| L4 | Section graph has few edges due to imperfect slug→title matching |
| L5 | Analysis covers English BS4 docs only, at scrape time |
| L6 | In-memory API cache must be invalidated after pipeline runs (handled in production path) |

---

## License

Academic project — FPT University, course PDS301m.
