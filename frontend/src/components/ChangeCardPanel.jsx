import { AlertTriangle, ArrowUpRight, CheckCircle2, Clock3, ShieldCheck, UsersRound } from "lucide-react";

const label = (value) => (value || "pending").replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
const contextMetric = (name, payload) => {
  const metric = [
    ["open_issue_count", "open issues"],
    ["open_pull_request_count", "open PRs"],
    ["recent_message_count", "recent messages"],
    ["page_count", "pages"],
  ].find(([key]) => Number.isFinite(Number(payload?.[key])));
  return metric ? `${label(name)} ${payload[metric[0]]} ${metric[1]}` : null;
};

export default function ChangeCardPanel({ card }) {
  if (!card) return null;
  const materiality = card.materiality || {};
  const exposure = card.exposure || {};
  const sourceQuality = card.source_quality || {};
  const evidenceStrength = sourceQuality.evidence_strength || {};
  const closure = card.closure || {};
  const internalContext = card.internal_context || {};
  const verifiedConnectorCount = Number(internalContext.verified_connector_count || 0);
  const contextHighlights = Object.entries(internalContext.connectors || {})
    .filter(([, payload]) => payload?.external_read)
    .map(([name, payload]) => contextMetric(name, payload))
    .filter(Boolean)
    .slice(0, 3);
  const approvalPending = closure.state === "approval_pending";
  const exposureTitle = exposure.mode === "connected_internal_data"
    ? "Permissioned business context"
    : exposure.mode === "synthetic_demo"
      ? "Illustrative scenario"
      : "CRM context unavailable";
  return (
    <section className="change-card panel" aria-labelledby="change-card-title">
      <header className="panel-header change-card-header">
        <div>
          <h2 id="change-card-title">Change-to-work card</h2>
          <span className="live-label public"><ShieldCheck size={12} />Evidence-bound decision</span>
          {card.change_card_id && <code className="change-card-id" title="Stable identity for this source snapshot">{card.change_card_id}</code>}
        </div>
        <span className={`materiality-pill ${materiality.severity || "medium"}`}><AlertTriangle size={13} />{label(materiality.severity)} materiality · {materiality.score || "—"}/100</span>
      </header>
      <div className="change-card-grid">
        <div className="change-card-block materiality-block">
          <span className="change-card-kicker">Why now</span>
          <strong>{materiality.reason || "Owner review is required before this signal becomes work."}</strong>
          <p>{materiality.decision_window || "Before the next owner review"}</p>
          <div className="trigger-list">{(materiality.triggers || []).map((trigger) => <span key={trigger}>{label(trigger)}</span>)}</div>
          <div className="source-quality"><span>Evidence confidence</span><b>{Math.round((sourceQuality.confidence || 0) * 100)}%</b><small>{label(sourceQuality.evidence_type || "unknown")}</small></div>
          <div className="evidence-strength" aria-label="Deterministic evidence strength review">
            <span>Evidence strength · heuristic</span><b>{evidenceStrength.score ?? "—"}/{evidenceStrength.max_score || 100}</b>
            <small>{evidenceStrength.label || "Review evidence dimensions"}</small>
            <small>{evidenceStrength.next_review || "Corroboration review has not run."}</small>
          </div>
        </div>
        <div className="change-card-block exposure-block">
          <span className="change-card-kicker"><UsersRound size={13} />Internal exposure</span>
          <strong>{exposureTitle}</strong>
          <p>{exposure.label || "Internal exposure is not available."}</p>
          <div className="exposure-stats">
            <span><b>{exposure.opportunity_count ?? "—"}</b> open opportunities</span>
            <span><b>{exposure.renewal_count ?? "—"}</b> renewals</span>
            <span><b>{exposure.affected_asset_count ?? 0}</b> assets</span>
          </div>
          {verifiedConnectorCount > 0 && <small className="exposure-context-note" aria-label="Verified aggregate connector context">
            {verifiedConnectorCount} connector{verifiedConnectorCount === 1 ? "" : "s"} verified · aggregate context only
          </small>}
          {contextHighlights.length > 0 && <small className="exposure-context-detail">
            {contextHighlights.join(" · ")}
          </small>}
        </div>
        <div className="change-card-block closure-block">
          <span className="change-card-kicker"><Clock3 size={13} />Closure</span>
          <strong>{label(closure.state)}</strong>
          <p>{closure.next_step || "Review the next step."}</p>
          {approvalPending
            ? <small>Actions are queued after the human decision</small>
            : <><div className="closure-progress"><span style={{ width: `${Math.round((closure.completion_rate || 0) * 100)}%` }} /></div><small>{closure.completed || 0}/{closure.item_count || 0} owner actions complete{closure.overdue ? ` · ${closure.overdue} overdue` : ""}</small></>}
        </div>
      </div>
      <div className="role-packet-strip">
        <div className="role-packet-title"><CheckCircle2 size={14} />One evidence set, role-specific work</div>
        <div className="role-packets">{(card.role_packets || []).map((packet) => <div className="role-packet" key={`${packet.role}-${packet.artifact}`}><strong>{packet.role}</strong><span>{packet.artifact}</span><small>{packet.next_action}</small><ArrowUpRight size={13} /></div>)}</div>
      </div>
      <footer className="change-card-disclosure">{(card.disclosures || []).map((note) => <span key={note}>{note}</span>)}{sourceQuality.disclosure && <span>{sourceQuality.disclosure}</span>}</footer>
    </section>
  );
}
