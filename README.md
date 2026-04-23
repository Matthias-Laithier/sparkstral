# Sparkstral

A simple fullstack application with a React frontend and FastAPI backend.

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

No variables are required for the base setup. See `.env.example` for the template.

## Project structure

```
.
├── frontend/          React + TypeScript app
│   └── src/
│       ├── api/       Typed API client
│       └── App.tsx    Main component
├── backend/           FastAPI app
│   └── src/
│       ├── api/       Route handlers
│       ├── schemas/   Pydantic models
│       └── main.py    App entry point
├── compose.yaml
├── Makefile
└── .env.example
```
