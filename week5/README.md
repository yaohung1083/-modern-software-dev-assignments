# Week 5

Minimal full‑stack starter for experimenting with autonomous coding agents.

Starter and assignment source: [CS146S: The Modern Software Developer](../README.md), from the [original course repository](https://github.com/mihail911/modern-software-dev-assignments). Original course attribution is retained; the additions below document an independent Codex self-study exercise.

- FastAPI backend with SQLite (SQLAlchemy)
- Static frontend (no Node toolchain needed)
- Minimal tests (pytest)
- Pre-commit (black + ruff)
- Tasks to practice agent-driven workflows

## Quickstart

1) Create and activate a virtualenv, then install dependencies

```bash
cd modern-software-dev-assignments
python -m venv .venv && source .venv/bin/activate
pip install -e .[dev]
```

2) (Optional) Install pre-commit hooks

```bash
pre-commit install
```

3) Run the app (from `week5/`)

```bash
cd week5 && make run
```

Open `http://localhost:8000` for the frontend and `http://localhost:8000/docs` for the API docs.

## Structure

```
backend/                # FastAPI app
frontend/               # Static UI served by FastAPI
data/                   # SQLite DB + seed
docs/                   # TASKS for agent-driven workflows
```

## Tests

```bash
cd week5 && make test
```

## Formatting/Linting

```bash
cd week5 && make format
cd week5 && make lint
```

## Configuration

Copy `.env.example` to `.env` (in `week5/`) to override defaults like the database path.

## Codex self-study workflows

Task 2 uses React 18.3.1 browser modules loaded from `esm.sh`; internet access is required, but Node and a frontend build are not required. Task 9 initializes SQLite sorting indexes at application startup.

See [automation setup and commands](docs/AUTOMATIONS.md), [multi-agent log](docs/MULTI_AGENT_LOG.md), and [self-study write-up](writeup.md). The two repeatable workflows are `python scripts/run_automation.py quality` and `python scripts/run_automation.py performance`; install the documented dependencies first. These are Codex self-study workflows, not Warp Drive integrations.
