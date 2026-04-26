# Sparkstral

A Mistral Workflows worker that researches a company and returns a client-ready GenAI opportunity report. Run it with Docker Compose or locally; trigger workflows from [Le Chat](https://chat.mistral.ai) or the Mistral Console after publishing your deployment.

## Quick start

```bash
cp .env.example .env
make up
```

`make up` builds and starts the workflow worker in the background. Use `make logs` to follow container output.

Stop the stack:

```bash
make down
```

## Local development (without Docker)

```bash
cd workflow_worker
uv sync
uv run python -m src.worker
```

Ensure `.env` in the repo root (or current working directory) contains the variables from `.env.example`.

## Quality checks

```bash
make format     # format workflow_worker
make lint       # lint workflow_worker
make typecheck  # type check workflow_worker
make test       # run workflow_worker tests
make check      # run all of the above
```

## Stack

| Layer   | Technology                          |
|---------|-------------------------------------|
| Worker  | Python 3.13, Mistral Workflows, uv |
| Tooling | Ruff + mypy                         |

## Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `MISTRAL_API_KEY` | Yes | Mistral API key from [console.mistral.ai](https://console.mistral.ai) |
| `DEPLOYMENT_NAME` | Yes | Workflow id: must match the worker registration and Mistral workflow name |
| `WEB_SEARCH_PROVIDER` | No | `serper` (Serper Google search API), `tavily` (Tavily SDK), or `mistralai` (Mistral built-in `web_search`) |
| `SERPER_API_KEY` | Yes when `WEB_SEARCH_PROVIDER=serper` | Serper API key |
| `TAVILY_API_KEY` | Yes when `WEB_SEARCH_PROVIDER=tavily` | Tavily API key |
| `WEB_SEARCH_MODEL` | Yes | Model for web-search research (when using custom tool or Mistral search path) |
| `WEB_SEARCH_MAX_ROUNDS` | Yes when `WEB_SEARCH_PROVIDER=serper` or `tavily` | Max tool-call rounds per research step |
| `COMPANY_RESOLVER_AGENT_MODEL` | Yes | Model for company resolution |
| `GENAI_USE_CASES_MODEL` | Yes | Model for structured GenAI use-case generation |
| `USE_CASE_GRADER_AGENT_MODEL` | Yes | Model for scoring use cases |
| `MARKDOWN_REPORTER_AGENT_MODEL` | Yes | Model for the markdown report |
| `LLM_MAX_TOKENS` | Yes | Max output tokens for chat / parse calls |
| `LLM_TEMPERATURE` | Yes | Temperature for web search and structured profile calls |
| `GENAI_USE_CASES_LLM_TEMPERATURE` | Yes | Temperature for GenAI use-case generation only |

## Company description workflow

Given a company name, the worker runs company resolution, web research, GenAI use-case generation and scoring, and returns a markdown report with the top high-impact GenAI use cases.

**Trigger from Le Chat or Mistral Console** after publishing the workflow whose name matches `DEPLOYMENT_NAME` (e.g. `sparkstral`). Start with input:

```json
{"company_name": "Mistral AI"}
```

The registered workflow returns a `ChatAssistantWorkflowOutput`, compatible with Le Chat publishing.

Or programmatically (`workflow_identifier` must match `DEPLOYMENT_NAME`):

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
├── workflow_worker/   Mistral Workflows worker (registers workflow name=DEPLOYMENT_NAME)
│   └── src/           `python -m src.worker`
├── compose.yaml
├── Makefile
└── .env.example
```
