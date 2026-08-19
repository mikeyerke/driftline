import { Check, Circle, Clock3, GitBranch } from "lucide-react";

const labels = {
  source_monitor: "Change detected",
  evidence_verifier: "Evidence verified",
  impact_mapper: "Business impact mapped",
  content_orchestrator: "Owner packets drafted",
  policy_gate: "Human decision requested",
  bounded_packet: "Handoff packet prepared",
  bounded_publisher: "Approved outputs created",
};

function timeLabel(value) {
  if (!value) return "Synthetic fixture";
  const date = new Date(value);
  return Number.isNaN(date.valueOf()) ? "Recorded" : date.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
}

export default function ChangeTimeline({ state }) {
  const events = state?.events || [];
  if (!events.length) return null;
  const visible = events.filter((event) => labels[event.action] || event.outcome === "decision_reopened").slice(-7);
  return (
    <section className="panel change-timeline" aria-labelledby="change-timeline-title">
      <header className="panel-header">
        <div><h2 id="change-timeline-title">Change timeline</h2><span className="live-label public"><GitBranch size={12} />Evidence chain</span></div>
        <span className="muted">Why this action exists</span>
      </header>
      <div className="change-timeline-list">
        {visible.map((event, index) => {
          const isComplete = index < visible.length - 1 || state.status === "complete";
          const label = labels[event.action] || (event.outcome === "decision_reopened" ? "Decision reopened" : "Recorded event");
          return (
            <div className={`change-timeline-item ${isComplete ? "complete" : "current"}`} key={event.event_id || `${event.action}-${index}`}>
              <span className="change-timeline-line" />
              <span className="change-timeline-dot">{isComplete ? <Check size={13} /> : <Circle size={9} fill="currentColor" />}</span>
              <span className="change-timeline-copy"><strong>{label}</strong><small>{event.outcome?.replaceAll("_", " ") || "Evidence-bound transition"}</small></span>
              <span className="change-timeline-time">{timeLabel(event.timestamp)}</span>
            </div>
          );
        })}
      </div>
      <footer className="change-timeline-footer"><Clock3 size={13} />A model can propose the chain; only a named human can cross the gate.</footer>
    </section>
  );
}
