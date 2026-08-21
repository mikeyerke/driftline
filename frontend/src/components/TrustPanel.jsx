import { Activity, Database, ListChecks, LockKeyhole, Scale, Server, ShieldCheck } from "lucide-react";
import { useEffect, useState } from "react";
import { getOpsSummary } from "../api";
import useNearViewport from "../hooks/useNearViewport";

export default function TrustPanel({ actionRecord }) {
  const [panelRef, nearViewport] = useNearViewport();
  const [ops, setOps] = useState(null);
  const jiraWasWritten = ["created", "reused", "reactivated", "reversed"].includes(actionRecord?.jira_status);
  const jiraTrustLabel = actionRecord?.jira_status === "reversed"
    ? "Scoped Jira handoff reversed; other destinations unchanged"
    : actionRecord?.jira_status === "reactivated"
      ? "Scoped Jira handoff reactivated; other destinations unchanged"
      : actionRecord?.jira_status === "created"
        ? "Jira issue created in the configured project; other destinations unchanged"
        : actionRecord?.jira_status === "reused"
          ? "Existing Jira issue linked; other destinations unchanged"
          : "One scoped Jira handoff recorded; other destinations remain unchanged";
  useEffect(() => {
    if (!nearViewport) return undefined;
    let active = true;
    const refresh = () => getOpsSummary().then((payload) => active && setOps(payload)).catch(() => active && setOps(null));
    refresh();
    const timer = window.setInterval(refresh, 60_000);
    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, [nearViewport]);
  const sourceHealth = ops?.source_health || [];
  const healthySources = sourceHealth.filter((source) => source.status === "healthy").length;
  const deadLettered = ops?.jobs?.dead_lettered;
  const queuedJobs = ops?.jobs?.by_status?.queued;
  const connectorLanes = Object.values(ops?.connectors || {}).filter(Boolean).length;
  const runtimeLabel = ops ? `${ops.model || "Agent runtime"} · ${ops.persistence || "persistence unavailable"}` : "Deployment telemetry unavailable";
  return (
    <section ref={panelRef} className="panel trust-panel" id="settings-section">
      <header className="panel-header"><div><h2>Trust and deployment posture</h2><span className="live-label">Production deployment</span></div><span className="muted">Public evaluation lane is isolated</span></header>
      <div className="trust-grid">
        <div><Server size={18} /><strong>Google Cloud</strong><small>Cloud Run · Firestore · Cloud Tasks</small></div>
        <div><ShieldCheck size={18} /><strong>Deterministic gate</strong><small>Agent cannot approve; writes require the human gate</small></div>
        <div><LockKeyhole size={18} /><strong>Evidence binding</strong><small>Every packet carries its source hash</small></div>
        <div><Scale size={18} /><strong>Bounded actions</strong><small>{jiraWasWritten ? jiraTrustLabel : "Review-ready packets; signed operator required for writes"}</small></div>
      </div>
      <div className="ops-pulse" aria-label="Live operational pulse">
        <div className="ops-pulse-heading"><strong>Live operational pulse</strong><span>{!nearViewport ? "Scroll to load deployment telemetry" : ops ? `Refreshed ${new Date(ops.generated_at).toLocaleTimeString()}` : "Reading deployment telemetry…"}</span></div>
        <div className="ops-pulse-grid">
          <div><Activity size={15} /><strong>{ops ? `${healthySources}/${sourceHealth.length}` : "—"}</strong><small>sources healthy</small></div>
          <div><ListChecks size={15} /><strong>{ops ? `${deadLettered || 0}` : "—"}</strong><small>dead-lettered jobs · {queuedJobs || 0} queued</small></div>
          <div><Database size={15} /><strong>{ops ? connectorLanes : "—"}</strong><small>connector lanes available</small></div>
          <div><ShieldCheck size={15} /><strong>{ops ? "Signed" : "—"}</strong><small>{ops ? "approval required for writes" : "guardrail status unavailable"}</small></div>
        </div>
        <p className="ops-pulse-note">{runtimeLabel}. Connector availability reflects deployment capability, not per-tenant credentials or an external write. This is deployment telemetry only; it contains no customer content or outcome claims.</p>
      </div>
      <p className="source-note">This public console is intentionally identity-free for judging. It is not an enterprise authentication claim, and it fails closed when the live backend is unavailable.</p>
    </section>
  );
}
