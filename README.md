# agentic_aws_manager

Agentic AWS Resource Manager is a local FastAPI service that creates and tracks proposed AWS actions.

This repository includes:
- REST API for plan, approve, proposals, and audits
- SQLite persistence
- JSON schema validation for proposed actions
- Optional local LLM integration
- Simple CLI client

## Quick Start

1. Open a terminal in the project root.
2. Create and activate a Python 3.10 virtual environment.
3. Install dependencies.
4. Start the API.

Commands:

	python3.10 -m venv .venv310
	source .venv310/bin/activate
	python -m pip install --upgrade pip
	python -m pip install -r requirements.txt
	PYTHONPATH=src uvicorn app_with_validation:app --host 127.0.0.1 --port 8000

Open API docs:
- http://127.0.0.1:8000/docs

## One-Command Start + Smoke Test

Run this from the project root:

	source .venv310/bin/activate && (PYTHONPATH=src uvicorn app_with_validation:app --host 127.0.0.1 --port 8000 >/tmp/agentic_aws_manager.log 2>&1 &) && sleep 2 && curl -fsS http://127.0.0.1:8000/docs >/dev/null && python - <<'PY'
	import urllib.request
	req = urllib.request.Request('http://127.0.0.1:8000/proposals', method='GET')
	with urllib.request.urlopen(req, timeout=10) as r:
		print(r.status, r.read().decode())
	PY

Expected result:
- Status code 200
- Response body such as []

## API Examples

Create a plan:

	curl -sS -X POST http://127.0.0.1:8000/plan \
	  -H 'Content-Type: application/json' \
	  -d '{"prompt":"Create an S3 bucket named demo-bucket for testing"}'

List proposals:

	curl -sS http://127.0.0.1:8000/proposals

Get one proposal:

	curl -sS http://127.0.0.1:8000/proposals/<proposal_id>

Approve proposal as dry run:

	curl -sS -X POST http://127.0.0.1:8000/approve/<proposal_id> \
	  -H 'Content-Type: application/json' \
	  -d '{"dry_run": true}'

List audits:

	curl -sS http://127.0.0.1:8000/audits

## CLI Examples

In a second terminal while API is running:

	source .venv310/bin/activate
	PYTHONPATH=src python scripts/cli.py --help
	PYTHONPATH=src python scripts/cli.py plan-s3 demo-bucket
	PYTHONPATH=src python scripts/cli.py list-proposals
	PYTHONPATH=src python scripts/cli.py audits

## Run Tests

	source .venv310/bin/activate
	PYTHONPATH=src pytest -q

## Troubleshooting

- If pip fails in system Python on macOS with externally-managed-environment, use the virtual environment steps above.
- If dependency resolution fails, ensure you are using Python 3.10.
- If port 8000 is already in use, change the port in the uvicorn command.
- If imports fail, confirm PYTHONPATH=src is set when running app and tests.

## Full Guide

For deeper architecture and endpoint details, see FULL_README.md.
