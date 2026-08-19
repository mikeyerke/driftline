import { Check } from "lucide-react";

const steps = ["Monitor", "Verify", "Map impact", "Draft updates", "Await approval", "Create outputs"];

export default function WorkflowTimeline({ state }) {
  const stageIndex = {
    monitor: 0,
    verify: 1,
    map_impact: 2,
    draft_updates: 3,
    await_approval: 4,
    publish: 5,
  }[state?.stage] ?? 0;
  const finished = state?.status === "complete";
  return (
    <section className="workflow-timeline" aria-label="Workflow progress">
      {steps.map((step, index) => {
        const complete = finished ? true : index < stageIndex;
        const active = !finished && index === stageIndex;
        return (
          <div className={`workflow-step ${complete ? "complete" : ""} ${active ? "active" : ""}`} key={step}>
            <span className="step-line" />
            <span className="step-dot">{complete ? <Check size={15} /> : ""}</span>
            <strong>{step}</strong>
            <small>{complete ? "Complete" : active ? "In progress" : "Queued"}</small>
          </div>
        );
      })}
    </section>
  );
}
