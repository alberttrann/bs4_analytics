# BS4 Documentation Analytics — Work Division & Timeline

**Team:** Dat (B) · Phuc (C) · Duong (D) · Hung (A)  
**Stack:** FastAPI · Streamlit · BeautifulSoup4 · Pandas · NumPy · Matplotlib  
**Approach:** get the real pipeline running first, then build everything on top of real data.

---

## Members & Responsibilities

| Member | Core role | Pipeline | API route | App |
|--------|-----------|----------|-----------|-----|
| **Dat (B)** | Collector + API infra | `collector.py`, `parser.py` | `api/main.py`, `data_service.py`, `/sections` | — |
| **Phuc (C)** | Extractor + Frontend | `extractor.py`, `link_classifier.py` | `/links` | `app/main.py`, pages 1–3 |
| **Duong (D)** | Analyzer + Charts + Tests | `analyzer.py`, `visualizer.py` | `/analytics` | `tests/`, `config/` |
| **Hung (A)** | Orchestrator + Advanced | `code_extractor.py`, `reporter.py`, `pipeline.py`, `advanced/` | `/code`, `/pipeline`, advanced routes | pages 0, 4, 5, `components/` |

**Route ownership rule:** whoever writes the pipeline stage that produces a dataset also writes the API route that serves it. Dat owns the API infrastructure (`api/main.py`, `data_service.py`) but only the `/sections` route, not routes for data he never touched.

---

## Hung (A) — Day 1 priority

Before anyone else branches, Hung commits `shared/` to `main`. These three files are the contracts that every other file in the project depends on:

- `shared/schemas.py` — Pydantic models defining the shape of every data object: `SectionModel`, `LinkModel`, `CodeExampleModel`, `AnalyticsSummary`. If any file produces or consumes data, it imports from here.
- `shared/constants.py` — Every file path, URL, column name list, and link type enum in one place. No one hardcodes paths or column names anywhere else.
- `shared/utils.py` — Shared helpers: `ensure_dirs()` creates data/output folders, `load_sections()` / `load_links()` / `load_code_examples()` read the processed CSVs with a clear error message if the pipeline hasn't been run yet.

These files are already written and sitting in the repo. Hung just commits them. No one edits `shared/` without checking with Hung first.

---

## Dat (B) — Collector + Parser + API Infrastructure

### Pipeline

**`pipeline/collector.py`** (Feature 1)

Send an HTTP GET request to the BeautifulSoup documentation URL, check that the response status is 200, then save the raw HTML to `data/raw/beautifulsoup_doc.html`. This is the first thing that must exist before any other pipeline stage can run.

Key things to handle: call `ensure_dirs()` before writing, use `response.raise_for_status()` to automatically raise an error on any non-200 response, write the file with UTF-8 encoding.

**`pipeline/parser.py`** (Feature 2)

Load the saved HTML file from disk, create a BeautifulSoup object using `html.parser`, then implement `extract_section_tree()` — the function that walks every h1, h2, h3 heading in the document in order, collects all the content underneath each heading until the next heading of the same or higher level, and returns a list of dicts matching the columns defined in `SECTION_COLS`. Each dict must include the heading level (1/2/3), title, combined text, word count, count of code blocks, and count of links in that section.

This is the most algorithmically complex function in the whole codebase. The key insight: when you encounter a heading, iterate `.next_siblings` and stop when you hit another tag with a heading level equal to or lower than the current one.

### API

**`api/main.py`** — Dat sets this up but it belongs to the whole team. The file is already written and working. The only thing each person needs to do is uncomment their own `include_router()` line when their route file is ready.

**`api/services/data_service.py`** — A simple in-memory cache layer. Exposes `load_sections()`, `load_links()`, `load_code_examples()`, and `invalidate_cache()`. All route files import their data from here — no route file ever reads a CSV directly. Dat commits this early so everyone else can import from it.

**`api/routes/sections.py`** — Two endpoints: a paginated `GET /sections` that accepts `page` and `size` query params, and `GET /sections/{id}` that returns a single section or 404. Both read from `load_sections()` in `data_service.py`.

### Definition of done

- Running `python -m pipeline.collector` creates `data/raw/beautifulsoup_doc.html`
- Running `python -m pipeline.parser` prints the number of sections found
- Running `uvicorn api.main:app --reload` starts the server and `GET /health` returns 200
- `GET /sections` returns real section data after the pipeline has run
- `data_service.py` is committed so Phuc, Duong, and Hung can import from it immediately

---

## Phuc (C) — Extractor + Frontend

### Pipeline

**`pipeline/link_classifier.py`** (part of Feature 4)

A single pure function — `classify_link(href)` — that takes a raw href string and returns one of exactly five values: `internal_anchor`, `external_link`, `documentation_link`, `image_link`, or `empty_or_invalid`. No file I/O, no network calls, no dependencies on any other pipeline stage.

