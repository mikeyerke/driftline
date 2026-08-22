import { useEffect, useState } from "react";
import { Dna, History, LoaderCircle, RotateCcw, ShieldAlert } from "lucide-react";
import { getMemorySummary } from "../api";
import useNearViewport from "../hooks/useNearViewport";

export default function ChangeGenomePanel() {
  const [panelRef, nearViewport] = useNearViewport();
  const [memory, setMemory] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!nearViewport) return undefined;
    let active = true;
    setLoading(true);
    getMemorySummary()
      .then((payload) => active && setMemory(payload))
      .catch(() => active && setMemory(null))
      .finally(() => active && setLoading(false));
    return () => { active = false; };
  }, [nearViewport]);

  return (
    <section ref={panelRef} className="panel genome-panel" aria-labelledby="genome-title">
      <header className="panel-header">
        <div><h2 id="genome-title"><Dna size={17} />Change memory</h2><span className="live-label">Append-only</span></div>
        <span className="muted">{memory?.history_window?.scope === "public_recent_evaluation_window" ? `Recent ${memory.history_window.limit}-record window` : "Recurring moves and open work"}</span>
      </header>
      {!nearViewport && <p className="multimodal-empty">Change memory loads when this panel enters view.</p>}
      {nearViewport && loading && <p className="multimodal-empty"><LoaderCircle size={15} className="spin" />Reading the source ledger…</p>}
      {!loading && memory && <>
        <div className="genome-summary">
          <span><strong>{memory.work_summary?.workflow_count || 0}</strong>workflows</span>
          <span><strong>{memory.change_genomes?.length || 0}</strong>change genomes</span>
          <span><strong>{memory.work_summary?.unresolved_count || 0}</strong>open owner items</span>
          <span><strong>{memory.work_summary?.reversed_count || 0}</strong>reversed owner items</span>
        </div>
        <div className="genome-grid">
          <div><h3><History size={14} />Recent recurring moves</h3>{(memory.recurring_changes || []).length === 0
            ? <p className="empty-state">No repeated transition yet. Each verified change becomes a stable genome.</p>
            : <ul>{memory.recurring_changes.slice(0, 4).map((item) => <li key={item.genome}><code>{item.genome.slice(0, 12)}…</code><span>{item.occurrences} observations · {item.sources.join(", ")}</span></li>)}</ul>}</div>
          <div><h3><ShieldAlert size={14} />Unresolved downstream work</h3>{(memory.work_summary?.unresolved || []).length === 0
            ? <p className="empty-state">No queued or failed owner work.</p>
            : <ul>{memory.work_summary.unresolved.slice(0, 4).map((item) => <li key={`${item.workflow_id}-${item.item_id}`}><strong>{item.artifact}</strong><span>{item.owner} · {item.status}</span></li>)}</ul>}</div>
        </div>
        <p className="genome-note"><RotateCcw size={13} />The genome is derived from immutable source snapshots and workflow records; it never rewrites evidence.</p>
      </>}
      {nearViewport && !loading && !memory && <p className="empty-state">Change memory is unavailable right now; source evidence remains available.</p>}
    </section>
  );
}
