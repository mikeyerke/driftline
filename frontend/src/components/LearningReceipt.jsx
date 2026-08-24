import { Activity, AlertTriangle, CheckCircle2, ClipboardList, Database, FlaskConical, History, RotateCcw } from "lucide-react";

function shortHash(value) {
  return value ? `${value.slice(0, 12)}…` : "pending";
}

export default function LearningReceipt({ decisionCase, evaluation, busy, onOutcome }) {
  const active = decisionCase.status === "experiment_active";
  const reopened = decisionCase.status === "reopened";
  const plan = decisionCase.experiment_plan;
  const currentGenerationPrefix = `outcome-g${decisionCase.generation}-`;
  const latestOutcome = [...decisionCase.outcomes].reverse().find((outcome) => (
    outcome.observation_id && outcome.observation_id.startsWith(currentGenerationPrefix)
  ));
  return (
    <section className={`decision-room-section learning-receipt${reopened ? " reopened" : ""}`} aria-labelledby="learning-receipt-title" aria-live="polite">
      <header className="decision-room-section-header">
        <div><span className="decision-room-kicker">Action + learning</span><h3 id="learning-receipt-title">{reopened ? "The outcome changed the decision" : active ? "The approved action is now measurable" : "Decision memory is ready"}</h3><p className="section-dek">Driftline keeps the owner handoff, guardrail, and outcome attached to the same decision.</p></div>
        {evaluation && <span className={`evaluation-gate ${evaluation.gate_status}`}>{evaluation.passed_case_count}/{evaluation.case_count} policy checks</span>}
      </header>
      {plan && <div className="experiment-contract">
        <div><FlaskConical size={20} /><span><strong>{plan.hypothesis}</strong><small>{plan.target_segment.replaceAll("_", " ")} · review {new Date(plan.review_at).toLocaleDateString()}</small></span></div>
        <dl><div><dt>Primary metric</dt><dd>{plan.primary_metric.replaceAll("_", " ")}</dd></div><div><dt>Success</dt><dd>{plan.success_condition}</dd></div><div><dt>Stop</dt><dd>{plan.stop_conditions[0]}</dd></div></dl>
      </div>}
      {plan?.owner_actions?.length > 0 && <section className="owner-action-list" aria-labelledby="owner-action-title">
        <header><ClipboardList size={17} /><strong id="owner-action-title">Owner handoff prepared</strong><span>{plan.owner_actions.length} bounded actions</span></header>
        <ul>{plan.owner_actions.map((action) => <li key={action}><CheckCircle2 size={14} />{action}</li>)}</ul>
      </section>}
      {reopened && <div className="reopen-alert"><AlertTriangle size={22} /><div><strong>Generation {decisionCase.generation} reopened for human review</strong><p>{decisionCase.reopen_reason}</p><small>The original approval and outcome remain preserved in decision memory.</small></div></div>}
      <div className="learning-proof-grid" aria-label="Four-part decision proof">
        <div><Database size={17} /><span><strong>Decision state</strong><small>Firestore-ready generation {decisionCase.generation}</small></span></div>
        <div><Activity size={17} /><span><strong>Evidence manifest</strong><small>{shortHash(decisionCase.council.evidence_manifest_hash)}</small></span></div>
        <div><CheckCircle2 size={17} /><span><strong>Council synthesis</strong><small>{shortHash(decisionCase.council.synthesis_hash)}</small></span></div>
        <div>{latestOutcome ? <History size={17} /> : <RotateCcw size={17} />}<span><strong>{latestOutcome ? "Outcome observed" : "Rollback path"}</strong><small>{latestOutcome?.evaluation?.verdict || (plan?.reversible ? "Available" : "Prepared")}</small></span></div>
      </div>
      <details className="decision-proof-details"><summary>Inspect IDs and policy lineage</summary><dl><div><dt>Case</dt><dd>{decisionCase.case_id}</dd></div><div><dt>Evidence</dt><dd>{decisionCase.council.evidence_manifest_hash}</dd></div><div><dt>Synthesis</dt><dd>{decisionCase.council.synthesis_hash}</dd></div>{latestOutcome && <div><dt>Outcome</dt><dd>{latestOutcome.observation_id} · {latestOutcome.content_hash}</dd></div>}</dl></details>
      {active && <button className="primary decision-outcome-button" type="button" onClick={onOutcome} disabled={busy}><Activity size={17} />{busy ? "Evaluating outcome…" : "Advance to measured outcome"}</button>}
      {active && <p className="fixture-disclosure">Runs a pinned aggregate measurement fixture for the judge demo; it is not presented as customer validation.</p>}
    </section>
  );
}
