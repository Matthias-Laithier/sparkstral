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
| `COMPANY_PROFILER_SEARCH_MODEL` | Yes | Model for the web-search research phase of company profiling |
| `COMPANY_PROFILER_AGENT_MODEL` | Yes | Model for the structured `CompanyProfileOutput` parse phase |
| `DEPLOYMENT_NAME` | Yes | Stable identifier for this worker deployment (e.g. `sparkstral`) |

## Company description workflow

A Mistral Workflows worker that, given a company name, searches the web and returns a short description of what the company does.

**Run everything** (worker + backend + frontend) with one command:

```bash
make up
```

The workflow worker, FastAPI backend, and React frontend all start together via Docker Compose.

**Trigger an execution** from the frontend at http://localhost:5173, or from [console.mistral.ai](https://console.mistral.ai) → Workflows → `sparkstral` → Start Workflow with input:

```json
{"company_name": "Mistral AI"}
```

Or programmatically:

```python
from mistralai.client import Mistral

client = Mistral(api_key="your_key")
execution = client.workflows.execute_workflow(
    workflow_identifier="sparkstral",
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
├── backend/           FastAPI app + Mistral Workflows worker
│   └── src/
│       ├── api/         Route handlers
│       ├── core/        Config (settings)
│       ├── schemas/     Pydantic models
│       ├── workflow/    Mistral Workflows definitions (worker: `src.workflow.worker`)
│       └── main.py      App entry point
├── compose.yaml
├── Makefile
└── .env.example
```
