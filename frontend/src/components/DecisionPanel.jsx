import { AlertTriangle, Check, FileText, RotateCcw } from "lucide-react";

export default function DecisionPanel({ approved, approval, onApprove, onUndo, onEvidence }) {
  if (approved) {
    const approver = approval?.approver || "Demo operator";
    const initials = approver.split(/\s+/).map((part) => part[0]).join("").slice(0, 2).toUpperCase();
    const auditEvent = approval?.audit_event_id || "Not persisted in local fallback";
    return (
      <aside className="decision-panel resolved">
        <div className="decision-title"><span className="success-icon"><Check size={17} /></span><h2>Decision recorded</h2></div>
        <dl>
          <dt>Decision</dt><dd>Grandfather existing enterprise customers through their next renewal.</dd>
          <dt>Approver</dt><dd className="approver"><span className="avatar">{initials}</span><span><strong>{approver}</strong><small>Named human decision</small></span></dd>
          <dt>Decided</dt><dd>{approval?.timestamp ? new Date(approval.timestamp).toLocaleString() : "Synthetic local fallback"}</dd>
        </dl>
        <button className="secondary full" onClick={onUndo}><RotateCcw size={17} />Undo decision</button>
        <p className="decision-note">
          {approval?.timestamp
            ? "This decision is logged and controls downstream actions."
            : "Synthetic preview only; no server decision was recorded."}
        </p>
        <div className="audit-id"><strong>Audit event</strong><span>{auditEvent}</span></div>
        <button className="secondary full evidence-button" onClick={onEvidence}><FileText size={17} />Open evidence</button>
      </aside>
    );
  }

  return (
    <aside className="decision-panel pending">
      <AlertTriangle className="warning-icon" size={27} />
      <h2>Human decision needed</h2>
      <p className="decision-question">Should existing enterprise customers retain unlimited history through renewal?</p>
      <div className="decision-rationale"><strong>Why this needs a decision</strong><p>This change affects contractual expectations and may require an exception path for existing customers.</p></div>
      <button className="primary full" onClick={onApprove}><Check size={18} />Approve exception path</button>
      <button className="secondary full" onClick={onEvidence}><FileText size={17} />Open evidence</button>
      <p className="decision-note">Approval will unblock publishing of 2 high-risk artifacts.</p>
    </aside>
  );
}
