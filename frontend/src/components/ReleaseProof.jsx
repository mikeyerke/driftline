import { Activity, CheckCircle2, ShieldCheck, XCircle } from "lucide-react";
import { useEffect, useState } from "react";
import { getHealth, getLatestEvaluation, getMonitorRegistry } from "../api";

const percent = (value) => value === null || value === undefined ? "—" : `${Math.round(Number(value) * 100)}%`;
const releasePart = (value, length) => typeof value === "string" && value && value !== "unknown" ? value.slice(0, length) : null;
const isReleaseSha = (value) => typeof value === "string" && /^[0-9a-f]{40}$/.test(value);

export default function ReleaseProof() {
  const [evaluation, setEvaluation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [monitor, setMonitor] = useState(null);
  const [monitorLoading, setMonitorLoading] = useState(true);
  const [health, setHealth] = useState(null);
  const [healthLoading, setHealthLoading] = useState(true);

  useEffect(() => {
    let active = true;
    getLatestEvaluation()
      .then((payload) => active && setEvaluation(payload.evaluation || null))
      .catch(() => active && setEvaluation(null))
      .finally(() => active && setLoading(false));
    getMonitorRegistry()
      .then((payload) => active && setMonitor(payload.summary || null))
      .catch(() => active && setMonitor(null))
      .finally(() => active && setMonitorLoading(false));
    getHealth()
      .then((payload) => active && setHealth(payload || null))
      .catch(() => active && setHealth(null))
      .finally(() => active && setHealthLoading(false));
    return () => { active = false; };
  }, []);

  const passed = evaluation?.gate_status === "pass";
  const blocked = evaluation && !passed;
  const label = loading
    ? "Checking"
    : !evaluation
      ? "Unavailable"
      : passed
        ? `Pass · ${percent(evaluation.overall_score)}`
        : "Blocked";
  const GateIcon = passed ? CheckCircle2 : blocked ? XCircle : ShieldCheck;
  const monitorLabel = monitor
    ? `${monitor.healthy || 0}/${monitor.total || 0} healthy${monitor.due ? ` · ${monitor.due} due` : ""}`
    : monitorLoading
      ? "Checking"
      : "Unavailable";
  const monitorDegraded = Boolean(monitor && ((monitor.stale || 0) > 0 || (monitor.source_failed || 0) > 0));
  const releaseSha = isReleaseSha(health?.release_sha) ? releasePart(health.release_sha, 7) : null;
  const buildId = releasePart(health?.build_id, 8);
  const releaseVersioned = Boolean(releaseSha && buildId);
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

  return (
    <div className="release-proof" aria-label="Latest deployment proof">
      <div className={`release-proof-item ${passed ? "pass" : blocked ? "blocked" : ""}`}>
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
      <div className={`release-proof-item ${monitorDegraded ? "blocked" : monitor ? "pass" : ""}`}>
        <Activity size={14} aria-hidden="true" />
        <span><small>Monitor pulse</small><strong>{monitorLabel}</strong></span>
      </div>
      <div className={`release-proof-item ${releaseVersioned ? "pass" : health && health.status !== "ok" ? "blocked" : ""}`} title={releaseTitle} aria-label={releaseTitle || "Serving release status"}>
        <span><small>Serving release</small><strong>{releaseLabel}</strong></span>
      </div>
      <span className="release-proof-note">Evaluation telemetry · not customer ROI</span>
    </div>
  );
}
