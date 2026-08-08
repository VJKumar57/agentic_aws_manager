# Agentic AWS Resource Manager

A complete setup and API walkthrough for running this repository locally.

## 1. What This Repository Does

This project runs a local FastAPI service that:
- accepts a natural-language AWS request
- generates a proposed action list using a local LLM adapter
- validates the proposal against schema rules
- stores proposals and audit events in SQLite
- supports approval in dry-run mode

Main paths:
- `src/app_with_validation.py` (API entry point)
- `src/agentic_aws_manager/` (core modules)
- `scripts/cli.py` (CLI helper)
- `tests/test_validator.py` (unit tests)

## 2. Prerequisites

- Python 3.10
- Terminal access

Important:
- Use Python 3.10 for reliable dependency installation in this repo.
- Python 3.13 may fail with dependency/build conflicts.

## 3. Complete Setup

From repository root:

```bash
python3.10 -m venv .venv310
source .venv310/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Optional quick check:

```bash
python -V
```

Expected output should include `Python 3.10`.

## 4. Start the API

Run:

```bash
source .venv310/bin/activate
PYTHONPATH=src uvicorn app_with_validation:app --host 127.0.0.1 --port 8000
```

Open Swagger UI:
- http://127.0.0.1:8000/docs

## 5. One-Command Start + Smoke Test

Use this command from repository root:

```bash
source .venv310/bin/activate && (PYTHONPATH=src uvicorn app_with_validation:app --host 127.0.0.1 --port 8000 >/tmp/agentic_aws_manager.log 2>&1 &) && sleep 2 && curl -fsS http://127.0.0.1:8000/docs >/dev/null && python - <<'PY'
import urllib.request
req = urllib.request.Request('http://127.0.0.1:8000/proposals', method='GET')
with urllib.request.urlopen(req, timeout=10) as r:
    print(r.status, r.read().decode())
PY
```

Expected result:
- `200` status
- JSON output, usually `[]` on a fresh DB

## 6. API Walkthrough

### 6.1 Endpoint Summary

| Method | Path | Purpose |
|---|---|---|
| POST | `/plan` | Create a proposal from a natural-language prompt |
| GET | `/proposals` | List all proposals |
| GET | `/proposals/{proposal_id}` | Get one proposal |
| POST | `/approve/{proposal_id}` | Approve and execute (supports dry-run) |
| GET | `/audits` | List audit events |

### 6.2 Step-by-Step API Flow

1. Create a proposal

```bash
curl -sS -X POST http://127.0.0.1:8000/plan \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"Create an S3 bucket named demo-bucket for testing"}'
```

Typical response shape:

```json
{
  "proposal_id": "<uuid>",
  "actions": [
    {
      "action": "create",
      "type_name": "AWS::S3::Bucket",
      "properties": {
        "BucketName": "example-bucket"
      }
    }
  ]
}
```

2. List proposals

```bash
curl -sS http://127.0.0.1:8000/proposals
```

3. Get one proposal

```bash
curl -sS http://127.0.0.1:8000/proposals/<proposal_id>
```

4. Approve proposal as dry run

```bash
curl -sS -X POST http://127.0.0.1:8000/approve/<proposal_id> \
  -H 'Content-Type: application/json' \
  -d '{"dry_run": true}'
```

5. View audit history

```bash
curl -sS http://127.0.0.1:8000/audits
```

### 6.3 Full Copy-Paste E2E Script

This script creates a proposal, extracts `proposal_id`, fetches it, dry-runs approval, and prints audits.

```bash
source .venv310/bin/activate

PLAN_JSON=$(curl -sS -X POST http://127.0.0.1:8000/plan \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"Create an S3 bucket named e2e-demo-bucket"}')

echo "$PLAN_JSON"

PROPOSAL_ID=$(echo "$PLAN_JSON" | python - <<'PY'
import json, sys
payload = json.loads(sys.stdin.read())
print(payload["proposal_id"])
PY
)

echo "proposal_id=$PROPOSAL_ID"

curl -sS "http://127.0.0.1:8000/proposals/$PROPOSAL_ID"
curl -sS -X POST "http://127.0.0.1:8000/approve/$PROPOSAL_ID" \
  -H 'Content-Type: application/json' \
  -d '{"dry_run": true}'
curl -sS http://127.0.0.1:8000/audits
```

## 7. CLI Walkthrough

With API running in one terminal, use another terminal:

```bash
source .venv310/bin/activate
PYTHONPATH=src python scripts/cli.py --help
PYTHONPATH=src python scripts/cli.py plan-s3 demo-bucket
PYTHONPATH=src python scripts/cli.py list-proposals
PYTHONPATH=src python scripts/cli.py approve <proposal_id>
PYTHONPATH=src python scripts/cli.py audits
```

Change API base URL when needed:

```bash
PYTHONPATH=src python scripts/cli.py --base http://127.0.0.1:8000 list-proposals
```

## 8. Data and Environment Variables

Default DB file:
- `./agent_data.db`

Override database path:

```bash
AGENT_DB_PATH=/path/to/agent_data.db PYTHONPATH=src uvicorn app_with_validation:app --host 127.0.0.1 --port 8000
```

LLM load priority:
1. `model_path` in `/plan` request body
2. `LLAMA_MODEL_PATH` environment variable
3. transformers fallback
4. echo fallback

Behavior note:
- If generated LLM output is not valid JSON action list, the service writes a fallback S3 action and logs a `plan_fallback` audit event.

## 9. Testing

Run unit tests:

```bash
source .venv310/bin/activate
PYTHONPATH=src pytest -q
```

## 10. Troubleshooting

### `externally-managed-environment` on macOS
Cause:
- using system Python package installation directly

Fix:
- use `.venv310` virtual environment setup from section 3

### Dependency build/resolution errors
Cause:
- unsupported Python version

Fix:
- use Python 3.10

### `ModuleNotFoundError` for local package
Cause:
- `src` not on Python path

Fix:
- include `PYTHONPATH=src` for app/test commands

### Port 8000 already in use
Fix:
- start on another port, example `--port 8001`
- update curl/CLI base URLs accordingly

## 11. Daily Developer Workflow

```bash
git pull --rebase
source .venv310/bin/activate
PYTHONPATH=src pytest -q
PYTHONPATH=src uvicorn app_with_validation:app --host 127.0.0.1 --port 8000
```

After code changes:

```bash
git add .
git commit -m "Describe your change"
git push
```
