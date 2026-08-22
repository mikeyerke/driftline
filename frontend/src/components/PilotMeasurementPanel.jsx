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
  const workflowCount = utility.proof?.observed?.workflows || 0;
  const completedActions = utility.proof?.observed?.action_items_completed_historically || 0;
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
        <div><Clock3 size={15} /><strong>{measured ? `${report.time_saved_minutes_total}m` : "—"}</strong><small>time saved recorded</small></div>
        <div><ClipboardCheck size={15} /><strong>{report?.changes_observed || 0}</strong><small>changes measured</small></div>
        <div><ShieldCheck size={15} /><strong>{measured ? `${report.time_saved_pct}%` : "—"}</strong><small>before/after delta</small></div>
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
      <div className="pilot-actions">
        <button className="secondary compact pilot-toggle" type="button" onClick={() => { setOpen((current) => !current); setMessage(""); setError(""); }}><Plus size={14} />{open ? "Close measurement form" : "Record a measurement"}</button>
        <button className="secondary compact pilot-toggle" type="button" onClick={downloadPacket} disabled={downloading}><Download size={14} />{downloading ? "Preparing…" : "Download pilot packet"}</button>
      </div>
      {open && <form className="pilot-form" onSubmit={submit}>
        <label>Evidence type<select name="source_type" value={form.source_type} onChange={update}><option value="pilot_log">Pilot log</option><option value="customer_interview">Customer interview</option><option value="win_loss">Win / loss</option><option value="billing_record">Billing record</option></select></label>
        <label>Cohort label<input required name="cohort_label" value={form.cohort_label} onChange={update} maxLength={80} placeholder="Named pilot cohort" /></label>
        <label>Changes observed<input required type="number" min="1" name="changes_observed" value={form.changes_observed} onChange={update} placeholder="Measured count" /></label>
        <label>Baseline minutes<input required type="number" min="0" step="0.1" name="baseline_minutes" value={form.baseline_minutes} onChange={update} placeholder="Observed baseline" /></label>
        <label>Driftline minutes<input required type="number" min="0" step="0.1" name="driftline_minutes" value={form.driftline_minutes} onChange={update} placeholder="Observed Driftline time" /></label>
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
