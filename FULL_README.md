# Agentic AWS Resource Manager

A compact scaffold for an agentic workflow that proposes AWS resource actions,
validates them, and stores proposal/audit history.

## What This Repo Does

This project runs a local API service that:
- accepts natural language intent
- asks an LLM to propose AWS-style actions
- validates the action schema
- stores proposals and audit events in SQLite
- supports a dry-run approval path

Core paths:
- src/app_with_validation.py
- src/agentic_aws_manager/
- scripts/cli.py
- tests/test_validator.py

## Prerequisites

- macOS, Linux, or Windows with Python 3.10 available
- terminal access

Recommended Python for this repo:
- Python 3.10

## Setup

From project root:

    python3.10 -m venv .venv310
    source .venv310/bin/activate
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt

If python3.10 is not found, install it first and retry.

## Start The API

    source .venv310/bin/activate
    PYTHONPATH=src uvicorn app_with_validation:app --host 127.0.0.1 --port 8000

Swagger UI:
- http://127.0.0.1:8000/docs

## One-Command Start + Test Endpoint

Use this from project root:

    source .venv310/bin/activate && (PYTHONPATH=src uvicorn app_with_validation:app --host 127.0.0.1 --port 8000 >/tmp/agentic_aws_manager.log 2>&1 &) && sleep 2 && curl -fsS http://127.0.0.1:8000/docs >/dev/null && python - <<'PY'
    import urllib.request
    req = urllib.request.Request('http://127.0.0.1:8000/proposals', method='GET')
    with urllib.request.urlopen(req, timeout=10) as r:
	 print(r.status, r.read().decode())
    PY

Expected output:
- HTTP status 200
- response body, often [] in a fresh run

## End-to-End Usage Flow

1. Create a plan proposal

	curl -sS -X POST http://127.0.0.1:8000/plan \
	  -H 'Content-Type: application/json' \
	  -d '{"prompt":"Create an S3 bucket named demo-bucket for testing"}'

2. Copy proposal_id from response.

3. Inspect all proposals

	curl -sS http://127.0.0.1:8000/proposals

4. Inspect one proposal

	curl -sS http://127.0.0.1:8000/proposals/<proposal_id>

5. Approve with dry run

	curl -sS -X POST http://127.0.0.1:8000/approve/<proposal_id> \
	  -H 'Content-Type: application/json' \
	  -d '{"dry_run": true}'

6. View audit trail

	curl -sS http://127.0.0.1:8000/audits

## CLI Usage

Run CLI commands while API is active:

    source .venv310/bin/activate
    PYTHONPATH=src python scripts/cli.py --help
    PYTHONPATH=src python scripts/cli.py plan-s3 demo-bucket
    PYTHONPATH=src python scripts/cli.py list-proposals
    PYTHONPATH=src python scripts/cli.py approve <proposal_id>
    PYTHONPATH=src python scripts/cli.py audits

The CLI default API base URL is:
- http://localhost:8000

Use custom base URL:

    PYTHONPATH=src python scripts/cli.py --base http://127.0.0.1:8000 list-proposals

## Local Data

SQLite file default:
- ./agent_data.db

Override DB path:

    AGENT_DB_PATH=/path/to/agent_data.db PYTHONPATH=src uvicorn app_with_validation:app --host 127.0.0.1 --port 8000

## LLM Behavior

LLM load path priority:
1. explicit model_path in request
2. LLAMA_MODEL_PATH environment variable
3. transformers fallback
4. echo fallback behavior

When output is not valid JSON actions list, the app writes a fallback S3 action and logs a plan_fallback audit event.

## Run Tests

    source .venv310/bin/activate
    PYTHONPATH=src pytest -q

## Common Issues

1. pip says externally-managed-environment on macOS
- Cause: using system Python installation directly
- Fix: use the virtual environment steps above

2. pydantic or dependency conflicts
- Cause: unsupported Python version
- Fix: use Python 3.10 for this repo

3. Module import errors for app modules
- Cause: src path not on import path
- Fix: include PYTHONPATH=src in commands

4. Port already in use
- Cause: another process on 8000
- Fix: start uvicorn on a different port

## Suggested Daily Workflow

1. Pull latest changes

	git pull --rebase

2. Activate environment

	source .venv310/bin/activate

3. Run tests

	PYTHONPATH=src pytest -q

4. Start API and validate docs endpoint

	PYTHONPATH=src uvicorn app_with_validation:app --host 127.0.0.1 --port 8000

5. Make changes, re-test, then commit and push

	git add .
	git commit -m "Describe your change"
	git push
