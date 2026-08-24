import { Activity, AlertTriangle, CheckCircle2, Database, FlaskConical, History, RotateCcw } from "lucide-react";

function shortHash(value) {
  return value ? `${value.slice(0, 12)}…` : "pending";
}

export default function LearningReceipt({ decisionCase, evaluation, busy, onOutcome }) {
  const active = decisionCase.status === "experiment_active";
  const reopened = decisionCase.status === "reopened";
  const plan = decisionCase.experiment_plan;
  const currentGenerationPrefix = `outcome-g${decisionCase.generation}-`;
  const currentOutcome = decisionCase.outcomes
    .filter((outcome) => outcome.observation_id.startsWith(currentGenerationPrefix))
    .at(-1);
  return (
    <section className={`decision-room-section learning-receipt${reopened ? " reopened" : ""}`} aria-labelledby="learning-receipt-title" aria-live="polite">
      <header className="decision-room-section-header">
        <div><span className="decision-room-kicker">What we learned</span><h3 id="learning-receipt-title">{reopened ? "New evidence changed the decision" : active ? "A test is running" : "Decision recorded"}</h3></div>
        {evaluation && <span className={`evaluation-gate ${evaluation.gate_status}`}>{evaluation.passed_case_count}/{evaluation.case_count} policy checks</span>}
      </header>
      {plan && <div className="experiment-contract">
        <div><FlaskConical size={20} /><span><strong>{plan.hypothesis}</strong><small>{plan.target_segment.replaceAll("_", " ")} · review {new Date(plan.review_at).toLocaleDateString()}</small></span></div>
        <dl><div><dt>Primary metric</dt><dd>{plan.primary_metric.replaceAll("_", " ")}</dd></div><div><dt>Success</dt><dd>{plan.success_condition}</dd></div><div><dt>Stop</dt><dd>{plan.stop_conditions[0]}</dd></div></dl>
      </div>}
      {reopened && <div className="reopen-alert"><AlertTriangle size={22} /><div><strong>Generation {decisionCase.generation} reopened for human review</strong><p>{decisionCase.reopen_reason}</p><small>The original approval and outcome remain preserved in decision memory.</small></div></div>}
      <div className="learning-proof-grid" aria-label="Four-part decision proof">
        <div><Database size={17} /><span><strong>Decision state</strong><small>Saved · round {decisionCase.generation}</small></span></div>
        <div><Activity size={17} /><span><strong>Evidence record</strong><small>{shortHash(decisionCase.council.evidence_manifest_hash)}</small></span></div>
        <div><CheckCircle2 size={17} /><span><strong>Decision record</strong><small>{shortHash(decisionCase.council.synthesis_hash)}</small></span></div>
        <div>{currentOutcome ? <History size={17} /> : <RotateCcw size={17} />}<span><strong>{currentOutcome ? "Outcome observed" : "Rollback path"}</strong><small>{currentOutcome?.evaluation?.verdict || (plan?.reversible ? "Available" : "Prepared")}</small></span></div>
      </div>
      <details className="decision-proof-details"><summary>View audit details</summary><dl><div><dt>Case</dt><dd>{decisionCase.case_id}</dd></div><div><dt>Evidence</dt><dd>{decisionCase.council.evidence_manifest_hash}</dd></div><div><dt>Decision</dt><dd>{decisionCase.council.synthesis_hash}</dd></div>{currentOutcome && <div><dt>Outcome</dt><dd>{currentOutcome.observation_id} · {currentOutcome.content_hash}</dd></div>}</dl></details>
      {active && <button className="primary decision-outcome-button" type="button" onClick={onOutcome} disabled={busy}><Activity size={17} />{busy ? "Evaluating outcome…" : "Advance to measured outcome"}</button>}
      {active && <p className="fixture-disclosure">Runs a pinned aggregate measurement fixture for the judge demo; it is not presented as customer validation.</p>}
    </section>
  );
}
