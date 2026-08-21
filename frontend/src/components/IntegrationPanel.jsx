import { AlertCircle, CheckCircle2, Database, FileText, GitPullRequest, Hash, MessageSquare, RefreshCw, ShieldCheck, TicketCheck } from "lucide-react";
import { useEffect, useState } from "react";
import { getConnectorBindingsHealth, getConnectorContextSummary } from "../api";

const icons = { Jira: TicketCheck, Confluence: FileText, Slack: MessageSquare, GitHub: GitPullRequest, Salesforce: Database };

const connectorOrder = ["Jira", "Confluence", "Slack", "GitHub", "Salesforce"];

function aggregateLabel(system, data = {}) {
  if (system === "Jira" && data.open_issue_count !== undefined) return `${data.open_issue_count} open issues`;
  if (system === "Confluence" && data.page_count !== undefined) return `${data.page_count} pages in scope`;
  if (system === "Slack" && data.recent_message_count !== undefined) return `${data.recent_message_count} recent messages`;
  if (system === "GitHub" && data.open_issue_count !== undefined) return `${data.open_issue_count} issues · ${data.open_pull_request_count || 0} PRs`;
  if (system === "Salesforce" && Array.isArray(data.objects)) {
    const total = data.objects.reduce((sum, item) => sum + Number(item.total || 0), 0);
    return `${data.objects.length} objects · ${total} records`;
  }
  if (data.status === "not_configured") return "Not configured";
  if (data.status === "failed") return "Read failed";
  return "Aggregate context available";
}

export default function IntegrationPanel({ targets = [], approved, dismissed, actionRecord, operatorSession }) {
  const [context, setContext] = useState(null);
  const [health, setHealth] = useState(null);
  const [contextLoading, setContextLoading] = useState(false);
  const [contextError, setContextError] = useState("");
  useEffect(() => {
    setContext(null);
    setHealth(null);
    setContextError("");
  }, [operatorSession?.tenantId]);
  if (!targets.length) return null;
  const statusKeys = { Jira: "jira_status", Confluence: "confluence_status", Slack: "slack_status", GitHub: "github_status", Salesforce: "salesforce_status" };
  const connectorStatuses = new Set(["created", "reused", "reactivated", "reversed"]);
  const statusFor = (target) => {
    if (dismissed) return { label: "Not created", written: false };
    if (!approved) return { label: "Ready for review", written: false };
    const connectorStatus = actionRecord?.[statusKeys[target.system]];
    if (connectorStatus === "created") return { label: "Created", written: true };
    if (connectorStatus === "reused") return { label: "Reused", written: true };
    if (connectorStatus === "reactivated") return { label: "Reactivated", written: true };
    if (connectorStatus === "reversed") return { label: "Reversed", written: true };
    if (connectorStatus === "failed") return { label: "Failed", written: false };
    if (connectorStatus === "not_eligible") return { label: "Not eligible", written: false };
    if (connectorStatus === "blocked_closed") return { label: "Blocked · closed target", written: false };
    return { label: "Packet ready", written: false };
  };
  const writes = Object.entries(statusKeys).filter(([, key]) => connectorStatuses.has(actionRecord?.[key])).map(([system, key]) => `${system}: ${actionRecord[key]}`);
  const loadContext = async () => {
    if (!operatorSession?.identityToken || contextLoading) return;
    setContextLoading(true);
    setContextError("");
    try {
      const [nextContext, nextHealth] = await Promise.all([getConnectorContextSummary(), getConnectorBindingsHealth()]);
      setContext(nextContext);
      setHealth(nextHealth);
    } catch (error) {
      setContextError(error.message || "Connector context could not be read");
    } finally {
      setContextLoading(false);
    }
  };
  return (
    <section className="panel integration-panel" aria-labelledby="integration-title">
      <header className="panel-header">
        <div><h2 id="integration-title">PMM handoff destinations</h2><span className="live-label">Approval-gated</span></div>
        <span className="muted">No silent writes</span>
      </header>
      <p className="integration-intro">Driftline turns the impact map into target-specific packets. The live public lane is packet-safe: it never mutates an external system. A separately authenticated tenant operator can enable a configured connector and execute only the signed, scoped handoff.</p>
      {operatorSession?.identityToken && <div className="connector-context" aria-labelledby="connector-context-title">
        <div className="connector-context-heading">
          <div><strong id="connector-context-title"><ShieldCheck size={14} />Internal context (read-only)</strong><small>Request-scoped aggregate counts · raw records and credentials stay out of the console</small></div>
          <button className="secondary compact" type="button" onClick={loadContext} disabled={contextLoading}>{contextLoading ? <><RefreshCw size={14} className="spin" />Reading…</> : <><RefreshCw size={14} />Refresh context</>}</button>
        </div>
        {contextError && <p className="connector-context-error" role="alert"><AlertCircle size={14} />{contextError}</p>}
        {context && <div className="connector-context-grid">
          {connectorOrder.map((system) => {
            const key = system.toLowerCase();
            const summary = context.connectors?.[key] || {};
            const binding = health?.checks?.find((item) => item.connector === key);
            const healthy = summary.status === "ok" && (!binding || binding.status === "healthy");
            return <div className="connector-context-card" key={system}>
              <span className={healthy ? "connector-context-status ready" : "connector-context-status"}>{healthy ? <CheckCircle2 size={13} /> : <AlertCircle size={13} />}{healthy ? "Read verified" : (summary.status || binding?.status || "Attention")}</span>
              <strong>{system}</strong>
              <small>{aggregateLabel(system, summary)}</small>
            </div>;
          })}
        </div>}
      </div>}
      <div className="integration-list">
        {targets.map((target) => {
          const Icon = icons[target.system] || Hash;
          const status = statusFor(target);
          return (
            <div className="integration-row" key={target.system}>
              <span className="integration-icon"><Icon size={16} /></span>
              <span className="integration-copy"><strong>{target.system}</strong><small>{target.description}</small></span>
              <span className={`integration-status ${status.written ? "ready" : "waiting"}`}>{status.written ? <CheckCircle2 size={14} /> : <Hash size={13} />}{status.label}</span>
              <span className="integration-count">{target.artifact_count} {target.artifact_count === 1 ? "surface" : "surfaces"}</span>
            </div>
          );
        })}
      </div>
      <footer className="integration-footer">
        {writes.length
          ? <>Connector writes: <strong>{writes.join(" · ")}</strong>. Each status is idempotent and reversible.</>
          : dismissed
            ? <>External writes: <strong>No</strong> · Signal intentionally dismissed; no packet, task, or connector handoff was created.</>
          : <>External writes: <strong>No</strong> · Public packets are ready for review; signed operator approval is required for configured connectors.</>}
      </footer>
    </section>
  );
}
