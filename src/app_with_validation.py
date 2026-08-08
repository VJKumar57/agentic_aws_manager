from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional
from agentic_aws_manager import llm as llm_mod
from agentic_aws_manager import db as db_mod
from agentic_aws_manager import executor_sqlite as exec_mod
from agentic_aws_manager import validator as validator_mod
from agentic_aws_manager import prompt_templates as prompt_templates_mod
import json
import re

app = FastAPI(title='Agentic AWS Resource Manager (validated)')

class PlanRequest(BaseModel):
    prompt: str
    model_path: Optional[str] = None

class ApproveRequest(BaseModel):
    dry_run: Optional[bool] = True

class ChatRequest(BaseModel):
    message: str
    execute: Optional[bool] = True
    dry_run: Optional[bool] = False
    model_path: Optional[str] = None

@app.on_event('startup')
def startup_checks():
    db_mod.init_db()

def _extract_bucket_name(user_prompt: str) -> Optional[str]:
    p = user_prompt.lower()
    if 's3' not in p or 'bucket' not in p:
        return None
    m = re.search(r'\bnamed\s+([a-z0-9][a-z0-9.-]{1,61}[a-z0-9])\b', p)
    if m:
        return m.group(1)
    m = re.search(r'\bname\s+([a-z0-9][a-z0-9.-]{1,61}[a-z0-9])\b', p)
    if m:
        return m.group(1)
    return None

def _fallback_actions_from_prompt(user_prompt: str):
    bucket_name = _extract_bucket_name(user_prompt)
    if bucket_name:
        return [
            {
                'action': 'create',
                'type_name': 'AWS::S3::Bucket',
                'properties': {'BucketName': bucket_name}
            }
        ]
    return [
        {
            'action': 'create',
            'type_name': 'AWS::S3::Bucket',
            'properties': {'BucketName': 'example-bucket'}
        }
    ]

def _build_plan(user_prompt: str, model_path: Optional[str] = None):
    llm = llm_mod.load_local_llm(model_path=model_path)
    prompt = prompt_templates_mod.build_proposal_prompt(user_prompt)
    resp = llm.generate(prompt)
    parsed = None
    try:
        parsed = json.loads(resp)
    except Exception:
        parsed = None

    if parsed is None or not isinstance(parsed, list):
        actions = _fallback_actions_from_prompt(user_prompt)
        pid = exec_mod.propose(actions)
        db_mod.add_audit(pid, 'plan_fallback', {'reason': 'parse_failed', 'raw_output': resp})
        return {'proposal_id': pid, 'actions': actions, 'note': 'fallback used'}

    valid, errors = validator_mod.validate_actions(parsed)
    pid = exec_mod.propose(parsed)
    if not valid:
        db_mod.update_proposal_result(pid, 'invalid', {'validation_errors': errors})
        db_mod.add_audit(pid, 'validation_failed', {'errors': errors, 'raw_output': resp})
        return {'proposal_id': pid, 'valid': False, 'errors': errors}
    db_mod.add_audit(pid, 'validated', {})
    return {'proposal_id': pid, 'actions': parsed, 'valid': True}

@app.post('/plan')
def plan(req: PlanRequest):
        return _build_plan(req.prompt, model_path=req.model_path)