Classification order matters (first match wins): check for empty/invalid first, then image file extensions, then `#` anchor links, then links containing `crummy.com` (the documentation domain), then everything else is external. You can test this function immediately with a few print statements — no other code needs to exist yet.

**`pipeline/extractor.py`** (Features 3 and 4)

Calls Dat's `extract_section_tree()` to get the section list, wraps it into a DataFrame with the columns defined in `SECTION_COLS`, and writes `sections.csv`. Then iterates over every `<a>` tag in the soup, calls `classify_link()` on each href, figures out which section the link belongs to by walking up its parent elements to find the nearest heading, and writes the result to `links.csv`. Both files go into `data/processed/`.

This file depends on Dat's `parser.py` being merged. Write `link_classifier.py` first since it has zero dependencies.

### API

**`api/routes/links.py`** — Two endpoints: `GET /links` which accepts optional `link_type` and `section` filter params, and `GET /links/stats` which returns the count of each of the 5 link types. The stats endpoint is what feeds the pie chart in the Streamlit frontend.

### Frontend

**`app/main.py`** — The Streamlit entry point. Sets page config, renders the sidebar with navigation, checks whether the API is reachable, and displays a friendly warning if the pipeline hasn't been run yet. The API base URL is read from the `API_BASE_URL` environment variable, defaulting to `http://localhost:8000`.

**`app/pages/1_sections.py`** — Fetches section data from `GET /sections` and displays it as a searchable table. Each row is expandable to show the full section text.

**`app/pages/2_links.py`** — Fetches link type counts from `GET /links/stats` and shows a pie chart. Includes a dropdown to filter the full link table by type.

**`app/pages/3_code.py`** — Fetches code examples from `GET /code-examples` and displays each one with syntax highlighting via `st.code`. Includes checkboxes to filter by which BS4 method the example uses.

All pages call the API — they never read CSVs directly.

### Definition of done

