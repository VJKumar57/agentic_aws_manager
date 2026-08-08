from typing import Dict, Any, List
from . import cloudcontrol
from . import db
import uuid

def propose(actions: List[Dict[str, Any]]) -> str:
    pid = str(uuid.uuid4())
    db.save_proposal(pid, actions, status='pending')
    db.add_audit(pid, 'proposed', {'actions': actions})
    return pid

def list_proposals() -> List[Dict[str, Any]]:
    return db.list_proposals()

def get_proposal(pid: str):
    return db.get_proposal(pid)

def approve_and_execute(pid: str, dry_run: bool = True) -> Dict[str, Any]:
    p = db.get_proposal(pid)
    if p is None:
        raise KeyError('proposal not found')
    if p.get('status') != 'pending':
        return {'id': pid, 'status': p.get('status'), 'result': p.get('result')}
    db.add_audit(pid, 'approved', {'dry_run': dry_run})
    results = []
    for act in p['actions']:
        if dry_run:
            results.append({'action': act, 'status': 'dry-run', 'detail': 'Not executed'})
            continue
        try:
            if act.get('action') == 'create':
                res = cloudcontrol.create_resource(act.get('type_name'), act.get('properties', {}))
            elif act.get('action') == 'delete':
                res = cloudcontrol.delete_resource(act.get('type_name'), act.get('identifier'))
            else:
                res = {'note': 'unsupported action'}
            results.append({'action': act, 'status': 'executed', 'detail': res})
            db.add_audit(pid, 'executed_action', {'action': act, 'detail': str(res)})
        except Exception as e:
            results.append({'action': act, 'status': 'error', 'error': str(e)})
            db.add_audit(pid, 'action_error', {'action': act, 'error': str(e)})
    db.update_proposal_result(pid, 'done', results)
    return {'id': pid, 'results': results}
