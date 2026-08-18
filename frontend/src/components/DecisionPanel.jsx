import { AlertTriangle, Check, Download, FileText, RotateCcw } from "lucide-react";

export default function DecisionPanel({ approved, approval, actionRecord, onApprove, onUndo, onEvidence, isLive, busy, packetHref }) {
  if (approved) {
    const approver = approval?.approver || "Demo operator";
    const initials = approver.split(/\s+/).map((part) => part[0]).join("").slice(0, 2).toUpperCase();
    const auditEvent = approval?.audit_event_id || "Not persisted in local fallback";
    return (
      <aside className="decision-panel resolved">
        <div className="decision-title"><span className="success-icon"><Check size={17} /></span><h2>Action plan recorded</h2></div>
        <dl>
          <dt>Decision</dt><dd>Grandfather existing enterprise customers through their next renewal.</dd>
          <dt>Approver</dt><dd className="approver"><span className="avatar">{initials}</span><span><strong>{approver}</strong><small>Named human decision</small></span></dd>
          <dt>Decided</dt><dd>{approval?.timestamp ? new Date(approval.timestamp).toLocaleString() : "Synthetic local fallback"}</dd>
        </dl>
        <button className="secondary full" onClick={onUndo} disabled={busy}><RotateCcw size={17} />Reopen decision</button>
        <p className="decision-note">
          {approval?.timestamp
            ? "The sandbox packet is recorded; no external system was changed."
            : "No server decision was recorded."}
        </p>
        <div className="audit-id"><strong>Audit event</strong><span>{auditEvent}</span></div>
        {actionRecord && <div className="audit-id"><strong>Firestore action record</strong><span>{actionRecord.action_id} · {actionRecord.status}</span></div>}
        {packetHref && <a className="secondary full packet-link" href={packetHref} target="_blank" rel="noreferrer"><Download size={17} />Download change packet</a>}
        <button className="secondary full evidence-button" onClick={onEvidence}><FileText size={17} />Open evidence</button>
      </aside>
    );
  }

  return (
    <aside className="decision-panel pending">
      <AlertTriangle className="warning-icon" size={27} />
      <h2>Human approval required</h2>
      <p className="decision-question">Should existing enterprise customers retain unlimited history through renewal?</p>
      <div className="decision-rationale"><strong>Why this needs a decision</strong><p>This change affects contractual expectations and may require an exception path for existing customers.</p></div>
      <button className="primary full" onClick={onApprove} disabled={!isLive || busy}><Check size={18} />{busy ? "Recording decision…" : "Approve action plan"}</button>
      <button className="secondary full" onClick={onEvidence}><FileText size={17} />Open evidence</button>
      <p className="decision-note">Approval creates a reversible, evidence-linked sandbox packet. The agent cannot approve itself.</p>
      {!isLive && <p className="decision-note decision-warning">Run the scan to create a live Firestore workflow before deciding.</p>}
    </aside>
  );
}
