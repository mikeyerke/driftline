import { Check } from "lucide-react";

const steps = ["Monitor", "Verify", "Map impact", "Draft updates", "Await approval", "Publish"];

export default function WorkflowTimeline({ approved }) {
  return (
    <section className="workflow-timeline" aria-label="Workflow progress">
      {steps.map((step, index) => {
        const complete = approved ? index < 5 : index < 4;
        const active = approved ? index === 5 : index === 4;
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

