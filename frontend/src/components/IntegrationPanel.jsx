import { CheckCircle2, FileText, GitPullRequest, Hash, MessageSquare, TicketCheck } from "lucide-react";

const icons = { Jira: TicketCheck, Confluence: FileText, Slack: MessageSquare, GitHub: GitPullRequest };

export default function IntegrationPanel({ targets = [], approved, actionRecord }) {
  if (!targets.length) return null;
  const jiraStatus = actionRecord?.jira_status;
  const jiraWasWritten = jiraStatus === "created" || jiraStatus === "reused" || jiraStatus === "reversed";
  const statusFor = (target) => {
    if (!approved) return { label: "Prepared", written: false };
    if (target.system !== "Jira") return { label: "Packet ready", written: false };
    if (jiraStatus === "created") return { label: "Issue created", written: true };
    if (jiraStatus === "reused") return { label: "Issue reused", written: true };
    if (jiraStatus === "reversed") return { label: "Reversed", written: true };
    return { label: "Prepared only", written: false };
  };
  return (
    <section className="panel integration-panel" aria-labelledby="integration-title">
      <header className="panel-header">
        <div><h2 id="integration-title">PMM handoff destinations</h2><span className="live-label">Approval-gated</span></div>
        <span className="muted">No silent writes</span>
      </header>
      <p className="integration-intro">Driftline turns the impact map into target-specific packets. Only an explicitly configured connector may write after approval; every other destination remains prepared-only.</p>
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
        {jiraWasWritten
          ? <>Jira write: <strong>{jiraStatus === "created" ? "Issue created" : jiraStatus === "reused" ? "Existing issue reused" : "Reversed"}</strong> · Other destinations: <strong>prepared only</strong>.</>
          : <>External writes: <strong>No</strong> · Jira and other destinations are prepared-only until a connector is explicitly configured.</>}
      </footer>
    </section>
  );
}
