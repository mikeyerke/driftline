import { ExternalLink, FileCheck2 } from "lucide-react";

const ACTIONS = [
  ["packet", "Create packet"],
  ["owner_review", "Owner review"],
  ["queued", "Queue for later"],
];

export default function ArtifactDetail({ item, live, decision, onDecisionChange, packetUrl, onPacket }) {
  if (!item) return null;
  return (
    <section className="panel artifact-detail" aria-labelledby="artifact-detail-title">
      <header className="panel-header">
        <div><FileCheck2 size={17} /><h2 id="artifact-detail-title">{item.name}</h2></div>
        <span className={`tag ${item.risk.toLowerCase()}`}>{item.risk}</span>
      </header>
      <div className="artifact-detail-body">
        <div className="artifact-meta"><span><strong>Owner</strong>{item.owner}</span><span><strong>Action</strong>{item.action}</span><span><strong>Scope</strong>{item.detail}</span></div>
        <div className="artifact-copy"><div><span className="diff-label removed-label">Current</span><p>{item.before || "Existing claim"}</p></div><div><span className="diff-label added-label">Proposed</span><p>{item.proposed || item.after || "Evidence-linked update"}</p></div></div>
        {live && item.status?.toLowerCase() === "draft ready" && <label className="decision-select">Action after approval<select id={`artifact-action-${item.name.replace(/[^a-z0-9]+/gi, "-").toLowerCase()}`} name="artifact-action" value={decision || "owner_review"} onChange={(event) => onDecisionChange(item.name, event.target.value)}>{ACTIONS.map(([value, label]) => <option value={value} key={value}>{label}</option>)}</select></label>}
        {item.evidence_hash && <code className="artifact-hash">Evidence: {item.evidence_hash}</code>}
        {packetUrl && (onPacket
          ? <button className="source-link packet-inline-button" type="button" onClick={onPacket}>Open the generated change packet <ExternalLink size={14} /></button>
          : <a className="source-link" href={packetUrl} target="_blank" rel="noreferrer">Open the generated change packet <ExternalLink size={14} /></a>)}
      </div>
    </section>
  );
}
