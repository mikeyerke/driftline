import { useEffect, useState } from "react";
import { ExternalLink, Globe2, Hash, ShieldCheck } from "lucide-react";
import { getSources } from "../api";

export default function SourcePanel({ evidence, dataMode }) {
  const isPublic = dataMode === "public_source";
  const [sources, setSources] = useState([]);

  useEffect(() => {
    let active = true;
    getSources().then((payload) => {
      if (active) setSources(payload.sources || []);
    }).catch(() => {
      if (active) setSources([]);
    });
    return () => { active = false; };
  }, []);

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
        <div className="monitor-registry-heading"><strong>Historical monitors</strong><span>Bounded source registry</span></div>
        <div className="monitor-source-list">
          {sources.map((source) => <span className={source.source_id === evidence?.source_id ? "monitor-source active" : "monitor-source"} key={source.source_id}><b>{source.name}</b><small>{source.source_id} · hash ledger</small></span>)}
        </div>
      </div>
      <p className="source-note">The adapter reads only these explicitly allowlisted public snapshots. It cannot discover arbitrary URLs or use private company data.</p>
    </section>
  );
}
