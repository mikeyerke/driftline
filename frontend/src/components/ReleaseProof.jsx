import { Activity, CheckCircle2, ShieldCheck, XCircle } from "lucide-react";
import { useEffect, useState } from "react";
import { getHealth, getLatestEvaluation, getMonitorRegistry } from "../api";

const percent = (value) => value === null || value === undefined ? "—" : `${Math.round(Number(value) * 100)}%`;
const releasePart = (value, length) => typeof value === "string" && value && value !== "unknown" ? value.slice(0, length) : null;
const isReleaseSha = (value) => typeof value === "string" && /^[0-9a-f]{40}$/.test(value);

export default function ReleaseProof({ compact = false }) {
  const [evaluation, setEvaluation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [monitor, setMonitor] = useState(null);
  const [monitorLoading, setMonitorLoading] = useState(true);
  const [health, setHealth] = useState(null);
  const [healthLoading, setHealthLoading] = useState(true);

  useEffect(() => {
    let active = true;
    const refreshMonitor = () => {
      getMonitorRegistry()
        .then((payload) => active && setMonitor(payload.summary || null))
        .catch(() => active && setMonitor(null))
        .finally(() => active && setMonitorLoading(false));
    };
    getLatestEvaluation()
      .then((payload) => active && setEvaluation(payload.evaluation || null))
      .catch(() => active && setEvaluation(null))
      .finally(() => active && setLoading(false));
    refreshMonitor();
    getHealth()
      .then((payload) => active && setHealth(payload || null))
      .catch(() => active && setHealth(null))
      .finally(() => active && setHealthLoading(false));
    // Cadence due state changes even when the release and trace gate do not.
    // Keep the operator-facing proof honest without requiring a full reload.
    const timer = window.setInterval(refreshMonitor, 60_000);
    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, []);

  const releaseShaValue = isReleaseSha(health?.release_sha) ? health.release_sha : null;
  const releaseSha = releaseShaValue ? releasePart(releaseShaValue, 7) : null;
  const buildId = releasePart(health?.build_id, 8);
  const releaseVersioned = Boolean(releaseSha && buildId);
  const evaluationNotBound = Boolean(evaluation && releaseVersioned && evaluation.release_sha !== releaseShaValue);
  const gateChecking = loading || healthLoading;
  const passed = Boolean(
    !gateChecking &&
    health?.status === "ok" &&
    evaluation &&
    releaseVersioned &&
    !evaluationNotBound &&
    evaluation.gate_status === "pass",
  );
  const blocked = Boolean(!gateChecking && evaluation && !passed);
  const label = compact
    ? gateChecking
      ? "Checking"
      : health?.status !== "ok"
        ? "Unavailable"
        : !evaluation
          ? "Unavailable"
          : !releaseVersioned
            ? "Unversioned"
            : evaluationNotBound
              ? "Trace refresh needed"
              : passed
                ? `Verified · ${percent(evaluation.overall_score)}`
                : "Review required"
    : gateChecking
      ? "Checking"
      : health?.status !== "ok"
        ? "Unavailable"
        : !evaluation
          ? "Unavailable"
          : !releaseVersioned
            ? "Unversioned"
            : evaluationNotBound
              ? "Trace refresh needed"
              : passed
                ? `Pass · ${percent(evaluation.overall_score)}`
                : "Blocked";
  // A release-bound trace mismatch is actionable but not a production outage.
  // Keep it visually distinct from a failed gate so the public judge lane does
  // not look broken while still telling an operator to refresh the trace.
  const GateIcon = passed ? CheckCircle2 : evaluationNotBound ? ShieldCheck : blocked ? XCircle : ShieldCheck;
  const monitorLabel = monitor
    ? `${monitor.healthy || 0}/${monitor.total || 0} healthy${compact ? "" : monitor.due ? ` · ${monitor.due} due` : ""}`
    : monitorLoading
      ? "Checking"
      : "Unavailable";
  const monitorDegraded = Boolean(monitor && ((monitor.stale || 0) > 0 || (monitor.source_failed || 0) > 0));
  const monitorAttention = monitor
    ? [
      monitor.stale ? `${monitor.stale} stale` : null,
      monitor.source_failed ? `${monitor.source_failed} failed` : null,
      monitor.needs_baseline ? `${monitor.needs_baseline} need a baseline` : null,
      monitor.paused ? `${monitor.paused} paused` : null,
      monitor.due ? `${monitor.due} due for check` : null,
    ].filter(Boolean).join(" · ")
    : "Monitor readiness is unavailable";
  const releaseLabel = releaseVersioned
    ? `${releaseSha} · ${buildId}`
    : healthLoading
      ? "Checking"
      : health?.status === "ok"
        ? "Unversioned"
        : "Unavailable";
  const releaseTitle = health
    ? `Serving SHA: ${health.release_sha || "unknown"}; build: ${health.build_id || "unknown"}`
    : undefined;
  const gateTitle = evaluationNotBound
    ? `Trace evaluation SHA: ${evaluation.release_sha || "unknown"}; serving SHA: ${health.release_sha}. Run a fresh evaluation for this release.`
    : undefined;

  return (
    <div className={`release-proof${compact ? " compact" : ""}`} aria-label="Latest deployment proof">
      <div className={`release-proof-item ${passed ? "pass" : evaluationNotBound ? "attention" : blocked ? "blocked" : ""}`} title={gateTitle} aria-label={gateTitle || "Latest trace gate status"}>
        <GateIcon size={14} aria-hidden="true" />
        <span><small>Latest trace gate</small><strong>{label}</strong></span>
      </div>
      <div className="release-proof-item">
        <Activity size={14} aria-hidden="true" />
        <span><small>Agent runtime</small><strong>{evaluation ? `${evaluation.execution_mode || "agent"} · ${evaluation.model || "model"}` : "Awaiting trace"}</strong></span>
      </div>
      <div className="release-proof-item">
        <span><small>Checks</small><strong>{evaluation ? `${evaluation.passed_case_count}/${evaluation.case_count}` : "—"}</strong></span>
      </div>
      <div className={`release-proof-item ${monitorDegraded ? "blocked" : monitor ? "pass" : ""}`} title={monitorAttention} aria-label={`Monitor pulse: ${monitorAttention}`}>
        <Activity size={14} aria-hidden="true" />
        <span><small>Monitor pulse</small><strong>{monitorLabel}</strong></span>
      </div>
      <div className={`release-proof-item ${releaseVersioned ? "pass" : health && health.status !== "ok" ? "blocked" : ""}`} title={releaseTitle} aria-label={releaseTitle || "Serving release status"}>
        <span><small>Serving release</small><strong>{releaseLabel}</strong></span>
      </div>
      <span className="release-proof-note">{compact ? "Judge telemetry · not customer ROI" : "Evaluation telemetry · not customer ROI"}</span>
    </div>
  );
}
