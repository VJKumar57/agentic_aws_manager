from agentic_aws_manager import validator

def test_validate_valid_actions():
    actions = [
        {'action': 'create', 'type_name': 'AWS::S3::Bucket', 'properties': {'BucketName': 'test-bucket'}}
    ]
    valid, errors = validator.validate_actions(actions)
    assert valid
    assert errors == []

def test_validate_invalid_actions():
    actions = [
        {'action': 'create', 'properties': {'BucketName': 'test-bucket'}}
    ]
    valid, errors = validator.validate_actions(actions)
    assert not valid
    assert len(errors) > 0