@app.get('/chat-ui', response_class=HTMLResponse)
def chat_ui():
        return '''<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Agentic AWS Chat</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #f7f6f2;
            --paper: #fffdf8;
            --ink: #11222a;
            --muted: #4f636b;
            --accent: #d96537;
            --accent-2: #2f8f9d;
            --line: #d7d2c9;
            --good: #177245;
            --bad: #b42931;
        }
        * { box-sizing: border-box; }
        body {
            margin: 0;
            min-height: 100vh;
            font-family: "Space Grotesk", sans-serif;
            color: var(--ink);
            background:
                radial-gradient(1000px 500px at -10% -10%, #ffd9a8 0%, rgba(255,217,168,0) 60%),
                radial-gradient(900px 450px at 110% 10%, #a8dfdd 0%, rgba(168,223,221,0) 55%),
                var(--bg);
            display: grid;
            place-items: center;
            padding: 16px;
        }
        .shell {
            width: min(920px, 100%);
            height: min(90vh, 860px);
            background: linear-gradient(180deg, #fffefb 0%, var(--paper) 100%);
            border: 1px solid var(--line);
            border-radius: 18px;
            box-shadow: 0 24px 60px rgba(17, 34, 42, 0.12);
            display: grid;
            grid-template-rows: auto 1fr auto;
            overflow: hidden;
        }
        .head {
            padding: 16px 18px;
            border-bottom: 1px solid var(--line);
            background: repeating-linear-gradient(
                135deg,
                rgba(47, 143, 157, 0.08),
                rgba(47, 143, 157, 0.08) 10px,
                rgba(217, 101, 55, 0.08) 10px,
                rgba(217, 101, 55, 0.08) 20px
            );
        }
        .title {
            margin: 0;
            font-size: 1.06rem;
            font-weight: 700;
            letter-spacing: 0.01em;
        }
        .sub {
            margin: 4px 0 0;
            color: var(--muted);
            font-size: 0.92rem;
        }
        .chat {
            padding: 16px;
            overflow: auto;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }
        .msg {
            max-width: min(86%, 760px);
            border: 1px solid var(--line);
            border-radius: 14px;
            padding: 12px 14px;
            line-height: 1.4;
            animation: fadeUp 220ms ease;
            white-space: pre-wrap;
            word-break: break-word;
        }
        .user {
            align-self: flex-end;
            background: #fff2e8;
            border-color: #ebc3ab;
        }
        .bot {
            align-self: flex-start;
            background: #eef7f8;
            border-color: #b7dbe0;
        }
        .meta {
            margin-top: 8px;
            font-family: "IBM Plex Mono", monospace;
            font-size: 0.8rem;
            color: var(--muted);
        }
        .ok { color: var(--good); }
        .err { color: var(--bad); }
        .composer {
            border-top: 1px solid var(--line);
            padding: 12px;
            background: #fffefb;
            display: grid;
            gap: 10px;
        }
        .controls {
            display: flex;
            justify-content: space-between;
            gap: 10px;
            flex-wrap: wrap;
            color: var(--muted);
            font-size: 0.9rem;
        }
        .row {
            display: grid;
            grid-template-columns: 1fr auto;
            gap: 10px;
        }
        input[type="text"] {
            width: 100%;
            border: 1px solid var(--line);
            border-radius: 12px;
            font: inherit;
            padding: 12px;
            background: #fffcf7;
            color: var(--ink);
        }
        button {
            border: 0;
            border-radius: 12px;
            font: inherit;
            font-weight: 700;
            padding: 0 18px;
            color: #fff;
            background: linear-gradient(135deg, var(--accent), #bd4f23);
            cursor: pointer;
            min-width: 124px;
        }
        button:disabled {
            opacity: 0.55;
            cursor: default;
        }
        @keyframes fadeUp {
            from { opacity: 0; transform: translateY(8px); }
            to { opacity: 1; transform: translateY(0); }
        }
        @media (max-width: 640px) {
            .shell { height: 94vh; border-radius: 14px; }
            .row { grid-template-columns: 1fr; }
            button { min-height: 44px; }
            .msg { max-width: 96%; }
        }
    </style>
</head>
<body>
    <main class="shell">
        <header class="head">
            <h1 class="title">Agentic AWS Conversational Console</h1>
            <p class="sub">Type an intent. The API will plan and optionally execute the AWS action.</p>
        </header>
        <section id="chat" class="chat"></section>
        <form id="composer" class="composer">
            <div class="controls">
                <label><input id="execute" type="checkbox" checked /> Execute now</label>
                <label><input id="dryRun" type="checkbox" /> Dry run</label>
            </div>
            <div class="row">
                <input id="msg" type="text" placeholder="Create an S3 bucket named demo-bucket for testing" required />
                <button id="send" type="submit">Send</button>
            </div>
        </form>
    </main>
    <script>
        const chat = document.getElementById('chat');
        const form = document.getElementById('composer');
        const msgInput = document.getElementById('msg');
        const sendBtn = document.getElementById('send');
        const executeBox = document.getElementById('execute');
        const dryRunBox = document.getElementById('dryRun');

        function appendMessage(role, text, metaText, metaClass) {
            const div = document.createElement('div');
            div.className = `msg ${role}`;
            div.textContent = text;
            if (metaText) {
                const meta = document.createElement('div');
                meta.className = `meta ${metaClass || ''}`;
                meta.textContent = metaText;
                div.appendChild(meta);
            }
            chat.appendChild(div);
            chat.scrollTop = chat.scrollHeight;
        }

        appendMessage('bot', 'Ready. Example: "Create an S3 bucket named demo-bucket for testing"');

        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const message = msgInput.value.trim();
            if (!message) return;
            const execute = executeBox.checked;
            const dryRun = dryRunBox.checked;

            appendMessage('user', message);
            msgInput.value = '';
            sendBtn.disabled = true;

            try {
                const r = await fetch('/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message, execute, dry_run: dryRun })
                });
                const data = await r.json();
                if (!r.ok) {
                    appendMessage('bot', 'Request failed.', JSON.stringify(data), 'err');
                    return;
                }
                appendMessage(
                    'bot',
                    data.assistant_message,
                    `proposal_id=${data.proposal_id}`,
                    data.success ? 'ok' : 'err'
                );
            } catch (err) {
                appendMessage('bot', 'Network or server error.', String(err), 'err');
            } finally {
                sendBtn.disabled = false;
                msgInput.focus();
            }
        });
    </script>
</body>
</html>'''

