import { CheckCircle2, FileText, GitPullRequest, Hash, MessageSquare, TicketCheck } from "lucide-react";

const icons = { Jira: TicketCheck, Confluence: FileText, Slack: MessageSquare, GitHub: GitPullRequest };

export default function IntegrationPanel({ targets = [], approved }) {
  if (!targets.length) return null;
  return (
    <section className="panel integration-panel" aria-labelledby="integration-title">
      <header className="panel-header">
        <div><h2 id="integration-title">PMM handoff destinations</h2><span className="live-label">Approval-gated</span></div>
        <span className="muted">No silent writes</span>
      </header>
      <p className="integration-intro">Driftline turns the impact map into target-specific packets. After approval, owners can send these to the systems where work actually lives.</p>
      <div className="integration-list">
        {targets.map((target) => {
          const Icon = icons[target.system] || Hash;
          return (
            <div className="integration-row" key={target.system}>
              <span className="integration-icon"><Icon size={16} /></span>
              <span className="integration-copy"><strong>{target.system}</strong><small>{target.description}</small></span>
              <span className={`integration-status ${approved ? "ready" : "waiting"}`}>{approved ? <CheckCircle2 size={14} /> : <Hash size={13} />}{approved ? "Packet ready" : "Prepared"}</span>
              <span className="integration-count">{target.artifact_count} {target.artifact_count === 1 ? "surface" : "surfaces"}</span>
            </div>
          );
        })}
      </div>
      <footer className="integration-footer">External write: <strong>No</strong> · Connector status is explicit and reversible.</footer>
    </section>
  );
}
