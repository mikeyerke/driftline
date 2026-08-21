import { ClipboardCheck, Clock3, Gauge, Plus, ShieldCheck } from "lucide-react";
import { useEffect, useState } from "react";
import { getPilotReport, recordOutcomeMeasurement } from "../api";

const initialForm = {
  source_type: "pilot_log",
  cohort_label: "first pilot cohort",
  changes_observed: "1",
  baseline_minutes: "60",
  driftline_minutes: "20",
  evidence_ref: "artifact://pilot-cohort",
  revenue_lift_usd: "",
  retention_lift_pct: "",
  willingness_to_pay_usd: "",
};

const numberOrNull = (value) => value === "" ? null : Number(value);

export default function PilotMeasurementPanel({ operatorSession }) {
  const [form, setForm] = useState(initialForm);
  const [report, setReport] = useState(null);
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const refresh = () => {
    if (!operatorSession?.identityToken || !operatorSession?.tenantId) return;
    getPilotReport()
      .then(setReport)
      .catch(() => setReport(null));
  };

  useEffect(() => {
    refresh();
  }, [operatorSession?.identityToken, operatorSession?.tenantId]);

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

  const measured = report?.record_count > 0;
  return (
    <section className="panel pilot-panel" aria-labelledby="pilot-title">
      <header className="panel-header">
        <div><h2 id="pilot-title"><Gauge size={17} />Pilot measurement</h2><span className="live-label public">Tenant-scoped</span></div>
        <span className="muted">Aggregate evidence only</span>
      </header>
      <div className="pilot-summary">
        <div><Clock3 size={15} /><strong>{measured ? `${report.time_saved_minutes_total}m` : "—"}</strong><small>time saved recorded</small></div>
        <div><ClipboardCheck size={15} /><strong>{report?.changes_observed || 0}</strong><small>changes measured</small></div>
        <div><ShieldCheck size={15} /><strong>{measured ? `${report.time_saved_pct}%` : "—"}</strong><small>before/after delta</small></div>
      </div>
      <p className="pilot-note">Record aggregate before/after observations from a real pilot. Driftline stores no customer names, raw notes, or CRM records; every entry remains explicitly operator-reported until independently reviewed.</p>
      <button className="secondary compact pilot-toggle" type="button" onClick={() => { setOpen((current) => !current); setMessage(""); setError(""); }}><Plus size={14} />{open ? "Close measurement form" : "Record a measurement"}</button>
      {open && <form className="pilot-form" onSubmit={submit}>
        <label>Evidence type<select name="source_type" value={form.source_type} onChange={update}><option value="pilot_log">Pilot log</option><option value="customer_interview">Customer interview</option><option value="win_loss">Win / loss</option><option value="billing_record">Billing record</option></select></label>
        <label>Cohort label<input required name="cohort_label" value={form.cohort_label} onChange={update} maxLength={80} /></label>
        <label>Changes observed<input required type="number" min="1" name="changes_observed" value={form.changes_observed} onChange={update} /></label>
        <label>Baseline minutes<input required type="number" min="0" step="0.1" name="baseline_minutes" value={form.baseline_minutes} onChange={update} /></label>
        <label>Driftline minutes<input required type="number" min="0" step="0.1" name="driftline_minutes" value={form.driftline_minutes} onChange={update} /></label>
        <label>Evidence reference<input required name="evidence_ref" value={form.evidence_ref} onChange={update} placeholder="artifact://pilot-cohort or https://…" maxLength={300} /></label>
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