@app.post('/chat')
def chat(req: ChatRequest):
        plan_res = _build_plan(req.message, model_path=req.model_path)
        pid = plan_res.get('proposal_id')
        if not pid:
                return {
                        'success': False,
                        'assistant_message': 'I could not create a proposal for that request.',
                        'details': plan_res
                }

        if req.execute:
                exec_res = exec_mod.approve_and_execute(pid, dry_run=bool(req.dry_run))
                statuses = [r.get('status', 'unknown') for r in exec_res.get('results', [])]
                if all(s in ('executed', 'dry-run') for s in statuses) and statuses:
                        action_mode = 'dry run simulated' if req.dry_run else 'executed'
                        return {
                                'success': True,
                                'proposal_id': pid,
                                'assistant_message': f'Request planned and {action_mode}.',
                                'plan': plan_res,
                                'execution': exec_res
                        }
                return {
                        'success': False,
                        'proposal_id': pid,
                        'assistant_message': 'Request was planned, but one or more actions failed during execution.',
                        'plan': plan_res,
                        'execution': exec_res
                }

        return {
                'success': True,
                'proposal_id': pid,
                'assistant_message': 'Request planned and waiting for approval.',
                'plan': plan_res
        }

@app.get('/proposals')
def proposals():
    return exec_mod.list_proposals()

@app.get('/proposals/{pid}')
def get_proposal(pid: str):
    p = exec_mod.get_proposal(pid)
    if not p:
        raise HTTPException(status_code=404, detail='proposal not found')
    return p

@app.post('/approve/{pid}')
def approve(pid: str, body: ApproveRequest):
    try:
        res = exec_mod.approve_and_execute(pid, dry_run=body.dry_run)
    except KeyError:
        raise HTTPException(status_code=404, detail='proposal not found')
    return res

@app.get('/audits')
def audits():
    return db_mod.list_audits()
