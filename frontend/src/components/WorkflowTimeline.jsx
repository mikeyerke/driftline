import { Check } from "lucide-react";

const steps = ["Monitor", "Verify", "Map impact", "Draft updates", "Await approval", "Create outputs"];

export default function WorkflowTimeline({ state }) {
  const hasState = Boolean(state);
  const stageIndex = {
    monitor: 0,
    verify: 1,
    map_impact: 2,
    draft_updates: 3,
    await_approval: 4,
    publish: 5,
  }[state?.stage] ?? -1;
  const finished = state?.status === "complete";
  return (
    <section className="workflow-timeline" aria-label="Workflow progress">
      {steps.map((step, index) => {
        const complete = finished ? true : index < stageIndex;
        const active = hasState && !finished && index === stageIndex;
        const ready = !hasState && index === 0;
        return (
          <div className={`workflow-step ${complete ? "complete" : ""} ${active ? "active" : ""}`} key={step}>
            <span className="step-line" />
            <span className="step-dot">{complete ? <Check size={15} /> : ""}</span>
            <strong>{step}</strong>
            <small>{complete ? "Complete" : active ? "In progress" : ready ? "Ready to start" : "Queued"}</small>
          </div>
        );
      })}
    </section>
  );
}
