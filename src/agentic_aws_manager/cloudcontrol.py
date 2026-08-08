import json
from typing import Any, Dict, Optional
from .aws_auth import get_client

def _cloudcontrol_client(profile: Optional[str] = None, region_name: Optional[str] = None):
    for name in ('cloudcontrol', 'cloudcontrolapi'):
        try:
            return get_client(name, profile=profile, region_name=region_name)
        except Exception:
            continue
    raise RuntimeError('Could not create Cloud Control API client')

def create_resource(type_name: str, properties: Dict[str, Any], profile: Optional[str] = None, region_name: Optional[str] = None):
    client = _cloudcontrol_client(profile, region_name)
    desired_state = json.dumps(properties) if not isinstance(properties, str) else properties
    return client.create_resource(TypeName=type_name, DesiredState=desired_state)

def delete_resource(type_name: str, identifier: str, profile: Optional[str] = None, region_name: Optional[str] = None):
    client = _cloudcontrol_client(profile, region_name)
    return client.delete_resource(TypeName=type_name, Identifier=identifier)

def get_resource(resource_arn: str, profile: Optional[str] = None, region_name: Optional[str] = None):
    client = _cloudcontrol_client(profile, region_name)
    return client.get_resource(ResourceArn=resource_arn)
