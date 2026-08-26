import { Activity, AlertTriangle, CheckCircle2, ClipboardList, Database, FlaskConical, History, RotateCcw } from "lucide-react";
import { useState } from "react";

function shortHash(value) {
  return value ? `${value.slice(0, 12)}…` : "pending";
}

export default function LearningReceipt({ decisionCase, evaluation, busy, monitoring, fixtureEligible, onOutcome, onMeasuredOutcome }) {
  const active = decisionCase.status === "experiment_active";
  const inconclusive = decisionCase.status === "inconclusive";
  const validated = decisionCase.status === "validated";
  const reopened = decisionCase.status === "reopened";
  const terminalReview = decisionCase.status === "review_required";
  const plan = decisionCase.experiment_plan;
  const currentGenerationPrefix = `outcome-g${decisionCase.generation}-`;
  const generationOutcomes = decisionCase.outcomes.filter((outcome) => (
    outcome.observation_id && outcome.observation_id.startsWith(currentGenerationPrefix)
  ));
  const currentOutcome = generationOutcomes[generationOutcomes.length - 1];
  const currentMeasurementGroup = currentOutcome?.observation_id?.replace(/-(primary|risk)$/, "");
  const currentOutcomes = currentMeasurementGroup === currentOutcome?.observation_id
    ? generationOutcomes
    : generationOutcomes.filter((outcome) => (
      outcome.observation_id.startsWith(`${currentMeasurementGroup}-`)
    ));
  const triggerOutcome = (reopened || terminalReview) ? decisionCase.decision_history?.[decisionCase.decision_history.length - 1]?.trigger_observation : null;
  const latestOutcome = triggerOutcome || currentOutcome;
  const latestAction = [...(decisionCase.action_records || [])].reverse()[0];
  const actionApproval = decisionCase.approval || decisionCase.decision_history?.at(-1)?.approval;
  const [measurement, setMeasurement] = useState({
    sourceLabel: "",
    primaryValue: "",
    riskValue: "",
  });
  const measurementPending = !fixtureEligible && (active || inconclusive);
  const reviewAt = plan ? Date.parse(plan.review_at) : Number.NaN;
  const measurementWindowOpen = Number.isFinite(reviewAt) && Date.now() >= reviewAt;
  const actionTitle = latestAction?.status === "rolled_back"
    ? "Guardrail rolled the internal action back"
    : latestAction?.status === "completed"
      ? "Bounded internal action completed"
      : "Bounded internal action executed";
  return (
    <section className={`decision-room-section learning-receipt${reopened ? " reopened" : ""}`} aria-labelledby="learning-receipt-title" aria-live="polite">
      <header className="decision-room-section-header">
        <div><span className="decision-room-kicker">Action + learning</span><h3 id="learning-receipt-title" tabIndex="-1">{terminalReview ? "Generation limit reached—human review required" : reopened ? "The outcome changed the decision" : validated ? "The action completed inside its guardrail" : measurementPending ? "Attach the real measurement when the review window closes" : active ? "The approved action is now measurable" : "Decision memory is ready"}</h3><p className="section-dek">Driftline keeps the owner follow-through, guardrail, and outcome attached to the same decision.</p></div>
        {evaluation && <span className={`evaluation-gate ${evaluation.gate_status}`}>{evaluation.passed_case_count}/{evaluation.case_count} policy checks</span>}
      </header>
      {plan && <div className="experiment-contract">
        <div><FlaskConical size={20} /><span><strong>{plan.hypothesis}</strong><small>{plan.target_segment.replaceAll("_", " ")} · review {new Date(plan.review_at).toLocaleDateString()}</small></span></div>
        <dl><div><dt>Primary metric</dt><dd>{plan.primary_metric.replaceAll("_", " ")}</dd></div>{plan.risk_metric && <div><dt>Risk metric</dt><dd>{plan.risk_metric.replaceAll("_", " ")}</dd></div>}<div><dt>Success</dt><dd>{plan.success_condition}</dd></div><div><dt>Stop</dt><dd>{plan.stop_conditions[0]}</dd></div>{plan.owner && <div><dt>Owner</dt><dd>{plan.owner}</dd></div>}</dl>
      </div>}
      {latestAction && <section className={`bounded-action-record ${latestAction.status}`} aria-labelledby="bounded-action-title">
        <div>{latestAction.status === "rolled_back" ? <RotateCcw size={19} /> : <Activity size={19} />}<span><strong id="bounded-action-title">{actionTitle}</strong><small>{latestAction.status === "rolled_back" ? "Driftline reversed the allocation automatically when the measured outcome crossed the approved stop condition." : latestAction.status === "completed" ? "Driftline completed the internal allocation after the primary outcome met success and the risk metric remained inside its guardrail." : `Driftline created an internal allocation record for ${latestAction.target_segment.replaceAll("_", " ")} after human approval.`}</small>{actionApproval && <small className="bounded-action-approver"><b>Named human approval</b> · {actionApproval.approver} · {new Date(actionApproval.approved_at).toLocaleString()}</small>}</span></div>
        <dl><div><dt>Generation</dt><dd>{latestAction.generation}</dd></div><div><dt>Status</dt><dd>{latestAction.status.replaceAll("_", " ")}</dd></div><div><dt>Scope</dt><dd>Decision state only</dd></div><div><dt>External writes</dt><dd>None</dd></div></dl>
      </section>}
      {currentOutcomes.length > 0 && <section className="measured-outcome-summary" aria-labelledby="measured-outcome-title">
        <header><Database size={17} /><strong id="measured-outcome-title">Observed measurement</strong><span>PM-provided · unverified</span></header>
        <dl>{currentOutcomes.map((outcome) => <div key={outcome.observation_id}><dt>{outcome.metric_id}</dt><dd>{outcome.value} {outcome.unit}</dd><small>{outcome.evaluation?.verdict}</small></div>)}</dl>
      </section>}
      {plan?.owner_actions?.length > 0 && <section className="owner-action-list" aria-labelledby="owner-action-title">
        <header><ClipboardList size={17} /><strong id="owner-action-title">Owner follow-through attached</strong><span>{plan.owner_actions.length} bounded steps</span></header>
        <ul>{plan.owner_actions.map((action) => <li key={action}><CheckCircle2 size={14} />{action}</li>)}</ul>
      </section>}
      {reopened && <div className="reopen-alert"><AlertTriangle size={22} /><div><strong>Generation {decisionCase.generation} reopened for human review</strong><p>{decisionCase.reopen_reason}</p><small>The original approval and outcome remain preserved in decision memory.</small></div></div>}
      {terminalReview && <div className="reopen-alert"><AlertTriangle size={22} /><div><strong>Automation stopped at generation {decisionCase.generation}</strong><p>{decisionCase.reopen_reason}</p><small>The breached outcome is durable; a human must resolve or archive this decision outside the automatic generation loop.</small></div></div>}
      <div className="learning-proof-grid" aria-label="Four-part decision proof">
        <div><Database size={17} /><span><strong>Decision state</strong><small>Firestore-ready generation {decisionCase.generation}</small></span></div>
        <div><Activity size={17} /><span><strong>Evidence manifest</strong><small>{shortHash(decisionCase.council.evidence_manifest_hash)}</small></span></div>
        <div><CheckCircle2 size={17} /><span><strong>Council synthesis</strong><small>{shortHash(decisionCase.council.synthesis_hash)}</small></span></div>
        <div>{latestOutcome ? <History size={17} /> : <RotateCcw size={17} />}<span><strong>{latestOutcome ? "Outcome observed" : "Rollback path"}</strong><small>{latestOutcome?.evaluation?.verdict || (plan?.reversible ? "Available" : "Prepared")}</small></span></div>
      </div>
      <details className="decision-proof-details"><summary>Inspect IDs and policy lineage</summary><dl><div><dt>Case</dt><dd>{decisionCase.case_id}</dd></div><div><dt>Evidence</dt><dd>{decisionCase.council.evidence_manifest_hash}</dd></div><div><dt>Synthesis</dt><dd>{decisionCase.council.synthesis_hash}</dd></div>{latestOutcome && <div><dt>Outcome</dt><dd>{latestOutcome.observation_id} · {latestOutcome.content_hash}</dd></div>}</dl></details>
      {active && monitoring && <div className="autonomous-monitor-status" role="status" aria-live="polite"><Activity size={18} /><span><strong>Autonomous monitor active</strong><small>Cloud Tasks is checking the approved guardrail. No second PM action is required.</small></span></div>}
      {active && fixtureEligible && !monitoring && <button className="secondary decision-outcome-button" type="button" onClick={onOutcome} disabled={busy}><Activity size={17} />{busy ? "Evaluating outcome…" : "Run demo measurement fallback"}</button>}
      {active && fixtureEligible && <p className="fixture-disclosure">The public judge lane automatically processes a pinned aggregate measurement fixture; it is not presented as customer validation.</p>}
      {measurementPending && !measurementWindowOpen && <div className="measurement-window-locked" role="status"><History size={18} /><span><strong>Measurement opens {Number.isFinite(reviewAt) ? new Date(reviewAt).toLocaleString() : "after a valid review date is restored"}</strong><small>Return with this decision link after the review window. The internal action remains active; Driftline will reject early measurements at the API boundary.</small></span></div>}
      {measurementPending && measurementWindowOpen && <form className="measured-outcome-form" onSubmit={(event) => {
        event.preventDefault();
        onMeasuredOutcome({
          ...measurement,
          measurementId: crypto.randomUUID().toLowerCase(),
        });
      }}>
        <header><Activity size={18} /><span><strong>Attach the PM-observed outcome</strong><small>Aggregate, non-confidential values only · retained as PM-provided and unverified</small></span></header>
        <div>
          <label><span>Measurement source</span><input required minLength="3" maxLength="120" value={measurement.sourceLabel} onChange={(event) => setMeasurement({ ...measurement, sourceLabel: event.target.value })} placeholder="Weekly product analytics" /></label>
          <label><span>{plan.primary_metric} ({plan.metric_unit})</span><input required type="number" step="any" value={measurement.primaryValue} onChange={(event) => setMeasurement({ ...measurement, primaryValue: event.target.value })} placeholder={String(plan.primary_baseline ?? "")} /></label>
          <label><span>{plan.risk_metric} ({plan.metric_unit})</span><input required type="number" step="any" value={measurement.riskValue} onChange={(event) => setMeasurement({ ...measurement, riskValue: event.target.value })} placeholder={String(plan.risk_baseline ?? "")} /></label>
        </div>
        <button className="secondary" type="submit" disabled={busy}><Activity size={17} />{busy ? "Attaching measurement…" : "Evaluate real measurement"}</button>
        <p>This never generates a synthetic result. The primary outcome and risk guardrail must both resolve before Driftline completes the action; a breached guardrail rolls it back.</p>
      </form>}
    </section>
  );
}
