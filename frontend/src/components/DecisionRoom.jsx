import { ArrowRight, CheckCircle2, CircleAlert, LoaderCircle, Play, Sparkles } from "lucide-react";

function uniqueOwners(workflow) {
  const owners = [
    ...(workflow?.action_items || []).map((item) => item.owner),
    ...(workflow?.impacts || []).map((item) => item.owner),
  ];
  return [...new Set(owners.filter(Boolean))];
}

function recommendationFor(copilot) {
  return copilot?.options?.find((option) => option.option_id === copilot?.recommendation_id)
    || copilot?.options?.[0]
    || null;
}

function statusCopy(status) {
  if (status === "needs_approval") return { label: "Waiting for your approval", action: "Review owner work" };
  if (status === "complete") return { label: "Plan recorded", action: "View owner work" };
  if (status === "dismissed") return { label: "Signal dismissed", action: "View evidence" };
  return { label: "Review ready", action: "Open owner work" };
}

export default function DecisionRoom({ workflowState, job, scanning, scanMessage, scanFailed, scenarioTitle = "A competitor changed its pricing.", scenarioLabel = "competitor pricing", onRunReview, onOpenWorkflow }) {
  const workflow = workflowState || job?.workflow || null;
  const copilot = workflow?.agent_trace?.decision_copilot;
  const recommendation = recommendationFor(copilot);
  const owners = uniqueOwners(workflow);
  const actionCount = workflow?.action_items?.length || workflow?.impacts?.length || copilot?.artifact_count || 0;
  const status = statusCopy(workflow?.status);
  const explanation = copilot?.executive_summary
    || copilot?.summary
    || workflow?.agent_trace?.structured_analysis?.summary
    || "Review the affected work surfaces before updating the public response.";
  const optionList = copilot?.options?.slice(0, 3) || [];

  if (!workflow) {
    return (
      <section className="decision-room-hero" aria-labelledby="decision-room-hero-title">
        <div className="decision-room-hero-copy">
          <span className="decision-room-kicker"><Sparkles size={14} />Product Marketing + RevOps</span>
          <h2 id="decision-room-hero-title">{scenarioTitle}</h2>
          <p>Driftline verifies the change, shows which work needs updating, and prepares a reversible plan for the people who own it.</p>
          <div className="decision-room-hero-actions">
            <button className="primary decision-room-run" type="button" onClick={onRunReview} disabled={scanning}>
              {scanning ? <LoaderCircle className="spin" size={18} /> : <Play size={18} />}
              {scanning ? "Reviewing this change…" : "Review this change"}
            </button>
            <span>Example source · {scenarioLabel} · human approval</span>
          </div>
          {scanning && <p className="decision-room-status" role="status" aria-live="polite">Checking the source and mapping affected work…</p>}
          {scanFailed && scanMessage && <p className="decision-room-error" role="alert"><CircleAlert size={16} />{scanMessage}</p>}
        </div>
        <div className="decision-room-promise">
          <span className="decision-room-promise-label">The PMM/RevOps loop</span>
          <strong>From signal to owner work</strong>
          <p>One verified change, one clear plan, and one human decision.</p>
          <ol className="decision-room-steps">
            <li><b>1</b><span><strong>Verify the change</strong><small>Use the cited source evidence.</small></span></li>
            <li><b>2</b><span><strong>Map affected work</strong><small>See owners and surfaces at risk.</small></span></li>
            <li><b>3</b><span><strong>Approve or dismiss</strong><small>Keep every output reversible.</small></span></li>
          </ol>
          <small className="decision-room-safety">Public example · no external writes</small>
        </div>
      </section>
    );
  }

  return (
    <section className="decision-room decision-room-brief" aria-labelledby="decision-room-title">
      <header className="decision-room-header">
        <div>
          <span className="decision-room-kicker"><Sparkles size={14} />Recommended response</span>
          <h2 id="decision-room-title">{workflow.title || "Competitor pricing changed"}</h2>
          <p>One verified change, one owner plan, and one clear approval.</p>
        </div>
        <button className="secondary compact" type="button" onClick={onOpenWorkflow}>{status.action}<ArrowRight size={14} /></button>
      </header>
      <div className="decision-room-brief-grid">
        <section className="decision-room-recommendation" aria-labelledby="recommendation-title">
          <div className="decision-room-card-heading"><span>What Driftline recommends</span><b className={workflow.status === "complete" ? "complete" : ""}>{status.label}</b></div>
          <h3 id="recommendation-title">{recommendation?.title || "Review the owner plan"}</h3>
          <p>{recommendation?.summary || explanation}</p>
          <div className="decision-room-meta" aria-label="Plan summary">
            <span><strong>{actionCount}</strong> {actionCount === 1 ? "work surface" : "work surfaces"}</span>
            <span><strong>{owners.length || "—"}</strong> {owners.length === 1 ? "owner" : "owners"}</span>
            <span><strong>Human</strong> approval</span>
          </div>
        </section>
        <aside className="decision-room-why" aria-label="Recommendation explanation">
          <details className="decision-why">
            <summary>Why this recommendation</summary>
            <div className="decision-why-body">
              <p>{copilot?.rationale || explanation}</p>
              {optionList.length > 0 && <ul>
                {optionList.map((option) => <li key={option.option_id || option.title}><strong>{option.title}</strong><span>{option.summary || option.rationale || "Evidence-cited response plan"}</span></li>)}
              </ul>}
              <small>The AI can recommend; you decide.</small>
            </div>
          </details>
        </aside>
      </div>
      <div className={`decision-room-next ${workflow.status === "complete" ? "complete" : workflow.status === "dismissed" ? "dismissed" : ""}`}>
        <CheckCircle2 size={18} />
        <div><strong>{workflow.status === "complete" ? "The owner plan is recorded and reversible." : workflow.status === "dismissed" ? "The signal is dismissed with an audit trail." : "Your approval creates owner-ready work."}</strong><span>{workflow.status === "complete" ? "Open the supporting workflow to see the receipt and owner queue." : "Open the supporting workflow to inspect evidence, owners, and the approval gate."}</span></div>
        <button className={workflow.status === "complete" ? "secondary compact" : "primary compact"} type="button" onClick={onOpenWorkflow}>{workflow.status === "complete" ? "View the result" : "Open owner work"}<ArrowRight size={14} /></button>
      </div>
    </section>
  );
}
