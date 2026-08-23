import { useEffect, useState } from "react";
import { AlertTriangle, Ban, Check, Download, FileText, RotateCcw } from "lucide-react";
import DecisionCopilot from "./DecisionCopilot";

export default function DecisionPanel({ approved, dismissed, approval, artifactDecisions, actionRecord, copilot, evidence, onApprove, onOptionSelect, onUndo, onDismiss, onEvidence, onPacket, isLive, busy, packetHref, sourceCategory, requiresDecisionCopilot = false }) {
  const decisions = approval?.artifact_decisions || artifactDecisions || { "Pricing battlecard": "packet", "Renewal playbook": "packet", "Enterprise FAQ": "owner_review", "CRM guidance": "queued" };
  const counts = Object.values(decisions).reduce((result, value) => ({ ...result, [value]: (result[value] || 0) + 1 }), {});
  const outcomeSummary = `${counts.packet || 0} packet${counts.packet === 1 ? "" : "s"} · ${counts.owner_review || 0} owner review${counts.owner_review === 1 ? "" : "s"} · ${counts.queued || 0} queued follow-up${counts.queued === 1 ? "" : "s"}`;
  const [selectedOptionId, setSelectedOptionId] = useState(copilot?.recommendation_id || "");
  const [overrideReason, setOverrideReason] = useState("Operator reviewed the evidence and chose a narrower artifact route.");
  useEffect(() => {
    setSelectedOptionId(copilot?.recommendation_id || "");
  }, [copilot?.recommendation_id]);
  const selectedOption = copilot?.options?.find((option) => option.option_id === selectedOptionId);
  // A human can intentionally override one or more artifact routes after
  // selecting a copilot option. Keep the reviewed option id and mark the
  // override explicitly so the API can revalidate and audit the custom plan.
  const selectedOptionMatchesArtifacts = selectedOption
    && Object.keys(selectedOption.artifact_decisions || {}).length === Object.keys(artifactDecisions || {}).length
    && Object.entries(selectedOption.artifact_decisions || {}).every(([name, value]) => artifactDecisions?.[name] === value);
  const customRouting = Boolean(selectedOption && !selectedOptionMatchesArtifacts);
  const approvalOption = selectedOption
    ? {
        ...selectedOption,
        copilot_artifact_override: customRouting,
        copilot_override_reason: customRouting ? overrideReason.trim() : null,
      }
    : selectedOption;
  const policyBlocked = copilot?.policy_review?.status === "blocked";
  const copilotUnavailable = isLive && requiresDecisionCopilot && !copilot;
  if (approved) {
    const approver = approval?.approver || "Demo operator";
    const initials = approver.split(/\s+/).map((part) => part[0]).join("").slice(0, 2).toUpperCase();
    const auditEvent = approval?.audit_event_id || "Not persisted in local fallback";
    const externalSystemsChanged = Boolean(actionRecord?.external_systems_changed || actionRecord?.external_write);
    const actionStatus = actionRecord?.status || "recorded";
    return (
      <aside className="decision-panel resolved">
        <div className="decision-title"><span className="success-icon"><Check size={17} /></span><h2>Action plan recorded</h2></div>
        <dl>
          <dt>Decision</dt><dd>{approval?.decision === "approve_competitive_response" ? "Approve the observed competitive response for owner handoff." : "Grandfather existing enterprise customers through their next renewal."}</dd>
          <dt>Approver</dt><dd className="approver"><span className="avatar">{initials}</span><span><strong>{approver}</strong><small>Named human decision</small></span></dd>
          <dt>Decided</dt><dd>{approval?.timestamp ? new Date(approval.timestamp).toLocaleString() : "Synthetic local fallback"}</dd>
        </dl>
        <button className="secondary full" onClick={onUndo} disabled={busy}><RotateCcw size={17} />Reopen decision</button>
        <p className="decision-note">
          {approval?.timestamp
            ? `One approved operational output is versioned inside the isolated Driftline project${["created", "reused", "reactivated"].includes(actionRecord?.jira_status) ? "; one bounded Jira issue was recorded" : ""}; no customer-facing system was changed.`
            : "No server decision was recorded."}
        </p>
        {actionRecord && <section className="action-receipt" aria-label="Proof of action">
          <header className="action-receipt-header">
            <div><strong>Proof of action</strong><small>Durable output · reversible lifecycle</small></div>
            <span className={`action-receipt-state ${actionStatus}`}>{actionStatus.replaceAll("_", " ")}</span>
          </header>
          <div className="action-receipt-grid">
            <div><strong>1</strong><span>Firestore action</span><code>{actionRecord.action_id}</code></div>
            <div><strong>2</strong><span>Cloud Storage</span><code>{actionRecord.storage_status || "not configured"}</code></div>
            <div><strong>3</strong><span>Rollback path</span><code>{actionRecord.reversible ? "available" : "not available"}</code></div>
          </div>
          <p className="action-receipt-footer"><span>External systems changed</span><b className={externalSystemsChanged ? "changed" : "unchanged"}>{externalSystemsChanged ? "Yes · scoped connector" : "No · packet-safe lane"}</b></p>
        </section>}
        <div className="audit-id"><strong>Audit event</strong><span>{auditEvent}</span></div>
        {actionRecord && <div className="audit-id"><strong>Firestore action record</strong><span>{actionRecord.action_id} · {actionRecord.status}</span></div>}
        {actionRecord?.storage_status && <div className="audit-id"><strong>Cloud Storage artifact</strong><span>{actionRecord.storage_status === "persisted" ? `${actionRecord.artifact_kind === "rollback" ? "Rollback marker" : "Versioned packet"} persisted` : actionRecord.storage_status}</span>{actionRecord.artifact_uri && <code className="artifact-uri">{actionRecord.artifact_uri}</code>}</div>}
        {actionRecord?.operational_status && <div className="audit-id"><strong>Operational output</strong><span>{actionRecord.operational_status === "active" ? "Approved output published to the isolated Driftline bucket" : actionRecord.operational_status === "reversed" ? "Operational output reversed with a durable marker" : `Output ${actionRecord.operational_status}`}</span>{actionRecord.operational_output_uri && <code className="artifact-uri">{actionRecord.operational_output_uri}</code>}</div>}
        {actionRecord?.jira_status && <div className="audit-id"><strong>Jira handoff</strong><span>{actionRecord.jira_status === "created" ? "Issue created in the configured least-privilege project" : actionRecord.jira_status === "reused" ? "Existing idempotent issue reused" : actionRecord.jira_status === "reactivated" ? "Previously reversed issue reactivated" : actionRecord.jira_status === "reversed" ? "Driftline marker reversed" : actionRecord.jira_status === "blocked_closed" ? "Blocked: matching issue is closed; no automatic reopen" : actionRecord.jira_status === "not_configured" ? "Connector disabled until Atlassian credentials are configured" : `Handoff ${actionRecord.jira_status}`}</span>{actionRecord.jira_issue_key && <code className="artifact-uri">{actionRecord.jira_issue_key}</code>}</div>}
        {packetHref && (onPacket
          ? <button className="secondary full packet-link" type="button" onClick={onPacket} disabled={busy}><Download size={17} />Download change packet</button>
          : <a className="secondary full packet-link" href={packetHref} target="_blank" rel="noreferrer"><Download size={17} />Download change packet</a>)}
        <button className="secondary full evidence-button" onClick={onEvidence}><FileText size={17} />Open evidence</button>
      </aside>
    );
  }

  if (dismissed) {
    return (
      <aside className="decision-panel dismissed">
        <div className="decision-title"><span className="dismissed-icon"><Ban size={17} /></span><h2>Signal dismissed</h2></div>
        <dl>
          <dt>Reason</dt><dd>{approval?.reason || "Reviewed as non-material"}</dd>
          <dt>Reviewed by</dt><dd>{approval?.approver || "Demo operator"}</dd>
          <dt>Recorded</dt><dd>{approval?.timestamp ? new Date(approval.timestamp).toLocaleString() : "Synthetic local fallback"}</dd>
        </dl>
        <p className="decision-note">No packet or external system write was created. The dismissal is retained so this signal is not silently lost.</p>
        <div className="audit-id"><strong>Audit state</strong><span>Intentional no-op · evidence remains available</span></div>
        <button className="secondary full" onClick={onEvidence}><FileText size={17} />Open evidence</button>
      </aside>
    );
  }

  return (
    <aside className="decision-panel pending">
      <AlertTriangle className="warning-icon" size={27} />
      <h2>Human approval required</h2>
      <p className="decision-question">{sourceCategory?.startsWith("Competitor") ? "Should Product Marketing approve this competitive response for owner handoff?" : "Should existing enterprise customers retain unlimited history through renewal?"}</p>
      <div className="decision-rationale"><strong>Why this needs a decision</strong><p>{sourceCategory?.startsWith("Competitor") ? "This signal can change comparison claims and deal guidance; Driftline keeps the observed source attached before anyone acts." : "This change affects contractual expectations and may require an exception path for existing customers."}</p></div>
      <DecisionCopilot copilot={copilot} evidence={evidence} selectedId={selectedOptionId} onSelect={(option) => { setSelectedOptionId(option.option_id); onOptionSelect?.(option); }} />
      {customRouting && <label className="override-reason"><span>Why change the recommended artifact routing?</span><textarea value={overrideReason} onChange={(event) => setOverrideReason(event.target.value)} maxLength={240} rows={2} /></label>}
      <div className="decision-action-dock">
        <div className="approval-scope"><strong>Human decision · reversible</strong><span>{outcomeSummary}</span><small>{customRouting ? "Custom routing selected · policy boundaries still apply." : "Creates owner-ready work only after your approval."}</small></div>
        <button className="primary full" onClick={() => onApprove(approvalOption)} disabled={!isLive || busy || policyBlocked || copilotUnavailable || (copilot && !selectedOption) || (customRouting && overrideReason.trim().length < 3)}><Check size={18} />{busy ? "Recording decision…" : policyBlocked ? "Resolve policy findings" : copilotUnavailable ? "Rerun scan for Gemini review" : "Approve action plan"}</button>
        <div className="decision-secondary-actions">
          <button className="secondary" onClick={onEvidence}><FileText size={17} />Open evidence</button>
          <button className="text-button" onClick={() => {
            const reason = window.prompt("Why is this signal not material right now?", "Reviewed as non-material for the current segment");
            if (reason?.trim()) onDismiss?.(reason.trim());
          }} disabled={!isLive || busy}><Ban size={17} />Dismiss signal</button>
        </div>
        <p className="decision-note">The agent cannot approve itself. Any created output stays evidence-linked and reversible.</p>
      </div>
      {copilotUnavailable && <p className="decision-note decision-warning">Gemini decision analysis was unavailable for this tenant run. Approval is disabled until a new scan produces a reviewed option.</p>}
      {!isLive && <p className="decision-note decision-warning">Run the live agent to create a Firestore workflow before deciding.</p>}
    </aside>
  );
}
