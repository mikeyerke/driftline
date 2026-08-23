import { AlertTriangle, ArrowRight, CheckCircle2, Clock3, History, Play, ShieldCheck } from "lucide-react";

function openItems(items) {
  return (items || []).filter((item) => !["completed", "reversed"].includes(item.status));
}

/**
 * Keep the console pointed at the operator's next useful move.
 *
 * Driftline's value is the change-to-work loop, not the number of panels on
 * the page. This small rail turns the current workflow state into one clear,
 * reversible action without pretending a connector or customer outcome exists.
 */
export default function UtilityNextStep({ workflow, job, scanning, sourcePaused, onRunScan, onNavigate }) {
  const items = workflow?.action_items || [];
  const open = openItems(items);
  const pendingApproval = workflow?.status === "needs_approval";
  const approved = workflow?.status === "complete";
  const dismissed = workflow?.status === "dismissed";
  const monitorNoOp = !workflow && job?.status === "complete" && job?.source_status === "unchanged";
  const monitorBaseline = !workflow && job?.status === "complete" && job?.source_status === "baseline_established";
  const monitorFailed = !workflow && job?.status === "complete" && job?.source_status === "source_fetch_failed";
  const reconciliationRequired = workflow?.status === "reconciliation_required";
  const operationExecuting = ["approval_executing", "reversal_executing"].includes(workflow?.status);

  if (reconciliationRequired || operationExecuting) {
    return (
      <section className={`utility-next-step ${reconciliationRequired ? "failed" : "execute"}`} aria-label="Next best action">
        <span className="utility-next-step-icon">{reconciliationRequired ? <AlertTriangle size={16} /> : <Clock3 size={16} />}</span>
        <div><strong>{reconciliationRequired ? "Confirm the claimed operation" : "A durable operation is in progress"}</strong><p>{reconciliationRequired ? "Driftline blocked conflicting decisions and preserved the operation ID for an idempotent retry." : "The action was claimed before side effects began; wait for the durable receipt."}</p></div>
        <button className="primary compact" type="button" onClick={() => onNavigate?.("approvals-section")}>{reconciliationRequired ? "Open recovery" : "View operation"}<ArrowRight size={14} /></button>
      </section>
    );
  }

  if (monitorFailed) {
    return (
      <section className="utility-next-step failed" aria-label="Next best action">
        <span className="utility-next-step-icon"><AlertTriangle size={16} /></span>
        <div><strong>Source monitor needs attention</strong><p>The exact source could not be fetched. No workflow or business change was created; Scheduler will retry the bounded source.</p></div>
        <div className="utility-next-step-actions">
          <button className="secondary compact" type="button" onClick={onRunScan} disabled={scanning || sourcePaused} title={sourcePaused ? "Resume this source before retrying" : undefined}>{scanning ? "Retrying…" : sourcePaused ? "Source paused" : "Retry now"}<ArrowRight size={14} /></button>
          <button className="text-button compact" type="button" onClick={() => onNavigate?.("sources-section")}>Inspect source health</button>
        </div>
      </section>
    );
  }

  if (monitorNoOp || monitorBaseline) {
    return (
      <section className="utility-next-step monitor" aria-label="Next best action">
        <span className="utility-next-step-icon"><History size={16} /></span>
        <div><strong>{monitorNoOp ? "No material change found" : "Baseline captured"}</strong><p>{monitorNoOp ? "The source hash matched its prior observation, so Driftline created no noisy workflow. Continue on the next cadence or inspect the append-only history." : "Driftline recorded the first bounded observation without inventing a change. The next read will establish whether the source actually moved."}</p></div>
        <button className="secondary compact" type="button" onClick={() => onNavigate?.("sources-section")}>Open source history<ArrowRight size={14} /></button>
      </section>
    );
  }

  if (!workflow) {
    return (
      <section className={`utility-next-step ready${scanning ? " scanning" : ""}`} aria-label="Next best action">
        <span className="utility-next-step-icon"><Play size={16} /></span>
        <div><strong>{scanning ? "Gemini + ADK are tracing the change" : "Turn this source change into owner-ready work"}</strong><p>{scanning ? "Verifying the evidence and mapping every affected surface. No action can bypass the human gate." : "Watch Gemini + ADK verify the evidence, map downstream work, and stop at a human decision."}</p></div>
        <button className="primary compact" type="button" onClick={onRunScan} disabled={scanning || sourcePaused} title={sourcePaused ? "Resume this source before scanning" : undefined}>{scanning ? "Agent running…" : sourcePaused ? "Source paused" : "Run live agent"}<ArrowRight size={14} /></button>
      </section>
    );
  }

  if (pendingApproval) {
    const count = workflow.impact_graph?.summary?.artifact_count || workflow.impacts?.length || 0;
    return (
      <section className="utility-next-step review" aria-label="Next best action">
        <span className="utility-next-step-icon"><ShieldCheck size={16} /></span>
        <div><strong>Compare the evidence-cited response plans</strong><p>Gemini mapped {count} downstream surface{count === 1 ? "" : "s"}. Choose the narrowest safe plan, then approve or dismiss it.</p></div>
        <button className="primary compact" type="button" onClick={() => onNavigate?.("approvals-section")}>Review decision<ArrowRight size={14} /></button>
      </section>
    );
  }

  if (approved && open.length > 0) {
    const next = open[0];
    return (
      <section className="utility-next-step execute" aria-label="Next best action">
        <span className="utility-next-step-icon"><Clock3 size={16} /></span>
        <div><strong>Next move: put the decision to work</strong><p><b>{next.owner}</b> owns <b>{next.artifact}</b>. Claim it to start the auditable closure loop.</p></div>
        <button className="primary compact" type="button" onClick={() => onNavigate?.("actions-section")}>Open owner queue<ArrowRight size={14} /></button>
      </section>
    );
  }

  return (
    <section className={`utility-next-step${dismissed ? " dismissed" : " complete"}`} aria-label="Next best action">
      <span className="utility-next-step-icon"><CheckCircle2 size={16} /></span>
      <div><strong>{dismissed ? "Signal dismissed with an audit trail" : "Decision recorded; closure is complete"}</strong><p>{dismissed ? "Keep the evidence in change memory and reopen only if a new source observation warrants work." : "The packet is durable and reversible. Use the audit history to confirm what changed and when."}</p></div>
      <button className="secondary compact" type="button" onClick={() => onNavigate?.("activity-section")}>Open audit<ArrowRight size={14} /></button>
    </section>
  );
}
