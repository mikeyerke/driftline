import json

import pytest

from app import connectors as connector_module
from app.connectors import (
    ConfluenceConfig,
    ConfluenceConnector,
    ConnectorError,
    GitHubConfig,
    GitHubConnector,
    JiraConfig,
    JiraConnector,
    SalesforceConfig,
    SalesforceReadOnlyClient,
    SlackConfig,
    SlackConnector,
    exchange_salesforce_code,
    execute_confluence_handoff,
    salesforce_authorization_url,
    salesforce_readiness,
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


def test_jira_reactivates_a_reversed_marker_before_reuse() -> None:
    requests = []
    responses = [
        {
            "issues": [
                {
                    "key": "DRIFT-42",
                    "self": "https://jira.example/rest/api/3/issue/10042",
                    "fields": {"labels": ["driftline-reversed"]},
                }
            ]
        },
        {},
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

    assert result == {
        "status": "reactivated",
        "issue_key": "DRIFT-42",
        "issue_url": "https://jira.example/rest/api/3/issue/10042",
        "idempotent": True,
    }
    assert len(requests) == 2
    assert requests[1][0].method == "PUT"
    body = json.loads(requests[1][0].data)
    assert body["update"]["labels"] == [
        {"remove": "driftline-reversed"},
        {"add": "driftline-active"},
    ]


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


def test_jira_context_summary_is_bounded_and_aggregate_only() -> None:
    requests = []

    def opener(request, timeout):
        requests.append(request)
        return _Response(
            {
                "total": 3,
                "issues": [
                    {"fields": {"status": {"name": "To Do"}, "priority": {"name": "High"}}},
                    {"fields": {"status": {"name": "To Do"}, "priority": {"name": "Low"}}},
                ],
            }
        )

    connector = JiraConnector(
        JiraConfig(enabled=True, base_url="https://example.atlassian.net/", email="a@b.com", token="x", project_key="DRIFT"),
        opener=opener,
    )
    result = connector.read_context_summary()

    assert result["open_issue_count"] == 3
    assert result["sampled_issue_count"] == 2
    assert result["by_status"] == {"To Do": 2}
    assert result["redaction"] == "aggregate_metadata_only"
    payload = json.loads(requests[0].data)
    assert payload["maxResults"] == 50
    assert "summary" not in payload["fields"]


def test_confluence_context_summary_does_not_return_page_bodies() -> None:
    responses = [{"results": [{"id": "space-1"}]}, {"totalSize": 4, "results": [{"id": "page-1", "title": "private"}], "_links": {"next": "/next"}}]
    connector = ConfluenceConnector(
        ConfluenceConfig(enabled=True, base_url="https://example.atlassian.net/wiki/", email="a@b.com", token="x", space_key="DRIFT"),
        opener=lambda request, timeout: _Response(responses.pop(0)),
    )
    result = connector.read_context_summary()

    assert result["page_count"] == 4
    assert result["sampled_page_count"] == 1
    assert "title" not in result
    assert result["redaction"] == "aggregate_metadata_only"


def test_slack_context_summary_omits_message_text() -> None:
    connector = SlackConnector(
        SlackConfig(enabled=True, token="xoxb-test", channel_id="C123"),
        opener=lambda request, timeout: _Response({"ok": True, "messages": [{"ts": "1", "text": "private"}], "has_more": True}),
    )
    result = connector.read_context_summary()

    assert result["recent_message_count"] == 1
    assert result["has_more"] is True
    assert "private" not in str(result)


def test_github_context_summary_is_repository_scoped() -> None:
    connector = GitHubConnector(
        GitHubConfig(enabled=True, token="ghp-test", owner="acme", repo="docs"),
        opener=lambda request, timeout: _Response(
            [
                {"labels": [{"name": "driftline-active"}]},
                {"pull_request": {"url": "https://api.github.com/pr/1"}, "labels": []},
            ]
        ),
    )
    result = connector.read_context_summary()

    assert result["open_issue_count"] == 1
    assert result["open_pull_request_count"] == 1
    assert result["driftline_active_count"] == 1
    assert result["scope"] == "repository:acme/docs"


@pytest.mark.parametrize(
    "config",
    [
        SlackConfig(
            enabled=True,
            token="xoxb-test",
            channel_id="C123",
            base_url="https://collector.example/api/",
        ),
        GitHubConfig(
            enabled=True,
            token="ghp-test",
            owner="acme",
            repo="docs",
            api_url="https://collector.example/",
        ),
        JiraConfig(
            enabled=True,
            base_url="https://evil-atlassian.net.example/",
            email="a@b.com",
            token="x",
            project_key="DRIFT",
        ),
    ],
)
def test_connector_rejects_untrusted_destination_hosts(config) -> None:
    with pytest.raises(ConnectorError):
        config.validate()


def test_unconfigured_confluence_is_explicitly_prepared_only(monkeypatch) -> None:
    monkeypatch.delenv("DRIFTLINE_CONFLUENCE_ENABLED", raising=False)

    result = execute_confluence_handoff(DriftlineWorkflow().start_demo())

    assert result == {
        "confluence_status": "not_configured",
        "confluence_prepared_only": True,
        "external_write": False,
    }


def test_tenant_connector_secret_resolution_requires_binding(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_JIRA_ENABLED", "true")
    monkeypatch.delenv("DRIFTLINE_JIRA_TOKEN", raising=False)
    monkeypatch.delenv("DRIFTLINE_JIRA_TOKEN_SECRET", raising=False)
    monkeypatch.setattr(
        connector_module,
        "read_secret",
        lambda name: "tenant-token" if name == "driftline-tenant-acme-jira" else "",
    )
    monkeypatch.setattr(
        "app.persistence.load_connector_binding",
        lambda tenant, connector: {
            "tenant_id": tenant,
            "connector": connector,
            "secret_name": "driftline-tenant-acme-jira",
            "status": "active",
        },
    )

    config = JiraConfig.from_env("acme")
    assert config.token == "tenant-token"


def test_tenant_connector_secret_resolution_honors_pinned_version(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_JIRA_ENABLED", "true")
    monkeypatch.delenv("DRIFTLINE_JIRA_TOKEN", raising=False)
    monkeypatch.delenv("DRIFTLINE_JIRA_TOKEN_SECRET", raising=False)
    calls: list[tuple[str, str]] = []

    def read_secret(name: str, *, version: str = "latest") -> str:
        calls.append((name, version))
        return "tenant-token-v7"

    monkeypatch.setattr(connector_module, "read_secret", read_secret)
    monkeypatch.setattr(
        "app.persistence.load_connector_binding",
        lambda tenant, connector: {
            "tenant_id": tenant,
            "connector": connector,
            "secret_name": "driftline-tenant-acme-jira",
            "secret_version": "7",
            "status": "active",
        },
    )

    config = JiraConfig.from_env("acme")

    assert config.token == "tenant-token-v7"
    assert calls == [("driftline-tenant-acme-jira", "7")]


def test_tenant_connector_profile_scopes_non_secret_targets(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_JIRA_ENABLED", "true")
    monkeypatch.setenv("DRIFTLINE_JIRA_BASE_URL", "https://default.atlassian.net")
    monkeypatch.setenv("DRIFTLINE_JIRA_EMAIL", "default@example.com")
    monkeypatch.setenv("DRIFTLINE_JIRA_PROJECT_KEY", "DEFAULT")
    monkeypatch.setenv(
        "DRIFTLINE_TENANT_CONNECTOR_CONFIG",
        json.dumps(
            {
                "acme": {
                    "jira": {
                        "base_url": "https://acme.atlassian.net",
                        "email": "owner@acme.example",
                        "project_key": "ACME",
                        "issue_type": "Task",
                    }
                }
            }
        ),
    )
    monkeypatch.setattr(
        connector_module,
        "_tenant_secret_or_env",
        lambda tenant, connector, env_name, **_kwargs: "tenant-token",
    )

    config = JiraConfig.from_env("acme")

    assert config.base_url == "https://acme.atlassian.net/"
    assert config.email == "owner@acme.example"
    assert config.project_key == "ACME"
    assert config.token == "tenant-token"


def test_durable_tenant_connector_profile_precedes_deployment_defaults(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_JIRA_ENABLED", "true")
    monkeypatch.setenv("DRIFTLINE_JIRA_BASE_URL", "https://default.atlassian.net")
    monkeypatch.setenv("DRIFTLINE_JIRA_EMAIL", "default@example.com")
    monkeypatch.setenv("DRIFTLINE_JIRA_PROJECT_KEY", "DEFAULT")
    monkeypatch.delenv("DRIFTLINE_TENANT_CONNECTOR_CONFIG", raising=False)
    monkeypatch.setattr(
        "app.persistence.load_connector_profile",
        lambda tenant, connector: {
            "tenant_id": tenant,
            "connector": connector,
            "status": "active",
            "settings": {
                "base_url": "https://durable.atlassian.net",
                "email": "owner@durable.example",
                "project_key": "DUR",
            },
        },
    )
    monkeypatch.setattr(
        connector_module,
        "_tenant_secret_or_env",
        lambda tenant, connector, env_name, **_kwargs: "tenant-token",
    )

    config = JiraConfig.from_env("durable-acme")

    assert config.base_url == "https://durable.atlassian.net/"
    assert config.email == "owner@durable.example"
    assert config.project_key == "DUR"


def test_firestore_tenant_connector_target_requires_durable_profile(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_PERSISTENCE", "firestore")
    monkeypatch.delenv("DRIFTLINE_TENANT_CONNECTOR_CONFIG", raising=False)
    monkeypatch.setenv("DRIFTLINE_JIRA_ENABLED", "true")
    monkeypatch.setenv("DRIFTLINE_JIRA_BASE_URL", "https://default.atlassian.net")
    monkeypatch.setenv("DRIFTLINE_JIRA_EMAIL", "default@example.com")
    monkeypatch.setenv("DRIFTLINE_JIRA_PROJECT_KEY", "DEFAULT")
    monkeypatch.setattr("app.persistence.load_connector_profile", lambda *_args: None)
    monkeypatch.setattr(
        connector_module,
        "_tenant_secret_or_env",
        lambda tenant, connector, env_name: "tenant-token",
    )

    with pytest.raises(ConnectorError, match="tenant_connector_profile_missing"):
        JiraConfig.from_env("missing-profile")


def test_invalid_tenant_connector_profile_fails_closed(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_TENANT_CONNECTOR_CONFIG", "{not-json")

    with pytest.raises(ConnectorError, match="tenant_connector_config_invalid"):
        JiraConfig.from_env("acme")


def test_tenant_connector_secret_resolution_fails_closed_without_binding(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_JIRA_ENABLED", "true")
    monkeypatch.delenv("DRIFTLINE_JIRA_TOKEN", raising=False)
    monkeypatch.delenv("DRIFTLINE_JIRA_TOKEN_SECRET", raising=False)
    monkeypatch.setattr("app.persistence.load_connector_binding", lambda *_args: None)
    with pytest.raises(ConnectorError, match="tenant_binding_missing"):
        JiraConfig.from_env("acme")


def test_revoked_tenant_connector_binding_fails_closed(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_JIRA_ENABLED", "true")
    monkeypatch.delenv("DRIFTLINE_JIRA_TOKEN", raising=False)
    monkeypatch.delenv("DRIFTLINE_JIRA_TOKEN_SECRET", raising=False)
    monkeypatch.setattr(
        "app.persistence.load_connector_binding",
        lambda *_args: {
            "tenant_id": "acme",
            "connector": "jira",
            "secret_name": "driftline-tenant-acme-jira",
            "status": "revoked",
        },
    )
    with pytest.raises(ConnectorError, match="tenant_binding_missing"):
        JiraConfig.from_env("acme")


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


def test_confluence_reactivates_a_reversed_page_without_overwriting_history() -> None:
    requests = []
    responses = [
        {
            "results": [
                {"id": "page-42", "_links": {"webui": "/wiki/page-42"}}
            ]
        },
        {"metadata": {"labels": {"results": [{"name": "driftline-reversed"}]}}},
        {},
        {},
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

    assert result["status"] == "reactivated"
    assert result["idempotent"] is True
    assert requests[1].full_url.endswith(
        "/rest/api/content/page-42?expand=metadata.labels"
    )
    assert requests[2].method == "DELETE"
    assert requests[2].full_url.endswith(
        "/rest/api/content/page-42/label/global/driftline-reversed"
    )
    assert requests[3].method == "POST"
    assert json.loads(requests[3].data) == {
        "prefix": "global",
        "name": "driftline-active",
    }


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


def test_slack_reactivates_after_a_reversal_message() -> None:
    requests = []
    responses = [
        {
            "ok": True,
            "messages": [
                {"ts": "1710000000.000001", "text": "Driftline action action-1"},
                {
                    "ts": "1710000000.000002",
                    "text": "Driftline action action-1 was reversed by a named human reviewer.",
                },
            ],
        },
        {"ok": True, "ts": "1710000000.000003"},
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

    assert result == {
        "status": "reactivated",
        "message_ts": "1710000000.000003",
        "idempotent": True,
    }
    assert requests[1].full_url.endswith("chat.postMessage")
    body = json.loads(requests[1].data)
    assert body["client_msg_id"] == "action-1:reactivate"
    assert "reactivated" in body["text"]


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


def test_github_reactivates_reversed_issue_labels() -> None:
    requests = []
    responses = [
        [
            {
                "number": 7,
                "html_url": "https://github.com/acme/docs/issues/7",
                "title": "[Driftline] Comparison map",
                "body": "Driftline action action-1",
                "labels": [{"name": "driftline-reversed"}],
            }
        ],
        {"labels": [{"name": "driftline-active"}]},
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

    assert result == {
        "status": "reactivated",
        "issue_number": 7,
        "issue_url": "https://github.com/acme/docs/issues/7",
        "idempotent": True,
    }
    assert requests[1].method == "POST"
    assert requests[1].full_url.endswith("/repos/acme/docs/issues/7/labels")
    assert json.loads(requests[1].data) == {
        "labels": ["driftline-active", "driftline-approval-gated"]
    }


def test_salesforce_defaults_to_read_only_prepared_contract(monkeypatch) -> None:
    monkeypatch.delenv("DRIFTLINE_SALESFORCE_ENABLED", raising=False)
    monkeypatch.delenv("DRIFTLINE_SALESFORCE_TOKEN", raising=False)
    result = salesforce_readiness()
    assert result["status"] == "not_configured"
    assert result["mode"] == "prepared_only"
    assert result["external_write"] is False


def test_salesforce_config_rejects_non_salesforce_hosts() -> None:
    config = SalesforceConfig(
        enabled=True,
        base_url="https://example.com",
        token="test-token",
    )
    try:
        config.validate()
    except ConnectorError as exc:
        assert "salesforce_base_url" in str(exc)
    else:  # pragma: no cover - assertion documents the security boundary.
        raise AssertionError("non-Salesforce host was accepted")


def test_salesforce_oauth_url_is_scoped_and_does_not_include_secret() -> None:
    config = SalesforceConfig(
        enabled=True,
        client_id="client-id",
        client_secret="do-not-leak",
        redirect_uri="https://driftline.example/api/connectors/salesforce/oauth/callback",
    )
    url = salesforce_authorization_url(config, "opaque-state")
    assert "client-id" in url
    assert "do-not-leak" not in url
    assert "state=opaque-state" in url
    assert "refresh_token" in url


def test_salesforce_oauth_url_includes_pkce_challenge() -> None:
    config = SalesforceConfig(
        enabled=True,
        client_id="client-id",
        client_secret="do-not-leak",
        redirect_uri="https://driftline.example/api/connectors/salesforce/oauth/callback",
    )
    url = salesforce_authorization_url(config, "opaque-state", code_challenge="challenge")
    assert "code_challenge=challenge" in url
    assert "code_challenge_method=S256" in url


def test_salesforce_code_exchange_uses_post_and_redacts_response_surface() -> None:
    requests = []

    def opener(request, timeout):
        requests.append((request, timeout))
        return _Response(
            {
                "access_token": "access",
                "refresh_token": "refresh",
                "instance_url": "https://acme.my.salesforce.com",
            }
        )

    config = SalesforceConfig(
        enabled=True,
        client_id="client-id",
        client_secret="secret",
        redirect_uri="https://driftline.example/callback",
    )
    result = exchange_salesforce_code(config, "one-time-code", opener=opener)
    assert result["instance_url"].endswith("salesforce.com")
    assert requests[0][0].method == "POST"
    assert b"one-time-code" in requests[0][0].data


def test_salesforce_code_exchange_sends_pkce_verifier() -> None:
    requests = []

    def opener(request, timeout):
        requests.append(request)
        return _Response({"access_token": "access", "refresh_token": "refresh"})

    config = SalesforceConfig(
        enabled=True,
        client_id="client-id",
        client_secret="secret",
        redirect_uri="https://driftline.example/callback",
    )
    exchange_salesforce_code(config, "one-time-code", code_verifier="verifier", opener=opener)
    assert b"code_verifier=verifier" in requests[0].data


def test_salesforce_client_rejects_unallowlisted_object() -> None:
    config = SalesforceConfig(enabled=True, base_url="https://acme.my.salesforce.com", token="token")
    client = SalesforceReadOnlyClient(
        config,
        access_token="access",
        instance_url="https://acme.my.salesforce.com",
    )
    try:
        client.query_summary("Account")
    except ConnectorError as exc:
        assert str(exc) == "salesforce_object_not_allowlisted"
    else:  # pragma: no cover - documents the read-only boundary.
        raise AssertionError("unallowlisted Salesforce object was queried")
