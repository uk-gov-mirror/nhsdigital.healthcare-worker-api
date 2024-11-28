import json
import os

from urllib3 import request

from status_reporting import handler, get_commit_state
from unittest.mock import patch


def construct_detail(stage, state):
    return {"detail": {"stage": stage, "state": state, "pipeline": "code_pipeline", "execution-id": "execution_id"}}


def test_commit_started_state():
    message = construct_detail("SOURCE", "STARTED")

    commit_state = get_commit_state(message)

    assert commit_state == "pending"


def test_success_state():
    message = construct_detail("INTEGRATION-TEST", "SUCCEEDED")

    commit_state = get_commit_state(message)

    assert commit_state == "success"


def test_failure_state():
    message = construct_detail("stage-name", "FAILED")

    commit_state = get_commit_state(message)

    assert commit_state == "error"


def test_stopped_state():
    message = construct_detail("stage-name", "STOPPED")

    commit_state = get_commit_state(message)

    assert commit_state == "error"


@patch.dict(os.environ, {"secret_id": "secret_id"})
@patch("status_reporting.boto3")
@patch("status_reporting.urllib3")
def test_new_pipeline_pr(urllib3_mock, boto3_mock):
    detail = json.dumps(construct_detail("SOURCE", "STARTED"))
    event = {"Records": [{"Sns": {"Message": detail}}]}

    boto3_mock.client.return_value.get_secret_value.return_value = {"SecretString": "secret_value"}
    boto3_mock.client.return_value.get_pipeline_execution.return_value = {
        "pipelineExecution": {
            "artifactRevisions": [{
                "revisionId": "commit_id"
            }],
            "variables": [{
                "name": "branch",
                "resolvedValue": "pr-123"
            }]
        }
    }

    handler(event, {})

    request_mock = urllib3_mock.PoolManager.return_value.request
    url = ("https://eu-west-2.console.aws.amazon.com/codesuite/codepipeline/pipelines/code_pipeline"
            "/executions/execution_id?region=eu-west-2")
    build_status = {
        'state': "pending",
        'context': 'HCW Deployment',
        'description': "CodePipeline: code_pipeline",
        'target_url': url
    }
    request_mock.assert_called_with("POST",
                                    "https://api.github.com/repos/NHSDigital/healthcare-worker-api/statuses/commit_id",
                                    headers={'Content-Type': 'application/json', 'Authorization': "Bearer secret_value"},
                                    body=json.dumps(build_status).encode())


@patch.dict(os.environ, {"secret_id": "secret_id", "slack_secret_id": "slack_secret_id"})
@patch("status_reporting.boto3")
@patch("status_reporting.urllib3")
def test_new_pipeline_develop(urllib3_mock, boto3_mock):
    detail = json.dumps(construct_detail("INTEGRATION-TEST", "SUCCEEDED"))
    event = {"Records": [{"Sns": {"Message": detail}}]}

    boto3_mock.client.return_value.get_secret_value.return_value = {"SecretString": "secret_value"}
    boto3_mock.client.return_value.get_pipeline_execution.return_value = {
        "pipelineExecution": {
            "artifactRevisions": [{
                "revisionId": "commit_id"
            }],
            "variables": [{
                "name": "branch",
                "resolvedValue": "ft"
            }]
        }
    }

    request_mock = urllib3_mock.PoolManager.return_value.request
    request_mock.return_value.data.decode.return_value = '{"ok": "true"}'

    handler(event, {})

    url = ("https://eu-west-2.console.aws.amazon.com/codesuite/codepipeline/pipelines/code_pipeline"
            "/executions/execution_id?region=eu-west-2")
    message = {
        "channel": "C07RCAJEJPP",
        "text": f"New FT build, deploy and test successful - <{url}|Pipeline>"
    }

    request_mock.assert_called_with("POST", "https://slack.com/api/chat.postMessage",
                                    headers={
                                        "Content-Type": "application/json; charset=utf-8",
                                        "Authorization": "Bearer secret_value"
                                    },
                                    body=json.dumps(message).encode())


@patch.dict(os.environ, {"secret_id": "secret_id", "slack_secret_id": "slack_secret_id"})
@patch("status_reporting.boto3")
@patch("status_reporting.urllib3")
def test_new_pipeline_develop_failure(urllib3_mock, boto3_mock):
    detail = json.dumps(construct_detail("INTEGRATION-TEST", "FAILED"))
    event = {"Records": [{"Sns": {"Message": detail}}]}

    boto3_mock.client.return_value.get_secret_value.return_value = {"SecretString": "secret_value"}
    boto3_mock.client.return_value.get_pipeline_execution.return_value = {
        "pipelineExecution": {
            "artifactRevisions": [{
                "revisionId": "commit_id"
            }],
            "variables": [{
                "name": "branch",
                "resolvedValue": "ft"
            }]
        }
    }

    request_mock = urllib3_mock.PoolManager.return_value.request
    request_mock.return_value.data.decode.return_value = '{"ok": "true"}'

    handler(event, {})

    url = ("https://eu-west-2.console.aws.amazon.com/codesuite/codepipeline/pipelines/code_pipeline"
            "/executions/execution_id?region=eu-west-2")
    message = {
        "channel": "C07RCAJEJPP",
        "text": f"<!here> ⚠️ New FT build / deploy / test failed - <{url}|Pipeline>"
    }

    request_mock.assert_called_with("POST", "https://slack.com/api/chat.postMessage",
                                    headers={
                                        "Content-Type": "application/json; charset=utf-8",
                                        "Authorization": "Bearer secret_value"
                                    },
                                    body=json.dumps(message).encode())
