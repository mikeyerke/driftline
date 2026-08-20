import { Activity, AlertTriangle, CheckCircle2, Clock3, Gauge, Layers3, ShieldCheck } from "lucide-react";
import { useEffect, useState } from "react";
import { getValueProof } from "../api";

const metric = (value, suffix = "") => (value === null || value === undefined ? "—" : `${value}${suffix}`);

const outcomeLabel = (value) => value
  .replaceAll("_", " ")
  .replace(/\b\w/g, (letter) => letter.toUpperCase());

const modeLabel = (value) => {
  if (value === "synthetic_demo") return "Synthetic replay";
  if (value === "public_source") return "Public source";
  if (value === "live") return "Live tenant run";
  return outcomeLabel(value);
};

export default function ValueProofPanel() {
  const [proof, setProof] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    getValueProof()
      .then((payload) => active && setProof(payload))
      .catch(() => active && setProof(null))
      .finally(() => active && setLoading(false));
    return () => { active = false; };
  }, []);

  const observed = proof?.observed || {};
  const latency = observed.approval_latency_seconds || {};
  const notMeasured = proof?.not_measured || [];
  const workflowModes = Object.entries(observed.workflow_data_modes || {});

  return (
    <section className="panel value-proof-panel" aria-labelledby="value-proof-title">
      <header className="panel-header">
        <div><h2 id="value-proof-title"><Gauge size={17} />Value proof</h2><span className="live-label">Public sandbox records</span></div>
        <span className="muted">Operational utility, not invented ROI</span>
      </header>
      {loading && <p className="multimodal-empty"><Activity size={15} className="spin" />Reading bounded deployment evidence…</p>}
      {!loading && proof && <>
        <div className="value-proof-grid">
          <div><Activity size={16} /><strong>{metric(observed.workflows)}</strong><small>workflows recorded</small></div>
          <div><CheckCircle2 size={16} /><strong>{metric(observed.cards_with_named_owners)}</strong><small>cards with named owners</small></div>
          <div><ShieldCheck size={16} /><strong>{metric(observed.workflows_reversed_or_reopened)}</strong><small>reopened or reversed</small></div>
          <div><Clock3 size={16} /><strong>{metric(latency.p50, "s")}</strong><small>approval latency p50</small></div>
        </div>
        <div className="value-proof-details">
          <div>
            <h3><CheckCircle2 size={14} />Measured in this deployment</h3>
            <dl>
              <div><dt>Source observations</dt><dd>{metric(observed.source_observations)}</dd></div>
              <div><dt>Healthy sources</dt><dd>{metric(observed.healthy_sources)}</dd></div>
              <div><dt>Owner action completion</dt><dd>{observed.action_item_completion_rate === null || observed.action_item_completion_rate === undefined ? "—" : `${Math.round(observed.action_item_completion_rate * 100)}%`}</dd></div>
              <div><dt>External writes</dt><dd>{metric(observed.external_write_actions)}</dd></div>
            </dl>
          </div>
          <div className="value-proof-unmeasured">
            <h3><AlertTriangle size={14} />Customer outcomes still unmeasured</h3>
            <p>These require a real pilot and are intentionally not inferred from synthetic activity:</p>
            <ul>{notMeasured.map((item) => <li key={item}>{outcomeLabel(item)}</li>)}</ul>
          </div>
        </div>
        <div className="value-proof-mix">
          <h3><Layers3 size={14} />Evidence mix</h3>
          <div className="value-proof-mix-grid">
            {workflowModes.length > 0 ? workflowModes.map(([mode, count]) => (
              <div key={mode}><strong>{count}</strong><span>{modeLabel(mode)}</span></div>
            )) : <p>No workflow records in this scope.</p>}
          </div>
          <p>{metric(observed.tenant_scoped_workflows, " tenant-scoped")} · {metric(observed.tenantless_workflows, " tenantless")} workflow records visible in this scope.</p>
        </div>
        <p className="value-proof-note">{proof.interpretation || "Counts are direct records from the isolated Driftline deployment."} This public panel is anonymous and intentionally excludes tenant-scoped customer records; signed tenant operators use the tenant-filtered API lane.</p>
      </>}
      {!loading && !proof && <p className="empty-state">Value proof is unavailable; source evidence and workflow audit remain available.</p>}
    </section>
  );
}
