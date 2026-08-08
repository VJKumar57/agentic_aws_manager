import sqlite3
import json
from typing import Optional, Dict, Any, List
from datetime import datetime
import os

def get_db_path() -> str:
    return os.getenv('AGENT_DB_PATH', './agent_data.db')

def get_conn():
    path = get_db_path()
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('''
    CREATE TABLE IF NOT EXISTS proposals (
        id TEXT PRIMARY KEY,
        actions TEXT NOT NULL,
        status TEXT NOT NULL,
        result TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    ''')
    cur.execute('''
    CREATE TABLE IF NOT EXISTS audits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        proposal_id TEXT,
        event TEXT,
        details TEXT,
        created_at TEXT NOT NULL
    )
    ''')
    conn.commit()
    conn.close()

def now_iso() -> str:
    return datetime.utcnow().isoformat() + 'Z'

def save_proposal(pid: str, actions: List[Dict[str, Any]], status: str = 'pending') -> None:
    conn = get_conn()
    cur = conn.cursor()
    now = now_iso()
    cur.execute('INSERT OR REPLACE INTO proposals (id, actions, status, result, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)', (pid, json.dumps(actions), status, None, now, now))
    conn.commit()
    conn.close()

def list_proposals() -> List[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('SELECT * FROM proposals ORDER BY created_at DESC')
    rows = cur.fetchall()
    conn.close()
    out = []
    for r in rows:
        out.append({'id': r['id'], 'actions': json.loads(r['actions']), 'status': r['status'], 'result': json.loads(r['result']) if r['result'] else None, 'created_at': r['created_at'], 'updated_at': r['updated_at']})
    return out

def get_proposal(pid: str) -> Optional[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('SELECT * FROM proposals WHERE id = ?', (pid,))
    r = cur.fetchone()
    conn.close()
    if not r:
        return None
    return {'id': r['id'], 'actions': json.loads(r['actions']), 'status': r['status'], 'result': json.loads(r['result']) if r['result'] else None, 'created_at': r['created_at'], 'updated_at': r['updated_at']}

def update_proposal_result(pid: str, status: str, result: Any) -> None:
    conn = get_conn()
    cur = conn.cursor()
    now = now_iso()
    cur.execute('UPDATE proposals SET status = ?, result = ?, updated_at = ? WHERE id = ?', (status, json.dumps(result), now, pid))
    conn.commit()
    conn.close()

def add_audit(proposal_id: Optional[str], event: str, details: Any) -> None:
    conn = get_conn()
    cur = conn.cursor()
    now = now_iso()
    cur.execute('INSERT INTO audits (proposal_id, event, details, created_at) VALUES (?, ?, ?, ?)', (proposal_id, event, json.dumps(details), now))
    conn.commit()
    conn.close()

def list_audits(limit: int = 100) -> List[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('SELECT * FROM audits ORDER BY created_at DESC LIMIT ?', (limit,))
    rows = cur.fetchall()
    conn.close()
    out = []
    for r in rows:
        out.append({'id': r['id'], 'proposal_id': r['proposal_id'], 'event': r['event'], 'details': json.loads(r['details']) if r['details'] else None, 'created_at': r['created_at']})
    return out
