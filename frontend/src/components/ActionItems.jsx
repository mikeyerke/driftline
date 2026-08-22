import { useMemo, useState } from "react";
import { AlertTriangle, Check, CircleDashed, ClipboardCheck, Filter, RotateCcw, UserRound } from "lucide-react";
import { claimAction, completeAction, failAction, retryAction } from "../api";

const label = (value) => (value || "queued").replace(/_/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());

export default function ActionItems({ workflowId, items, workflowStatus, onChange }) {
  const [busyId, setBusyId] = useState(null);
  const [error, setError] = useState("");
  const [filter, setFilter] = useState("all");
  const actionItems = items || [];
  const completedCount = actionItems.filter((item) => item.status === "completed").length;
  const closedCount = actionItems.filter((item) => ["completed", "reversed"].includes(item.status)).length;
  const outstandingCount = actionItems.length - closedCount;
  const reopened = workflowStatus === "needs_approval" && actionItems.length > 0 && actionItems.every((item) => item.status === "reversed");
  const visibleItems = useMemo(() => actionItems.filter((item) => {
    if (filter === "open") return !["completed", "reversed"].includes(item.status);
    if (filter === "closed") return ["completed", "reversed"].includes(item.status);
    return true;
  }), [filter, actionItems]);
  if (!actionItems.length) return null;

  const transition = async (item, operation) => {
    setBusyId(item.item_id);
    setError("");
    try {
      const next = operation === "claim"
        ? await claimAction(workflowId, item.item_id)
        : operation === "complete"
          ? await completeAction(workflowId, item.item_id)
          : operation === "fail"
            ? await failAction(workflowId, item.item_id)
            : await retryAction(workflowId, item.item_id);
      onChange(next);
    } catch (transitionError) {
      setError(transitionError.message || "Unable to update this action item");
    } finally {
      setBusyId(null);
    }
  };

  return (
    <section id="actions-section" className="panel action-items" aria-labelledby="action-items-title">
      <header className="panel-header">
        <div><h2 id="action-items-title">Owner action queue</h2><span className="live-label public">Human-owned</span></div>
        <span className="muted">{completedCount}/{items.length} completed · {closedCount}/{items.length} closed</span>
      </header>
      <p className="action-items-intro">{reopened ? "This decision was reopened. The reversed owner actions remain visible as append-only closure history; approve a new plan before creating new work." : `Approval created ${items.length} durable work ${items.length === 1 ? "item" : "items"}. ${outstandingCount ? `${outstandingCount} still need owner closure.` : "Every owner action is closed."}`} Driftline tracks ownership without pretending to update a CRM or customer system. Each row keeps its evidence hash and idempotency key so a retry cannot create duplicate work.</p>
      {error && <p className="trace-error action-items-error" role="alert">{error}</p>}
      <div className="action-item-filter" role="group" aria-label="Filter owner actions">
        <Filter size={13} aria-hidden="true" />
        {[['all', `All ${items.length}`], ['open', `Open ${outstandingCount}`], ['closed', `Closed ${closedCount}`]].map(([value, text]) => (
          <button key={value} type="button" className={`action-item-filter-button${filter === value ? " active" : ""}`} aria-pressed={filter === value} onClick={() => setFilter(value)}>{text}</button>
        ))}
      </div>
      <div className="action-item-list">
        {visibleItems.length === 0 && <p className="action-items-empty">No {filter} owner actions in this packet.</p>}
        {visibleItems.map((item) => (
          <div className="action-item-row" key={item.item_id}>
            <span className={`action-item-icon${item.status === "reversed" ? " reversed" : ""}`}>{item.status === "completed" ? <Check size={15} /> : item.status === "claimed" ? <ClipboardCheck size={15} /> : item.status === "failed" ? <AlertTriangle size={15} /> : item.status === "reversed" ? <RotateCcw size={15} /> : <CircleDashed size={15} />}</span>
            <span className="action-item-copy"><strong>{item.artifact}</strong><small><UserRound size={12} />{item.owner} · {item.priority || "medium"} priority</small><small title={item.evidence_hash ? `Evidence hash ${item.evidence_hash}` : undefined}>Evidence {item.evidence_hash ? `${item.evidence_hash.slice(0, 12)}…` : "not attached"} · {item.idempotency_key}</small></span>
            <span className={`action-item-status ${item.status}`}>{label(item.status)}</span>
            <small className={`action-item-due${item.due_at && new Date(item.due_at) < new Date() && !["completed", "reversed"].includes(item.status) ? " overdue" : ""}`}>{item.due_at ? `${item.due_at && new Date(item.due_at) < new Date() && !["completed", "reversed"].includes(item.status) ? "Overdue" : "Due"} ${new Date(item.due_at).toLocaleDateString()}` : "No due date"}</small>
            {item.status === "queued" && <button className="secondary compact" type="button" onClick={() => transition(item, "claim")} disabled={busyId === item.item_id}>{busyId === item.item_id ? "Claiming…" : "Claim"}</button>}
            {item.status === "claimed" && <span className="action-item-actions"><button className="primary compact" type="button" onClick={() => transition(item, "complete")} disabled={busyId === item.item_id}>{busyId === item.item_id ? "Completing…" : "Complete"}</button><button className="secondary compact" type="button" onClick={() => transition(item, "fail")} disabled={busyId === item.item_id} aria-label={`Mark ${item.artifact} failed`}><AlertTriangle size={13} />Fail</button></span>}
            {item.status === "failed" && <button className="secondary compact" type="button" onClick={() => transition(item, "retry")} disabled={busyId === item.item_id}>{busyId === item.item_id ? "Retrying…" : <><RotateCcw size={13} />Retry</>}</button>}
          </div>
        ))}
      </div>
    </section>
  );
}
