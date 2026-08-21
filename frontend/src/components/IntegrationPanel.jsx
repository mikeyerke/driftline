import { CheckCircle2, FileText, GitPullRequest, Hash, MessageSquare, TicketCheck } from "lucide-react";

const icons = { Jira: TicketCheck, Confluence: FileText, Slack: MessageSquare, GitHub: GitPullRequest };

export default function IntegrationPanel({ targets = [], approved, dismissed, actionRecord }) {
  if (!targets.length) return null;
  const statusKeys = { Jira: "jira_status", Confluence: "confluence_status", Slack: "slack_status", GitHub: "github_status" };
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
  return (
    <section className="panel integration-panel" aria-labelledby="integration-title">
      <header className="panel-header">
        <div><h2 id="integration-title">PMM handoff destinations</h2><span className="live-label">Approval-gated</span></div>
        <span className="muted">No silent writes</span>
      </header>
      <p className="integration-intro">Driftline turns the impact map into target-specific packets. The live public lane is packet-safe: it never mutates an external system. A separately authenticated tenant operator can enable a configured connector and execute only the signed, scoped handoff.</p>
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
