import { useEffect, useState } from "react";
import { ExternalLink, Globe2, Hash, History, ShieldCheck } from "lucide-react";
import { getSourceHistory } from "../api";
import MultimodalEvidencePanel from "./MultimodalEvidencePanel";

export default function SourcePanel({ evidence, dataMode, sources = [], selectedSource, onSourceChange }) {
  const isPublic = dataMode === "public_source";
  const [history, setHistory] = useState([]);

  useEffect(() => {
    let active = true;
    getSourceHistory(selectedSource || evidence?.source_id || "public/pricing")
      .then((payload) => active && setHistory(payload.observations || []))
      .catch(() => active && setHistory([]));
    return () => { active = false; };
  }, [selectedSource, evidence?.source_id, evidence?.retrieved_at]);

  return (
    <section className="panel source-panel" id="sources-section">
      <header className="panel-header">
        <div><h2>Allowlisted source</h2><span className={`live-label ${isPublic ? "public" : "synthetic"}`}>{isPublic ? "Public snapshot" : "Synthetic replay"}</span></div>
        <span className="muted">Source-level access only</span>
      </header>
      <div className="source-grid">
        <div className="source-identity"><span className="source-icon"><Globe2 size={20} /></span><div><strong>{evidence?.source_name || "Public pricing snapshot"}</strong><small>{evidence?.source_id || "public/pricing"}</small></div></div>
        <div><span className="source-label"><ShieldCheck size={14} />Evidence status</span><strong>Hash-bound and verified</strong></div>
        <div><span className="source-label"><Hash size={14} />Snapshot hash</span><code>{evidence?.snapshot_hash || evidence?.evidence_hash || "Not captured yet"}</code></div>
        <div><span className="source-label">Retrieved</span><strong>{evidence?.retrieved_at ? new Date(evidence.retrieved_at).toLocaleString() : "Run the scan to capture"}</strong></div>
      </div>
      {evidence?.source_url && <a className="source-link" href={evidence.source_url} target="_blank" rel="noreferrer">Open the allowlisted source snapshot <ExternalLink size={14} /></a>}
      <div className="monitor-registry" aria-label="Historical monitor sources">
        <div className="monitor-registry-heading"><strong>Monitor any approved change surface</strong><span>Bounded source registry</span></div>
        <label className="source-selector">Scenario for next scan<select value={selectedSource || evidence?.source_id || "public/pricing"} onChange={(event) => onSourceChange?.(event.target.value)}><optgroup label="Own surfaces">{sources.filter((source) => source.category?.startsWith("Own")).map((source) => <option value={source.source_id} key={source.source_id}>{source.name}</option>)}</optgroup><optgroup label="Competitor surfaces">{sources.filter((source) => source.category?.startsWith("Competitor")).map((source) => <option value={source.source_id} key={source.source_id}>{source.name}</option>)}</optgroup></select></label>
        <div className="monitor-source-list">
          {sources.map((source) => <span className={source.source_id === (selectedSource || evidence?.source_id) ? "monitor-source active" : "monitor-source"} key={source.source_id}><b>{source.name}</b><small>{source.category} · {source.change_type}</small></span>)}
        </div>
        <div className="source-history" aria-label="Append-only source history">
          <div className="source-history-heading"><span><History size={14} />Historical observations</span><small>Append-only ledger</small></div>
          {history.length === 0
            ? <p className="empty-state">No scheduled observations yet for this source. A demo replay does not rewrite the monitor ledger.</p>
            : <ol>{history.map((observation) => <li key={`${observation.retrieved_at}-${observation.snapshot_hash}`}><span><b>{new Date(observation.retrieved_at).toLocaleString()}</b><small>{observation.snapshot_hash.slice(0, 12)}… · {observation.data_mode.replaceAll("_", " ")}</small></span><code>{observation.body}</code></li>)}</ol>}
        </div>
      </div>
      <MultimodalEvidencePanel assetId="promise-card" mode="live" />
      <p className="source-note">The adapter reads only these explicitly allowlisted public snapshots. It cannot discover arbitrary URLs or use private company data. Competitor claims are observed signals, not verified product truth.</p>
    </section>
  );
}
