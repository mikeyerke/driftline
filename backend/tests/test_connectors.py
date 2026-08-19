import json

from app.connectors import JiraConfig, JiraConnector


class _Response:
    def __init__(self, payload: dict):
        self._payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return json.dumps(self._payload).encode()


def test_jira_create_is_project_scoped_and_marker_idempotent() -> None:
    requests = []
    responses = [
        {"issues": []},
        {"key": "DRIFT-42", "id": "10042", "self": "https://jira.example/rest/api/3/issue/10042"},
    ]

    def opener(request, timeout):
        requests.append((request, timeout))
        return _Response(responses.pop(0))

    connector = JiraConnector(
        JiraConfig(
            enabled=True,
            base_url="https://example.atlassian.net/",
            email="operator@example.com",
            token="test-token",
            project_key="DRIFT",
        ),
        opener=opener,
    )
    result = connector.create_or_reuse_issue(
        workflow_id="wf-1",
        action_id="action-1",
        source_name="Competitor pricing",
        evidence_hash="abc123",
        artifact="Comparison map",
        owner="Product Marketing",
        proposed="Update the price.",
    )

    assert result["status"] == "created"
    assert len(requests) == 2
    body = json.loads(requests[1][0].data)
    assert body["fields"]["project"] == {"key": "DRIFT"}
    assert body["fields"]["labels"] == ["driftline-active", "driftline-approval-gated"]
    assert "Driftline action action-1" in body["fields"]["description"]["content"][0]["content"][0]["text"]


def test_jira_reverse_toggles_only_driftline_owned_labels() -> None:
    requests = []

    def opener(request, timeout):
        requests.append(request)
        return _Response({})

    connector = JiraConnector(
        JiraConfig(
            enabled=True,
            base_url="https://example.atlassian.net/",
            email="operator@example.com",
            token="test-token",
            project_key="DRIFT",
        ),
        opener=opener,
    )
    result = connector.reverse_issue("DRIFT-42", "action-1")

    assert result == {"status": "reversed", "issue_key": "DRIFT-42"}
    assert requests[0].method == "PUT"
    update = json.loads(requests[0].data)
    assert update["update"]["labels"] == [
        {"remove": "driftline-active"},
        {"add": "driftline-reversed"},
    ]
    assert requests[1].method == "POST"
