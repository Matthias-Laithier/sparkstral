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
| `DEPLOYMENT_NAME` | Yes | Workflow id: must match the worker registration and API `execute_workflow` |
| `SERPER_API_KEY` | Yes (worker) | Serper API key for web search in research activities |
| `WEB_SEARCH_MODEL` | Yes (worker) | Model for the web-search tool loop |
| `WEB_SEARCH_MAX_ROUNDS` | Yes (worker) | Max tool-call rounds per research step |
| `COMPANY_PROFILER_AGENT_MODEL` | Yes (worker) | Model for structured company profile (`parse`) |
| `PAIN_POINT_PROFILER_AGENT_MODEL` | Yes (worker) | Model for structured pain points (`parse`) |
| `GENAI_USE_CASES_MODEL` | Yes (worker) | Model for structured GenAI use cases (`parse`) |
| `LLM_MAX_TOKENS` | Yes (worker) | Max output tokens for every chat completion / parse call (e.g. `2048`) |
| `LLM_TEMPERATURE` | Yes (worker) | Temperature for web search and structured profile/pain `parse` calls (e.g. `0`) |
| `GENAI_USE_CASES_LLM_TEMPERATURE` | Yes (worker) | Temperature for GenAI use-case `parse` only (e.g. `1` for diversity) |

## Company description workflow

A Mistral Workflows worker that, given a company name, runs company research and profiling, a pain-point pass, then a GenAI use-case ideation step—ordered steps in the UI.

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
