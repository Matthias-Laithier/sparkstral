# Sparkstral

A fullstack application with a React frontend, FastAPI backend, and a Mistral Workflows worker.

## Quick start

```bash
cp .env.example .env
make up
```

`make up` starts the stack in the background. Use `make logs` to follow container output.

- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- API docs: http://localhost:8000/docs
- PostgreSQL runs in Docker for the **web search cache** (the backend must have `DATABASE_URL` set, as in [`.env.example`](.env.example))

Stop the stack:

```bash
make down
```

## Local development (without Docker)

**Backend:**

```bash
cd backend
uv sync
uv run uvicorn src.main:app --reload
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

## Quality checks

Backend tests require **PostgreSQL** (same credentials as in [`.env.example`](.env.example), port `5432` on the host). For example:

```bash
docker compose up -d postgres
```

Then run `make test` (or `cd backend && uv run pytest`).

```bash
make format     # format backend + frontend
make lint       # lint backend + frontend
make typecheck  # type check backend + frontend
make test       # run backend + frontend tests
make check      # run all of the above
```

## Stack

| Layer    | Technology                        |
|----------|-----------------------------------|
| Frontend | React, TypeScript, Vite, Tailwind |
| Backend  | FastAPI, Python, uv               |
| Tooling  | Biome (frontend), Ruff + mypy (backend) |

## Environment variables

| Variable | Required | Description |
|---|---|---|
| `MISTRAL_API_KEY` | Yes | Mistral API key from [console.mistral.ai](https://console.mistral.ai) |
| `DATABASE_URL` | Yes (backend) | SQLAlchemy URL for PostgreSQL, e.g. `postgresql+psycopg://user:pass@host:5432/db` |
| `BACKEND_BASE_URL` | Yes (worker) | Base URL of the FastAPI backend; Serper web search cache calls use this. Compose sets `http://backend:8000`. |
| `DEPLOYMENT_NAME` | Yes | Workflow id: must match the worker registration and API `execute_workflow` |
| `WEB_SEARCH_PROVIDER` | No (worker) | Web search provider: `serper` (default, backend cache + Serper), `tavily` (Tavily SDK with advanced search depth), or `mistralai` (Mistral built-in `web_search`) |
| `SERPER_API_KEY` | Yes when `WEB_SEARCH_PROVIDER=serper` | Serper API key for web search on cache miss (stored rows come from the backend). Not required for `mistralai` or `tavily`. |
| `TAVILY_API_KEY` | Yes when `WEB_SEARCH_PROVIDER=tavily` | Tavily API key for SDK searches. Tavily results do not use the backend cache. |
| `WEB_SEARCH_MODEL` | Yes (worker) | Model for web-search research |
| `WEB_SEARCH_MAX_ROUNDS` | Yes when `WEB_SEARCH_PROVIDER=serper` or `tavily` | Max custom tool-call rounds per research step. The Mistral built-in provider uses the Conversations API instead. |
| `PAIN_POINT_PROFILER_AGENT_MODEL` | Yes (worker) | Model for structured pain points (`parse`) |
| `GENAI_USE_CASES_MODEL` | Yes (worker) | Model for structured GenAI use cases (`parse`) |
| `DEDUPLICATOR_AGENT_MODEL` | Yes (worker) | Model for structured use-case deduplication (`parse`) |
| `MARKDOWN_REPORTER_AGENT_MODEL` | Yes (worker) | Model for the direct client-ready markdown report writer (`parse`) |
| `LLM_MAX_TOKENS` | Yes (worker) | Max output tokens for every chat completion / parse call (e.g. `2048`) |
| `LLM_TEMPERATURE` | Yes (worker) | Temperature for web search and structured profile/pain `parse` calls (e.g. `0`) |
| `GENAI_USE_CASES_LLM_TEMPERATURE` | Yes (worker) | Temperature for GenAI use-case `parse` only (e.g. `1` for diversity) |

## Company description workflow

A Mistral Workflows worker that, given a company name, runs company resolution,
company research, pain-point analysis, use-case selection, and returns a client-ready
markdown report with the top 3 high-impact GenAI use cases. The frontend is a
simple output viewer for the workflow's raw text, JSON, and markdown results.

**Run everything** (worker + backend + frontend) with one command:

```bash
make up
```

The workflow worker, FastAPI backend, and React frontend all start together via Docker Compose.

**Trigger an execution** from the frontend at http://localhost:5173, or from [console.mistral.ai](https://console.mistral.ai) → Workflows → your `DEPLOYMENT_NAME` (e.g. `sparkstral`) → Start Workflow with input:

```json
{"company_name": "Mistral AI"}
```

Or programmatically (`workflow_identifier` must match `DEPLOYMENT_NAME` in `.env` and the registered worker workflow):

```python
import os

from mistralai.client import Mistral

client = Mistral(api_key="your_key")
execution = client.workflows.execute_workflow(
    workflow_identifier=os.environ["DEPLOYMENT_NAME"],
    input={"company_name": "Mistral AI"},
)
print(execution.model_dump_json(indent=2))
```

## Project structure

```
.
├── frontend/          React + TypeScript app
│   └── src/
│       ├── api/       Typed API client
│       └── App.tsx    Main component
├── backend/           FastAPI API (Mistral client; triggers workflows by `DEPLOYMENT_NAME`)
│   └── src/
│       ├── api/         Route handlers (e.g. Mistral workflow trigger + status)
│       ├── core/        Config (settings)
│       ├── schemas/     Pydantic models
│       └── main.py      App entry point
├── workflow_worker/   Mistral Workflows worker (registers workflow `name=DEPLOYMENT_NAME`)
│   └── src/             `python -m src.worker`
├── compose.yaml
├── Makefile
└── .env.example
```