- `classify_link()` returns the correct type for each of the 5 cases
- Running `python -m pipeline.extractor` writes both CSVs (after Dat's parser is merged)
- `links.csv` contains all 5 link types when run against the real document
- `streamlit run app/main.py` launches without errors
- Pages 1, 2, 3 display real data from the API

---

## Duong (D) — Analyzer + Charts + Tests

### Pipeline

**`pipeline/analyzer.py`** (Feature 6)

Reads all three processed CSVs and answers 10 analytical questions using Pandas and NumPy, then saves the results to `data/processed/summary_stats.json`. The 8 required questions are: total section count, highest word count section, section with most code examples, section with most links, top 10 keywords by frequency, link type counts, number of `find_all()` examples, number of `get_text()` examples. The 2 team-proposed additions are: average word count per section, and number of sections with zero code blocks.

The keyword extraction (Q5) is the most interesting one: join all section text, lowercase it, extract words of 4+ characters with a regex, filter out a stopword list (already defined in `shared/constants.py`), and return the top 10 by count.

**`pipeline/visualizer.py`** (Feature 7)

Creates 4 matplotlib charts and saves them as PNG files to `output/charts/`:
- A horizontal bar chart of the top 10 sections by word count, sorted descending
- A vertical bar chart of code example count per section
- A pie chart of link type distribution with 5 wedges and percentage labels
- A histogram of code example line counts, annotated with mean and median lines

### API

**`api/routes/analytics.py`** — Three endpoints: `GET /analytics/summary` which runs the full analyzer and returns an `AnalyticsSummary` object, `GET /analytics/charts` which returns a map of chart names to their static file URLs, and `GET /analytics/link-types` which returns the link type count breakdown.

### Tests

**`tests/test_pipeline_output.py`** — All tests run against the real data produced by the pipeline. There are no mock objects or fixture files. Tests are marked with a `@skip_if_no_data` decorator that checks whether the three processed CSVs exist — if not, they skip with a clear message saying to run the pipeline first. Once the pipeline has been run, all tests execute against real data.

Tests cover: correct column names in all three CSVs, non-empty row counts, valid section levels, all five link types present in `links.csv`, positive line counts in code examples, all 10 required keys in the analytics result, exactly 10 top keywords returned, all 4 chart PNGs existing, and the key API routes returning correct status codes and valid schemas.

### Config

**`config/settings.py`** — A Pydantic `BaseSettings` class that reads configuration from environment variables or a `.env` file. Fields: `api_host`, `api_port`, `log_level`, `api_base_url`, `skip_fetch`.

**`config/logging.py`** — Configures Python's logging module: colored console output in development, JSON-structured logs in production (controlled by `LOG_LEVEL`).

### Definition of done

- `python -m pipeline.analyzer` completes and prints all 10 answers to stdout
- `python -m pipeline.visualizer` saves 4 PNGs to `output/charts/`
- `GET /analytics/summary` returns valid JSON
- `pytest tests/ -v` skips cleanly before pipeline runs, passes after
- `config/settings.py` and `.env.example` committed

---

## Hung (A) — Orchestrator + Reporter + Advanced

### Core pipeline

**`pipeline/code_extractor.py`** (Feature 5)

Finds every `<div class="highlight">` block in the parsed soup, extracts the code text, counts non-empty lines, determines which section the block belongs to by walking up the DOM, and sets five boolean flags indicating whether the code uses `find_all()`, `find()`, `select()`, `get_text()`, or `requests`. Writes `code_examples.csv`.

**`pipeline/reporter.py`** (Feature 8)

Generates two output files. The PDF report (`output/report/final_report.pdf`) covers: dataset overview, scraping method, extracted data summary, all 10 analytics results, the 4 charts embedded inline, key findings, limitations, and conclusion. The Excel workbook (`output/report/summary_tables.xlsx`) has 5 sheets: Sections, Links, Code Examples, Analytics Summary, and Top Keywords.

**`pipeline/pipeline.py`** — The orchestrator. Runs all stages in the correct order: collect → parse → extract → analyze → visualize → report. Prints a progress line to stdout for each stage, including elapsed time. The `--skip-fetch` flag re-uses the cached HTML instead of hitting the network again, which is useful during development.

### Core API

**`api/routes/code.py`** — `GET /code-examples` with optional `method` filter (e.g. `?method=contains_find_all`) and `GET /code-examples/{id}` for a single example.

**`api/routes/pipeline.py`** — `POST /pipeline/run` triggers the full pipeline as a background task and returns 202 immediately. `GET /pipeline/status` returns whether the pipeline is currently running and when it last completed.

### Notebooks

**`notebooks/analysis.ipynb`** — The narrative Jupyter notebook that walks through all 10 analytics questions with code, output, and markdown explanations. This is one of the primary submission artifacts.

### Advanced layer (after all core features are green — Day 8)

All advanced work is in net-new files. Hung never edits files owned by Dat, Phuc, or Duong.

**`pipeline/advanced/nlp_analyzer.py`** — TF-IDF keyword ranking using scikit-learn (more precise than raw frequency), Flesch-Kincaid readability score per section using textstat, and spaCy NER to identify class and function names in section text.

**`pipeline/advanced/similarity.py`** — Builds a TF-IDF vector per section, computes pairwise cosine similarity, and returns the top N most similar section pairs. Used to populate the heatmap in `app/pages/4_analytics.py`.

**`pipeline/advanced/graph_builder.py`** — Builds a directed networkx graph where nodes are sections and edges are internal/documentation links between them. Exports as D3-compatible `{nodes, edges}` JSON for the `/graph` API endpoint.

**`api/routes/search.py`** — Full-text search across all three datasets. Accepts a query string `q` and an optional `target` param (`sections`, `links`, `code`, or `all`).

**`api/routes/graph.py`** — Returns the section-link network as D3-compatible JSON, consumed by the network graph widget in the frontend.

**`api/websocket.py`** — A WebSocket endpoint that spawns `pipeline/pipeline.py` as a subprocess and streams each stdout line back to the Streamlit frontend in real time, enabling the live progress bar.

**`app/pages/0_home.py`** — The home dashboard. Shows dataset health indicators (which CSVs exist), a "Run Pipeline" button that connects to the WebSocket and streams progress into a live progress bar, quick-stat metric cards, and the last pipeline run timestamp.

**`app/pages/4_analytics.py`** — Replaces the static chart images with interactive Plotly charts: a cosine similarity heatmap between sections, a TF-IDF keyword bar chart, a readability score distribution, and a grouped bar chart of method usage across code examples.

**`app/components/`** — Three reusable Streamlit components: `stat_cards.py` for the metric card row, `wordcloud_widget.py` for the TF-IDF weighted keyword cloud, and `network_graph.py` for the interactive pyvis section dependency graph.

**`docker/`** — Dockerfiles for the API and frontend containers, and a `docker-compose.yml` that brings both up together with shared `data/` and `output/` volume mounts.

**`.github/workflows/ci.yml`** — GitHub Actions CI: runs `pytest tests/` and `ruff check .` on every pull request to `main`.

### Definition of done

- `shared/` committed to `main` on Day 1
- `python -m pipeline.pipeline` completes all 6 stages end-to-end
- `output/report/final_report.pdf` opens correctly with all 8 required sections
- `output/report/summary_tables.xlsx` has 5 sheets
- `notebooks/analysis.ipynb` runs top-to-bottom with all 10 questions answered

---

## Timeline

**Day 1** — Hung commits `shared/` to `main`. Everyone clones the repo, installs dependencies, and confirms `from shared.schemas import SectionModel` works.

**Days 2–3** — Parallel sprint. Dat works on `collector.py` and `parser.py` — this is the team's critical path so Dat goes first. Phuc starts `link_classifier.py` immediately since it has no dependencies at all, then moves to `extractor.py` skeleton. Duong writes `config/settings.py`, `config/logging.py`, and begins `analyzer.py` and `visualizer.py` logic. Hung writes `code_extractor.py`, `pipeline.py`, and `reporter.py` skeleton.

**Day 4** — First full pipeline run milestone. Dat merges collector and parser. Everyone runs `python -m pipeline.pipeline`. All three CSVs appear in `data/processed/`. From this point on, all work happens against real data.

**Days 5–6** — Second sprint. Dat finishes `api/main.py`, `data_service.py`, and `routes/sections.py`. Phuc finalizes `extractor.py` against the real soup, builds `routes/links.py`, and completes Streamlit pages 1–3 against the running API. Duong completes `analyzer.py` with all 10 verified answers, `visualizer.py` producing all 4 charts, `routes/analytics.py`, and the full test file. Hung finishes `reporter.py` producing both output files, `routes/code.py` and `routes/pipeline.py`, and the analysis notebook.

**Day 7** — Integration checkpoint. `docker-compose up` brings both services online. All 5 Streamlit pages render with real data. All 4 charts are present. Both report files open correctly. `pytest tests/ -v` passes with zero failures.

**Day 8** — Advanced sprint (Hung only). All advanced pipeline, API, and frontend files.

**Day 9** — Polish and buffer. Cross-check all 8 features against the marking rubric. Fix chart formatting, label truncation, and layout issues. Duong finalizes test coverage. Hung writes the README. Feature freeze — bugfixes only from here.

**Day 10** — Submission. Clean run: delete `data/` and `output/`, run the full pipeline, verify all outputs exist, zip and submit.

---

## Dependency Chain

The only hard sequential dependency in the entire project is Dat's `parser.py`. Everything after the three CSVs exist is fully parallel.

```
Hung commits shared/ to main
        ↓
Dat: collector.py → parser.py       ← one hard step; Phuc and Hung partially blocked here
        ↓
Phuc: extractor.py → sections.csv + links.csv
Hung: code_extractor.py → code_examples.csv
        ↓  (Day 4 milestone — all three CSVs exist)
Duong: analyzer.py + visualizer.py        ← fully parallel from here
Phuc:  Streamlit pages 1–3
Hung:  reporter.py + notebook
        ↓
All: API routes + integration
        ↓
Hung: advanced layer (Day 8)
```

Phuc can start `link_classifier.py` on Day 1 since it has no dependencies. If Dat's parser is delayed past Day 3, Phuc and Hung write their extractor/code_extractor logic and verify it compiles, then do a final test run once the parser arrives. Duong can verify all Pandas logic in a scratch script with a manually constructed small DataFrame, then re-run against real CSVs on Day 4.

---

## Hard Blockers

| What | Who | Unblocks |
|------|-----|---------|
| `shared/` on `main` | Hung, Day 1 | Everyone branching |
| `collector.py` saves HTML | Dat | parser.py |
| `parser.py` works correctly | Dat | `extractor.py` (Phuc), `code_extractor.py` (Hung) |
| All 3 CSVs exist on disk | Dat + Phuc + Hung | Duong's analyzer, Streamlit pages, reporter |
| `data_service.py` committed | Dat | Phuc, Duong, Hung writing their route files |
| `api/main.py` running on :8000 | Dat | All Streamlit pages |

---

## Branch Strategy

Each member works on their own feature branch and opens a pull request to `main`. `main` must always be in a passing state — no direct commits.

| Branch name | Owner |
|-------------|-------|
| `feature/shared-contracts` | Hung — merge Day 1 before anyone else branches |
| `feature/collector-parser` | Dat |
| `feature/extractor-frontend` | Phuc |
| `feature/analyzer-qa` | Duong |
| `feature/reporter-orchestrator` | Hung |
| `feature/advanced-layer` | Hung — starts Day 8, never edits others' files |

Review rotation: Dat reviews Phuc → Phuc reviews Duong → Duong reviews Hung → Hung reviews Dat. Any change to `shared/` needs Hung's sign-off since it affects everyone.

---

## Quick-start

```bash
# Setup
git clone <repo-url> && cd bs4_analytics
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

# Run full pipeline (do this before anything else)
python -m pipeline.pipeline

# Start API (terminal 1)
uvicorn api.main:app --reload --port 8000

# Start frontend (terminal 2)
streamlit run app/main.py

# Run tests (after pipeline has been run)
pytest tests/ -v

# Re-run pipeline without re-fetching HTML
python -m pipeline.pipeline --skip-fetch

# Run everything with Docker
docker-compose -f docker/docker-compose.yml up --build
```