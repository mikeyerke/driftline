import { ClipboardCheck, Clock3, Download, Gauge, Plus, ShieldCheck } from "lucide-react";
import { useEffect, useState } from "react";
import { downloadPilotPacket, getMonitorRegistry, getPilotReport, getValueProof, recordOutcomeMeasurement } from "../api";
import useNearViewport from "../hooks/useNearViewport";

const initialForm = {
  source_type: "pilot_log",
  cohort_label: "",
  changes_observed: "",
  baseline_minutes: "",
  driftline_minutes: "",
  baseline_owner_ready_within_24h: "",
  driftline_owner_ready_within_24h: "",
  baseline_actions_completed_within_7d: "",
  driftline_actions_completed_within_7d: "",
  baseline_reversed_or_reopened: "",
  driftline_reversed_or_reopened: "",
  evidence_ref: "",
  revenue_lift_usd: "",
  retention_lift_pct: "",
  willingness_to_pay_usd: "",
};

const numberOrNull = (value) => value === "" ? null : Number(value);

export default function PilotMeasurementPanel({ operatorSession }) {
  const [panelRef, nearViewport] = useNearViewport();
  const [form, setForm] = useState(initialForm);
  const [report, setReport] = useState(null);
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [utility, setUtility] = useState({ registry: null, proof: null });

  const refresh = () => {
    if (!operatorSession?.identityToken || !operatorSession?.tenantId) return;
    Promise.allSettled([getPilotReport(), getMonitorRegistry(), getValueProof()]).then(([pilot, registry, proof]) => {
      setReport(pilot.status === "fulfilled" ? pilot.value : null);
      setUtility({
        registry: registry.status === "fulfilled" ? registry.value : null,
        proof: proof.status === "fulfilled" ? proof.value : null,
      });
    });
  };

  useEffect(() => {
    if (!nearViewport) return;
    refresh();
  }, [operatorSession?.identityToken, operatorSession?.tenantId, nearViewport]);

  if (!operatorSession?.identityToken) return null;

  const update = (event) => setForm((current) => ({ ...current, [event.target.name]: event.target.value }));
  const submit = async (event) => {
    event.preventDefault();
    setBusy(true);
    setMessage("");
    setError("");
    try {
      await recordOutcomeMeasurement({
        ...form,
        changes_observed: Number(form.changes_observed),
        baseline_minutes: Number(form.baseline_minutes),
        driftline_minutes: Number(form.driftline_minutes),
        baseline_owner_ready_within_24h: numberOrNull(form.baseline_owner_ready_within_24h),
        driftline_owner_ready_within_24h: numberOrNull(form.driftline_owner_ready_within_24h),
        baseline_actions_completed_within_7d: numberOrNull(form.baseline_actions_completed_within_7d),
        driftline_actions_completed_within_7d: numberOrNull(form.driftline_actions_completed_within_7d),
        baseline_reversed_or_reopened: numberOrNull(form.baseline_reversed_or_reopened),
        driftline_reversed_or_reopened: numberOrNull(form.driftline_reversed_or_reopened),
        revenue_lift_usd: numberOrNull(form.revenue_lift_usd),
        retention_lift_pct: numberOrNull(form.retention_lift_pct),
        willingness_to_pay_usd: numberOrNull(form.willingness_to_pay_usd),
      });
      setMessage("Pilot measurement recorded · operator-reported and unverified");
      refresh();
    } catch (requestError) {
      setError(requestError.message || "Pilot measurement could not be recorded");
    } finally {
      setBusy(false);
    }
  };

  const downloadPacket = async () => {
    setDownloading(true);
    setMessage("");
    setError("");
    try {
      await downloadPilotPacket(report?.cohort_label || "");
      setMessage("Pilot packet downloaded · aggregate-only and operator-reported");
    } catch (requestError) {
      setError(requestError.message || "Pilot packet could not be downloaded");
    } finally {
      setDownloading(false);
    }
  };

  const measured = report?.record_count > 0;
  const customSourceCount = (utility.registry?.sources || []).filter((source) => source.source_kind === "operator_registered_public").length;
  const observed = utility.proof?.observed || {};
  const approvalLatency = observed.approval_latency_seconds || {};
  const ownerActionCycle = observed.owner_action_cycle_seconds || {};
  const workflowCount = observed.workflows || 0;
  const completedActions = observed.action_items_completed_historically || 0;
  const formatSeconds = (value) => value === null || value === undefined || Number.isNaN(Number(value)) ? "—" : `${Number(value).toFixed(1)}s`;
  const formatPercent = (value) => value === null || value === undefined || Number.isNaN(Number(value)) ? "—" : `${Math.round(Number(value) * 100)}%`;
  const timeDirection = report?.time_delta_direction;
  const timeDeltaLabel = !measured ? "time delta recorded" : timeDirection === "added" ? "time added" : timeDirection === "neutral" ? "no time delta" : "time saved";
  const timeDeltaValue = measured && report?.time_saved_minutes_total !== null && report?.time_saved_minutes_total !== undefined
    ? `${Math.abs(Number(report.time_saved_minutes_total))}m`
    : "—";
  const readiness = [
    { label: "Tenant lane connected", ready: Boolean(operatorSession.tenantId), detail: operatorSession.tenantId || "Sign in and select a tenant" },
    { label: "Real source registered", ready: customSourceCount > 0, detail: customSourceCount > 0 ? `${customSourceCount} exact HTTPS source${customSourceCount === 1 ? "" : "s"}` : "Add one owned or competitor change surface" },
    { label: "Workflow work observed", ready: workflowCount > 0, detail: workflowCount > 0 ? `${workflowCount} tenant-scoped workflow${workflowCount === 1 ? "" : "s"}` : "Run a tenant workflow against the registered source" },
    { label: "Aggregate outcome recorded", ready: measured, detail: measured ? `${report.record_count} operator-reported record${report.record_count === 1 ? "" : "s"}` : "Record before/after minutes after a real pilot run" },
  ];
  return (
    <section ref={panelRef} className="panel pilot-panel" aria-labelledby="pilot-title">
      <header className="panel-header">
        <div><h2 id="pilot-title"><Gauge size={17} />Pilot measurement</h2><span className="live-label public">Tenant-scoped</span></div>
        <span className="muted">Aggregate evidence only</span>
      </header>
      <div className="pilot-summary">
        <div><Clock3 size={15} /><strong>{timeDeltaValue}</strong><small>{timeDeltaLabel}</small></div>
        <div><ClipboardCheck size={15} /><strong>{report?.changes_observed || 0}</strong><small>changes measured</small></div>
        <div><ShieldCheck size={15} /><strong>{measured ? `${report.time_delta_pct ?? report.time_saved_pct}%` : "—"}</strong><small>before/after delta</small></div>
      </div>
      <p className="pilot-note">Record aggregate before/after observations from a real pilot. No example measurements are prefilled: enter only values reconciled to the dated evidence reference. Driftline stores no customer names, raw notes, or CRM records; every entry remains explicitly operator-reported until independently reviewed.</p>
      <div className="pilot-readiness" aria-label="Pilot readiness checklist">
        <div className="pilot-readiness-heading"><strong>Utility loop readiness</strong><small>Product telemetry, not customer proof</small></div>
        <div className="pilot-readiness-list">
          {readiness.map((item) => <div className={`pilot-readiness-item${item.ready ? " ready" : ""}`} key={item.label}>
            <span aria-hidden="true">{item.ready ? "✓" : "○"}</span><div><strong>{item.label}</strong><small>{item.detail}</small></div>
          </div>)}
        </div>
        <p className="pilot-readiness-footnote">{completedActions > 0 ? `${completedActions} owner action${completedActions === 1 ? " has" : "s have"} closed in the append-only audit.` : "No owner action has been closed in this tenant audit yet."} Customer time saved, revenue, retention, and willingness-to-pay stay unmeasured until a real pilot produces source-backed records.</p>
      </div>
      <div className="pilot-observed" aria-label="Observed Driftline telemetry">
        <div className="pilot-observed-heading"><strong>Observed Driftline operations</strong><small>Not customer proof</small></div>
        <div className="pilot-observed-grid">
          <div><strong>{workflowCount}</strong><small>workflows</small></div>
          <div><strong>{observed.source_observations || 0}</strong><small>source observations</small></div>
          <div><strong>{observed.source_observations_unchanged || 0}</strong><small>no-op observations</small></div>
          <div><strong>{observed.source_observations_changed || 0}</strong><small>material ledger changes</small></div>
          <div><strong>{formatPercent(observed.source_no_op_comparison_rate)}</strong><small>no-op comparison rate</small></div>
          <div><strong>{completedActions}</strong><small>historical closures</small></div>
          <div><strong>{formatSeconds(ownerActionCycle.p50)}</strong><small>owner cycle p50</small></div>
          <div><strong>{formatSeconds(approvalLatency.p90)}</strong><small>approval p90</small></div>
        </div>
        <p>Bounded telemetry from this tenant’s Driftline workflows only. Demo replays are repeatable and do not mutate the source ledger; these counts are recorded monitor comparisons, not customer proof.</p>
      </div>
      {measured && report?.operational_metrics && <div className="pilot-outcome-metrics" aria-label="Aggregate pilot operational outcomes">
        <div className="pilot-observed-heading"><strong>Operational pilot outcomes</strong><small>Aggregate, operator-reported · not independently verified</small></div>
        <div className="pilot-outcome-table" role="table">
          {[['owner_ready_within_24h', 'Owner-ready within 24h'], ['actions_completed_within_7d', 'Actions completed within 7d'], ['reversed_or_reopened', 'Reversed or reopened']].map(([key, label]) => {
            const metric = report.operational_metrics[key] || {};
            const formatRate = (value) => value === null || value === undefined ? '—' : `${value}%`;
            return <div className="pilot-outcome-row" role="row" key={key}><strong role="cell">{label}</strong><span role="cell">Baseline {formatRate(metric.baseline_rate_pct)}</span><span role="cell">Driftline {formatRate(metric.driftline_rate_pct)}</span><b role="cell">Δ {metric.delta_percentage_points === null || metric.delta_percentage_points === undefined ? '—' : `${metric.delta_percentage_points} pp`}</b></div>;
          })}
        </div>
        <p className="pilot-readiness-footnote">Rates use the recorded change count as denominator. Blank rates mean that measure was not supplied; Driftline does not infer a customer outcome from workflow telemetry.</p>
      </div>}
      <div className="pilot-actions">
        <button className="secondary compact pilot-toggle" type="button" onClick={() => { setOpen((current) => !current); setMessage(""); setError(""); }}><Plus size={14} />{open ? "Close measurement form" : "Record a measurement"}</button>
        <button className="secondary compact pilot-toggle" type="button" onClick={downloadPacket} disabled={downloading}><Download size={14} />{downloading ? "Preparing…" : "Download pilot packet"}</button>
      </div>
      {open && <form className="pilot-form" onSubmit={submit}>
        <label>Evidence type<select name="source_type" value={form.source_type} onChange={update}><option value="pilot_log">Pilot log</option><option value="customer_interview">Customer interview</option><option value="win_loss">Win / loss</option><option value="billing_record">Billing record</option></select></label>
        <label>Cohort label<input required name="cohort_label" value={form.cohort_label} onChange={update} maxLength={80} placeholder="Named pilot cohort" /></label>
        <label>Changes observed<input required type="number" min="1" name="changes_observed" value={form.changes_observed} onChange={update} placeholder="Measured count" /></label>
        <label>Baseline minutes (total)<input required type="number" min="0.1" step="0.1" name="baseline_minutes" value={form.baseline_minutes} onChange={update} placeholder="Observed baseline" /></label>
        <label>Driftline minutes<input required type="number" min="0" step="0.1" name="driftline_minutes" value={form.driftline_minutes} onChange={update} placeholder="Observed Driftline time" /></label>
        <fieldset className="pilot-form-group"><legend>Optional operational counts</legend><small>Use counts from the same change set; each must be ≤ changes observed.</small><label>Baseline owner-ready ≤24h<input type="number" min="0" step="1" name="baseline_owner_ready_within_24h" value={form.baseline_owner_ready_within_24h} onChange={update} placeholder="Not measured" /></label><label>Driftline owner-ready ≤24h<input type="number" min="0" step="1" name="driftline_owner_ready_within_24h" value={form.driftline_owner_ready_within_24h} onChange={update} placeholder="Not measured" /></label><label>Baseline actions closed ≤7d<input type="number" min="0" step="1" name="baseline_actions_completed_within_7d" value={form.baseline_actions_completed_within_7d} onChange={update} placeholder="Not measured" /></label><label>Driftline actions closed ≤7d<input type="number" min="0" step="1" name="driftline_actions_completed_within_7d" value={form.driftline_actions_completed_within_7d} onChange={update} placeholder="Not measured" /></label><label>Baseline reversed / reopened<input type="number" min="0" step="1" name="baseline_reversed_or_reopened" value={form.baseline_reversed_or_reopened} onChange={update} placeholder="Not measured" /></label><label>Driftline reversed / reopened<input type="number" min="0" step="1" name="driftline_reversed_or_reopened" value={form.driftline_reversed_or_reopened} onChange={update} placeholder="Not measured" /></label></fieldset>
        <label>Evidence reference<input required name="evidence_ref" value={form.evidence_ref} onChange={update} placeholder="artifact://… or https://…" maxLength={300} /></label>
        <label>Revenue lift USD<input type="number" min="-1000000000" step="0.01" name="revenue_lift_usd" value={form.revenue_lift_usd} onChange={update} placeholder="Optional" /></label>
        <label>Retention lift %<input type="number" min="-100" max="100" step="0.01" name="retention_lift_pct" value={form.retention_lift_pct} onChange={update} placeholder="Optional" /></label>
        <label>Willingness to pay USD<input type="number" min="0" step="0.01" name="willingness_to_pay_usd" value={form.willingness_to_pay_usd} onChange={update} placeholder="Optional" /></label>
        <button className="primary pilot-submit" type="submit" disabled={busy}>{busy ? "Recording…" : "Record pilot evidence"}</button>
        {message && <p className="source-onboarding-success" role="status">{message}</p>}
        {error && <p className="source-onboarding-error" role="alert">{error}</p>}
      </form>}
      {report?.disclosure && <p className="pilot-disclosure">{report.disclosure}</p>}
    </section>
  );
}
