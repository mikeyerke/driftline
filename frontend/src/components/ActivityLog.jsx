import { CheckCircle2, ChevronRight, Clock3 } from "lucide-react";

const completedOutcomes = new Set([
  "verified",
  "change_detected",
  "4_artifacts_mapped",
  "4_updates_drafted",
  "approval_recorded",
  "decision_reopened",
]);

export default function ActivityLog({ events = [] }) {
  const formatLabel = (value) => (value || "").replace(/_/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
  const formatTime = (timestamp) => {
    if (!timestamp) return "Synthetic fixture";
    const date = new Date(timestamp);
    return Number.isNaN(date.valueOf()) ? "Synthetic fixture" : date.toLocaleTimeString();
  };

  return (
    <section className="panel activity-log">
      <header className="panel-header simple">
        <div><h2>Activity</h2><span className="live-label">Recorded</span><span className="muted">Workflow audit</span></div>
      </header>
        <div className="activity-grid activity-heading"><span>Time</span><span>Activity</span><span>Stage</span><span>Evidence</span><span>Outcome</span></div>
      {events.length === 0 && <p className="empty-state">Run the scan while the API is connected to create audit events.</p>}
      {events.map((event) => {
        const outcome = event.outcome || "recorded";
        const completed = completedOutcomes.has(outcome);
        return (
          <div className="activity-grid" key={event.event_id || (event.timestamp + "-" + event.action)}>
            <span><ChevronRight size={14} />{formatTime(event.timestamp)}</span>
            <span>{formatLabel(event.action || "workflow event")}</span>
            <span>{formatLabel(event.stage || "workflow")}</span>
            <span className="evidence-link" title={event.evidence_hash || event.event_id}>{event.evidence_hash ? `${event.evidence_hash.slice(0, 12)}…` : event.event_id || "audit event"}</span>
            <span className={"outcome " + (completed ? "success" : "queued")}>
              {completed ? <CheckCircle2 size={14} /> : <Clock3 size={14} />}
              {formatLabel(outcome)}
            </span>
          </div>
        );
      })}
    </section>
  );
}
