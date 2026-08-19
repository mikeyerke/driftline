import { Check, CircleDashed, ClipboardCheck, UserRound } from "lucide-react";
import { claimAction, completeAction } from "../api";

const label = (value) => (value || "queued").replace(/_/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());

export default function ActionItems({ workflowId, items, onChange }) {
  if (!items?.length) return null;

  const transition = async (item, operation) => {
    const next = operation === "claim" ? await claimAction(workflowId, item.item_id) : await completeAction(workflowId, item.item_id);
    onChange(next);
  };

  return (
    <section className="panel action-items" aria-labelledby="action-items-title">
      <header className="panel-header">
        <div><h2 id="action-items-title">Owner action queue</h2><span className="live-label public">Human-owned</span></div>
        <span className="muted">Reversible lifecycle</span>
      </header>
      <p className="action-items-intro">Approval created four durable work items. Driftline can track ownership without pretending to update a CRM or customer system.</p>
      <div className="action-item-list">
        {items.map((item) => (
          <div className="action-item-row" key={item.item_id}>
            <span className="action-item-icon">{item.status === "completed" ? <Check size={15} /> : item.status === "claimed" ? <ClipboardCheck size={15} /> : <CircleDashed size={15} />}</span>
            <span className="action-item-copy"><strong>{item.artifact}</strong><small><UserRound size={12} />{item.owner} · {item.idempotency_key}</small></span>
            <span className={`action-item-status ${item.status}`}>{label(item.status)}</span>
            {item.status === "queued" && <button className="secondary compact" type="button" onClick={() => transition(item, "claim")}>Claim</button>}
            {item.status === "claimed" && <button className="primary compact" type="button" onClick={() => transition(item, "complete")}>Complete</button>}
          </div>
        ))}
      </div>
    </section>
  );
}
