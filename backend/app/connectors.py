"""Least-privilege Jira handoff adapter.

The adapter is deliberately disabled unless an operator enables it and supplies
an Atlassian credential through the runtime environment. It creates at most
one issue for a Driftline action (marker-based idempotency), scopes writes to a
single configured project, and reverses the handoff by toggling Driftline-owned
labels rather than deleting or rewriting customer work.
"""

from __future__ import annotations

import base64
import json
import os
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urljoin
from urllib.request import Request, urlopen


class ConnectorError(RuntimeError):
    """A configured connector could not complete its bounded operation."""


@dataclass(frozen=True)
class JiraConfig:
    enabled: bool
    base_url: str = ""
    email: str = ""
    token: str = ""
    project_key: str = ""
    issue_type: str = "Task"

    @classmethod
    def from_env(cls) -> JiraConfig:
        enabled = os.getenv("DRIFTLINE_JIRA_ENABLED", "false").casefold() == "true"
        return cls(
            enabled=enabled,
            base_url=os.getenv("DRIFTLINE_JIRA_BASE_URL", "").rstrip("/") + "/",
            email=os.getenv("DRIFTLINE_JIRA_EMAIL", ""),
            token=os.getenv("DRIFTLINE_JIRA_TOKEN", ""),
            project_key=os.getenv("DRIFTLINE_JIRA_PROJECT_KEY", ""),
            issue_type=os.getenv("DRIFTLINE_JIRA_ISSUE_TYPE", "Task"),
        )

    def validate(self) -> None:
        if not self.enabled:
            return
        if not self.base_url.startswith("https://") or "atlassian.net" not in self.base_url:
            raise ConnectorError("jira_base_url_must_be_atlassian_https")
        if not self.email or not self.token or not self.project_key:
            raise ConnectorError("jira_credentials_or_project_missing")


def _adf(text: str) -> dict[str, Any]:
    return {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "paragraph",
                "content": [{"type": "text", "text": text[:32000]}],
            }
        ],
    }


class JiraConnector:
    """Small Jira v3 client with injectable transport for contract tests."""

    def __init__(
        self,
        config: JiraConfig,
        *,
        opener: Callable[..., Any] = urlopen,
    ) -> None:
        config.validate()
        self.config = config
        self._opener = opener
        credentials = f"{config.email}:{config.token}".encode()
        self._authorization = "Basic " + base64.b64encode(credentials).decode()

    def _request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
        *,
        query: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        url = urljoin(self.config.base_url, path.lstrip("/"))
        if query:
            url = f"{url}?{urlencode(query)}"
        body = json.dumps(payload).encode() if payload is not None else None
        request = Request(
            url,
            data=body,
            headers={
                "Accept": "application/json",
                "Authorization": self._authorization,
                "Content-Type": "application/json",
                "User-Agent": "Driftline-Jira-Connector/1.0",
            },
            method=method,
        )
        try:
            with self._opener(request, timeout=8) as response:
                raw = response.read().decode("utf-8")
        except (HTTPError, URLError, TimeoutError) as exc:
            raise ConnectorError(f"jira_request_failed:{method}:{path}") from exc
        try:
            return json.loads(raw) if raw else {}
        except json.JSONDecodeError as exc:
            raise ConnectorError("jira_response_not_json") from exc

    def create_or_reuse_issue(
        self,
        *,
        workflow_id: str,
        action_id: str,
        source_name: str,
        evidence_hash: str,
        artifact: str,
        owner: str,
        proposed: str,
    ) -> dict[str, Any]:
        marker = f"Driftline action {action_id}"
        search = self._request(
            "POST",
            "/rest/api/3/search",
            {
                "jql": f'project = "{self.config.project_key}" AND text ~ "{marker}"',
                "maxResults": 1,
                "fields": ["key", "summary", "labels"],
            },
        )
        existing = (search.get("issues") or [None])[0]
        if existing:
            return {
                "status": "reused",
                "issue_key": existing.get("key"),
                "issue_url": existing.get("self"),
                "idempotent": True,
            }

        description = (
            f"{marker}\n"
            f"Workflow: {workflow_id}\n"
            f"Source: {source_name}\n"
            f"Evidence hash: {evidence_hash}\n"
            f"Owner: {owner}\n\n"
            f"Proposed output:\n{proposed}\n\n"
            "This issue was created by an approval-gated Driftline connector. "
            "It does not change customer-facing systems automatically."
        )
        created = self._request(
            "POST",
            "/rest/api/3/issue",
            {
                "fields": {
                    "project": {"key": self.config.project_key},
                    "summary": f"[Driftline] {artifact} · {source_name}",
                    "issuetype": {"name": self.config.issue_type},
                    "description": _adf(description),
                    "labels": ["driftline-active", "driftline-approval-gated"],
                }
            },
        )
        return {
            "status": "created",
            "issue_key": created.get("key"),
            "issue_id": created.get("id"),
            "issue_url": created.get("self"),
            "idempotent": False,
        }

    def reverse_issue(self, issue_key: str, action_id: str) -> dict[str, Any]:
        self._request(
            "PUT",
            f"/rest/api/3/issue/{quote(issue_key, safe='')}",
            {
                "update": {
                    "labels": [
                        {"remove": "driftline-active"},
                        {"add": "driftline-reversed"},
                    ]
                }
            },
        )
        self._request(
            "POST",
            f"/rest/api/3/issue/{quote(issue_key, safe='')}/comment",
            {"body": _adf(f"Driftline action {action_id} was reversed by a named human reviewer.")},
        )
        return {"status": "reversed", "issue_key": issue_key}


def execute_jira_handoff(state: Any) -> dict[str, Any]:
    """Create one Jira task for the first approved packet, if explicitly enabled."""

    config = JiraConfig.from_env()
    if not config.enabled:
        return {"jira_status": "not_configured", "external_write": False}
    packet = next(
        (item for item in state.artifact_packets if item.get("status") == "packet_ready"),
        None,
    )
    if packet is None:
        return {"jira_status": "not_eligible", "external_write": False}
    connector = JiraConnector(config)
    evidence = state.evidence
    result = connector.create_or_reuse_issue(
        workflow_id=state.workflow_id,
        action_id=str((state.action_record or {}).get("action_id", "unknown")),
        source_name=evidence.source_name if evidence else "Unknown",
        evidence_hash=evidence.evidence_hash if evidence else "none",
        artifact=str(packet["artifact"]),
        owner=str(packet["owner"]),
        proposed=str(packet["content"]),
    )
    return {
        "jira_status": result["status"],
        "jira_issue_key": result.get("issue_key"),
        "jira_issue_url": result.get("issue_url"),
        "jira_idempotent": result.get("idempotent", False),
        "external_write": True,
    }


def reverse_jira_handoff(state: Any) -> dict[str, Any]:
    """Remove the active marker and append a reversal comment, never delete work."""

    action = state.action_record or {}
    issue_key = action.get("jira_issue_key")
    config = JiraConfig.from_env()
    if not issue_key or not config.enabled:
        return {"jira_status": "not_configured", "external_write": False}
    connector = JiraConnector(config)
    result = connector.reverse_issue(
        str(issue_key), str(action.get("action_id", "unknown"))
    )
    return {
        "jira_status": result["status"],
        "jira_issue_key": issue_key,
        "external_write": True,
    }
