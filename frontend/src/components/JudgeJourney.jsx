import { ArrowRight, CheckCircle2, FileSearch, ShieldCheck, Undo2 } from "lucide-react";

const steps = [
  {
    id: "evidence-section",
    label: "Evidence",
    detail: "Verify the source change",
    Icon: FileSearch,
  },
  {
    id: "approvals-section",
    label: "Human decision",
    detail: "Choose a bounded response",
    Icon: ShieldCheck,
  },
  {
    id: "actions-section",
    label: "Reversible action",
    detail: "Create owner-ready work",
    Icon: Undo2,
  },
];

export default function JudgeJourney({ workflow, scanning, onNavigate }) {
  const hasEvidence = Boolean(workflow);
  const resolved = ["complete", "dismissed"].includes(workflow?.status);
  const activeIndex = !hasEvidence ? 0 : resolved ? 2 : 1;

  return (
    <nav className="judge-journey" aria-label="Driftline workflow">
      {steps.map(({ id, label, detail, Icon }, index) => {
        const complete = index < activeIndex;
        const current = index === activeIndex;
        const target = id === "actions-section" && !workflow?.action_items?.length ? "approvals-section" : id;
        return (
          <div className="judge-journey-item" key={id}>
            <button
              className={`judge-journey-step${complete ? " complete" : ""}${current ? " current" : ""}`}
              type="button"
              onClick={() => onNavigate?.(target)}
              aria-current={current ? "step" : undefined}
            >
              <span className="judge-journey-icon">{complete ? <CheckCircle2 size={17} /> : <Icon size={17} />}</span>
              <span><strong>{label}</strong><small>{current && scanning ? "Agent tracing the change…" : detail}</small></span>
            </button>
            {index < steps.length - 1 && <ArrowRight className="judge-journey-arrow" size={15} aria-hidden="true" />}
          </div>
        );
      })}
    </nav>
  );
}
