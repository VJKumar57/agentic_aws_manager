import json
from jsonschema import Draft7Validator
from typing import Any, Tuple, List
from pathlib import Path

SCHEMA_PATH = Path(__file__).parent / 'schemas' / 'proposal_schema.json'

def load_schema() -> dict:
    with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def validate_actions(actions: Any) -> Tuple[bool, List[str]]:
    schema = load_schema()
    validator = Draft7Validator(schema)
    errors = []
    for e in validator.iter_errors(actions):
        path = '.'.join([str(p) for p in e.path])
        if path:
            errors.append(f"{path}: {e.message}")
        else:
            errors.append(e.message)
    return (len(errors) == 0, errors)
