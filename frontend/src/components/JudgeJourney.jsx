import { ArrowRight, CheckCircle2, FileSearch, ReceiptText, ShieldCheck, Sparkles, Undo2 } from "lucide-react";

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
  {
    id: "proof-section",
    label: "Proof",
    detail: "Inspect the durable receipt",
    Icon: ReceiptText,
  },
];

export default function JudgeJourney({ workflow, scanning, judgeMode, onToggleJudgeMode, onNavigate }) {
  const hasEvidence = Boolean(workflow);
  const resolved = workflow?.status === "complete";
  const dismissed = workflow?.status === "dismissed";
  const operating = ["approval_executing", "reversal_executing", "reconciliation_required"].includes(workflow?.status);
  const activeIndex = !hasEvidence ? 0 : resolved ? 3 : 1;

  return (
    <section className={`judge-mode-shell${judgeMode ? " active" : ""}`} aria-label="Judge mode">
      <header className="judge-mode-header">
        <div><Sparkles size={15} /><span><strong>Judge Mode</strong><small>One guided path from evidence to durable proof</small></span></div>
        <button className={judgeMode ? "judge-mode-toggle active" : "judge-mode-toggle"} type="button" aria-pressed={judgeMode} onClick={onToggleJudgeMode}>{judgeMode ? "Guided · on" : "Guided · off"}</button>
      </header>
      <nav className="judge-journey" aria-label="Driftline workflow">
      {steps.map(({ id, label, detail, Icon }, index) => {
        const complete = index < activeIndex;
        const current = index === activeIndex;
        const target = (id === "actions-section" && !workflow?.action_items?.length) || (id === "proof-section" && !resolved) ? "approvals-section" : id;
        return (
          <div className="judge-journey-item" key={id}>
            <button
              className={`judge-journey-step${complete ? " complete" : ""}${current ? " current" : ""}`}
              type="button"
              onClick={() => onNavigate?.(target)}
              aria-current={current ? "step" : undefined}
            >
              <span className="judge-journey-icon">{complete ? <CheckCircle2 size={17} /> : <Icon size={17} />}</span>
              <span><strong>{label}</strong><small>{current && scanning ? "Agent tracing the change…" : current && dismissed ? "Signal dismissed · no action created" : current && operating ? "Recover the claimed operation" : detail}</small></span>
            </button>
            {index < steps.length - 1 && <ArrowRight className="judge-journey-arrow" size={15} aria-hidden="true" />}
          </div>
        );
      })}
      </nav>
    </section>
  );
}
