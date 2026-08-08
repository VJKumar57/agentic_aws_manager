from textwrap import dedent

def build_proposal_prompt(user_prompt: str) -> str:
    template = dedent('''
        You are an AWS provisioning assistant. Given the user's intent, output a JSON array of actions the agent
        should perform. Do NOT output any explanation or text outside the JSON.

        Each action must be an object with at least the field "action" and follow this shape:
        - For creating resources: {"action": "create", "type_name": "AWS::Service::Type", "properties": {...}}
        - For deleting resources: {"action": "delete", "type_name": "AWS::Service::Type", "identifier": "resource-identifier"}
        - For updating resources: {"action": "update", "type_name": "AWS::Service::Type", "identifier": "resource-identifier", "properties": {...}}
        - For arbitrary calls: {"action": "call", "params": {...}}

        User intent: """
    ''')
    prompt = template + user_prompt + "\n\nRespond with a single JSON array."
    return prompt
