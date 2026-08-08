# agentic_aws_manager

Agentic AWS Manager is a local FastAPI service that proposes AWS-style actions,
validates them, and stores proposal and audit history.

## What You Get

- REST API: plan, approve, proposals, audits
- SQLite persistence (`agent_data.db` by default)
- JSON schema validation for proposed actions
- Optional local LLM integration
- CLI client for common flows

## Quickstart

Use Python 3.10 in this repo.

```bash
python3.10 -m venv .venv310
source .venv310/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
PYTHONPATH=src uvicorn app_with_validation:app --host 127.0.0.1 --port 8000
```

Open:
- http://127.0.0.1:8000/docs

## One Command: Start + Test Endpoint

Run from the project root:

```bash
source .venv310/bin/activate && (PYTHONPATH=src uvicorn app_with_validation:app --host 127.0.0.1 --port 8000 >/tmp/agentic_aws_manager.log 2>&1 &) && sleep 2 && curl -fsS http://127.0.0.1:8000/docs >/dev/null && python - <<'PY'
import urllib.request
req = urllib.request.Request('http://127.0.0.1:8000/proposals', method='GET')
with urllib.request.urlopen(req, timeout=10) as r:
    print(r.status, r.read().decode())
PY
```

Expected output:
- `200 [...]` (or `200 []` on a fresh DB)

## API Usage

Create a proposal:

```bash
curl -sS -X POST http://127.0.0.1:8000/plan \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"Create an S3 bucket named demo-bucket for testing"}'
```

List proposals:

```bash
curl -sS http://127.0.0.1:8000/proposals
```

Get one proposal:

```bash
curl -sS http://127.0.0.1:8000/proposals/<proposal_id>
```

Approve (dry run):

```bash
curl -sS -X POST http://127.0.0.1:8000/approve/<proposal_id> \
  -H 'Content-Type: application/json' \
  -d '{"dry_run": true}'
```

List audits:

```bash
curl -sS http://127.0.0.1:8000/audits
```

## CLI Usage

In a second terminal, while API is running:

```bash
source .venv310/bin/activate
PYTHONPATH=src python scripts/cli.py --help
PYTHONPATH=src python scripts/cli.py plan-s3 demo-bucket
PYTHONPATH=src python scripts/cli.py list-proposals
PYTHONPATH=src python scripts/cli.py approve <proposal_id>
PYTHONPATH=src python scripts/cli.py audits
```

## Run Tests

```bash
source .venv310/bin/activate
PYTHONPATH=src pytest -q
```

## Troubleshooting

- `externally-managed-environment` on macOS: use the local virtual environment above.
- Dependency conflicts: confirm you are using Python 3.10.
- Import errors: make sure `PYTHONPATH=src` is present in run/test commands.
- Port conflict on 8000: run uvicorn on a different port.

## Full Guide

See `FULL_README.md` for architecture, workflow details, and deeper operational notes.
