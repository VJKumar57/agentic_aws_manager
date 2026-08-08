from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from agentic_aws_manager import llm as llm_mod
from agentic_aws_manager import db as db_mod
from agentic_aws_manager import executor_sqlite as exec_mod
from agentic_aws_manager import validator as validator_mod
from agentic_aws_manager import prompt_templates as prompt_templates_mod
import json

app = FastAPI(title='Agentic AWS Resource Manager (validated)')

class PlanRequest(BaseModel):
    prompt: str
    model_path: Optional[str] = None

class ApproveRequest(BaseModel):
    dry_run: Optional[bool] = True

@app.on_event('startup')
def startup_checks():
    db_mod.init_db()

@app.post('/plan')
def plan(req: PlanRequest):
    llm = llm_mod.load_local_llm(model_path=req.model_path)
    prompt = prompt_templates_mod.build_proposal_prompt(req.prompt)
    resp = llm.generate(prompt)
    parsed = None
    try:
        parsed = json.loads(resp)
    except Exception:
        parsed = None
    if parsed is None or not isinstance(parsed, list):
        actions = [{'action': 'create', 'type_name': 'AWS::S3::Bucket', 'properties': {'BucketName': 'example-bucket'}}]
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
