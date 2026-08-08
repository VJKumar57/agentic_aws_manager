import boto3
import botocore
from typing import Optional, Dict

def get_boto3_session(profile: Optional[str] = None, region_name: Optional[str] = None):
    if profile:
        return boto3.Session(profile_name=profile, region_name=region_name)
    return boto3.Session(region_name=region_name)

def get_client(service_name: str, profile: Optional[str] = None, region_name: Optional[str] = None):
    sess = get_boto3_session(profile=profile, region_name=region_name)
    return sess.client(service_name)

def validate_aws_credentials(profile: Optional[str] = None, region_name: Optional[str] = None) -> Dict[str, str]:
    sess = get_boto3_session(profile=profile, region_name=region_name)
    try:
        sts = sess.client('sts')
        resp = sts.get_caller_identity()
        return {'Account': resp.get('Account'), 'Arn': resp.get('Arn'), 'UserId': resp.get('UserId')}
    except botocore.exceptions.NoCredentialsError as e:
        raise RuntimeError('No AWS credentials found') from e
    except botocore.exceptions.PartialCredentialsError as e:
        raise RuntimeError('Partial AWS credentials found') from e
    except Exception as e:
        raise RuntimeError(f'Failed to validate AWS credentials: {e}') from e
