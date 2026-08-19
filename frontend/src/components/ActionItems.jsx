import { useState } from "react";
import { AlertTriangle, Check, CircleDashed, ClipboardCheck, RotateCcw, UserRound } from "lucide-react";
import { claimAction, completeAction, failAction, retryAction } from "../api";

const label = (value) => (value || "queued").replace(/_/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());

export default function ActionItems({ workflowId, items, onChange }) {
  const [busyId, setBusyId] = useState(null);
  const [error, setError] = useState("");
  if (!items?.length) return null;

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
    <section className="panel action-items" aria-labelledby="action-items-title">
      <header className="panel-header">
        <div><h2 id="action-items-title">Owner action queue</h2><span className="live-label public">Human-owned</span></div>
        <span className="muted">Reversible lifecycle</span>
      </header>
      <p className="action-items-intro">Approval created four durable work items. Driftline can track ownership without pretending to update a CRM or customer system.</p>
      {error && <p className="trace-error action-items-error" role="alert">{error}</p>}
      <div className="action-item-list">
        {items.map((item) => (
          <div className="action-item-row" key={item.item_id}>
            <span className="action-item-icon">{item.status === "completed" ? <Check size={15} /> : item.status === "claimed" ? <ClipboardCheck size={15} /> : item.status === "failed" ? <AlertTriangle size={15} /> : <CircleDashed size={15} />}</span>
            <span className="action-item-copy"><strong>{item.artifact}</strong><small><UserRound size={12} />{item.owner} · {item.idempotency_key}</small></span>
            <span className={`action-item-status ${item.status}`}>{label(item.status)}</span>
            {item.status === "queued" && <button className="secondary compact" type="button" onClick={() => transition(item, "claim")} disabled={busyId === item.item_id}>{busyId === item.item_id ? "Claiming…" : "Claim"}</button>}
            {item.status === "claimed" && <span className="action-item-actions"><button className="primary compact" type="button" onClick={() => transition(item, "complete")} disabled={busyId === item.item_id}>{busyId === item.item_id ? "Completing…" : "Complete"}</button><button className="secondary compact" type="button" onClick={() => transition(item, "fail")} disabled={busyId === item.item_id} aria-label={`Mark ${item.artifact} failed`}><AlertTriangle size={13} />Fail</button></span>}
            {item.status === "failed" && <button className="secondary compact" type="button" onClick={() => transition(item, "retry")} disabled={busyId === item.item_id}>{busyId === item.item_id ? "Retrying…" : <><RotateCcw size={13} />Retry</>}</button>}
          </div>
        ))}
      </div>
    </section>
  );
}
