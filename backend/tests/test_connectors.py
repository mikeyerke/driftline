import json

from app.connectors import (
    ConfluenceConfig,
    ConfluenceConnector,
    GitHubConfig,
    GitHubConnector,
    JiraConfig,
    JiraConnector,
    SlackConfig,
    SlackConnector,
    execute_confluence_handoff,
)
from app.workflow import DriftlineWorkflow


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
    assert requests[0][0].method == "POST"
    search = json.loads(requests[0][0].data)
    assert search["jql"] == 'project = "DRIFT" AND text ~ "Driftline action action-1"'
    assert search["maxResults"] == 1
    assert search["fields"] == ["key", "summary", "labels"]
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


def test_jira_scoped_gateway_url_is_allowed() -> None:
    connector = JiraConnector(
        JiraConfig(
            enabled=True,
            base_url="https://api.atlassian.com/ex/jira/cloud-id/",
            email="operator@example.com",
            token="test-token",
            project_key="DRIFT",
        ),
        opener=lambda request, timeout: _Response({"issues": []}),
    )

    assert connector.config.base_url.endswith("/jira/cloud-id/")


def test_unconfigured_confluence_is_explicitly_prepared_only(monkeypatch) -> None:
    monkeypatch.delenv("DRIFTLINE_CONFLUENCE_ENABLED", raising=False)

    result = execute_confluence_handoff(DriftlineWorkflow().start_demo())

    assert result == {
        "confluence_status": "not_configured",
        "confluence_prepared_only": True,
        "external_write": False,
    }


def test_confluence_page_creation_is_marker_idempotent() -> None:
    requests = []
    responses = [
        {"results": []},
        {"id": "page-42", "_links": {"webui": "/wiki/page-42"}},
    ]

    def opener(request, timeout):
        requests.append(request)
        return _Response(responses.pop(0))

    connector = ConfluenceConnector(
        ConfluenceConfig(
            enabled=True,
            base_url="https://example.atlassian.net/wiki/",
            email="operator@example.com",
            token="test-token",
            space_key="PMM",
        ),
        opener=opener,
    )
    result = connector.create_or_reuse_page(
        action_id="action-1",
        workflow_id="wf-1",
        source_name="Competitor pricing",
        evidence_hash="a" * 64,
        artifact="Comparison map",
        owner="Product Marketing",
        proposed="Refresh the row.",
    )

    assert result["status"] == "created"
    assert len(requests) == 2
    assert requests[0].method == "GET"
    assert "spaceKey=PMM" in requests[0].full_url
    body = json.loads(requests[1].data)
    assert body["space"] == {"key": "PMM"}
    assert "Driftline action action-1" in body["body"]["storage"]["value"]


def test_slack_message_creation_reuses_marker() -> None:
    requests = []
    responses = [
        {"ok": True, "messages": []},
        {"ok": True, "ts": "1710000000.000001"},
    ]

    def opener(request, timeout):
        requests.append(request)
        return _Response(responses.pop(0))

    connector = SlackConnector(
        SlackConfig(enabled=True, token="xoxb-test", channel_id="C123"),
        opener=opener,
    )
    result = connector.create_or_reuse_message(
        action_id="action-1",
        workflow_id="wf-1",
        artifact="Comparison map",
        owner="Product Marketing",
        proposed="Refresh the row.",
    )

    assert result["status"] == "created"
    assert requests[0].full_url.endswith("conversations.history")
    post = json.loads(requests[1].data)
    assert post["channel"] == "C123"
    assert post["client_msg_id"] == "action-1"
    assert "Driftline action action-1" in post["text"]


def test_github_issue_creation_is_repository_scoped_and_idempotent() -> None:
    requests = []
    responses = [
        [],
        {"number": 7, "html_url": "https://github.com/acme/docs/issues/7"},
    ]

    def opener(request, timeout):
        requests.append(request)
        return _Response(responses.pop(0))

    connector = GitHubConnector(
        GitHubConfig(enabled=True, token="ghp-test", owner="acme", repo="docs"),
        opener=opener,
    )
    result = connector.create_or_reuse_issue(
        action_id="action-1",
        workflow_id="wf-1",
        artifact="Comparison map",
        owner="Product Marketing",
        proposed="Refresh the row.",
        evidence_hash="a" * 64,
    )

    assert result["status"] == "created"
    assert requests[0].full_url.endswith("/repos/acme/docs/issues?state=all&per_page=100")
    body = json.loads(requests[1].data)
    assert body["labels"] == ["driftline-active", "driftline-approval-gated"]
    assert "Driftline action action-1" in body["body"]
