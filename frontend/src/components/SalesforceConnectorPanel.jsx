import { AlertCircle, CheckCircle2, ExternalLink, RefreshCw, ShieldCheck } from "lucide-react";
import { useEffect, useState } from "react";
import { getSalesforceHealth, getSalesforceStatus, startSalesforceConnection } from "../api";

const fallbackObjects = ["Product2", "PricebookEntry", "Opportunity"];

function statusCopy(status, aggregateReadVerified = false) {
  if (status === "connected_read_only") {
    return aggregateReadVerified ? "Connected · read verified" : "Connected · probe required";
  }
  if (status === "reauthorization_required") return "Reauthorization required";
  if (status === "setup_incomplete") return "Reconnect to finish setup";
  if (status === "oauth_ready") return "Authorization required";
  if (status === "not_configured") return "Not configured";
  if (status === "invalid_config") return "Configuration needs attention";
  return "Prepared only";
}

export default function SalesforceConnectorPanel({ operatorSession }) {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [authorizing, setAuthorizing] = useState(false);
  const [health, setHealth] = useState(null);
  const [error, setError] = useState("");

  const refreshStatus = async ({ clearHealth = true } = {}) => {
    if (!operatorSession?.identityToken || !operatorSession?.tenantId) return null;
    setLoading(true);
    setError("");
    try {
      const nextStatus = await getSalesforceStatus();
      setStatus(nextStatus);
      if (clearHealth) setHealth(null);
      return nextStatus;
    } catch (requestError) {
      setError(requestError.message || "Salesforce status could not be read");
      return null;
    } finally {
      setLoading(false);
    }
  };

  const loadStatus = () => refreshStatus();

  useEffect(() => {
    setStatus(null);
    setHealth(null);
    setError("");
    if (operatorSession?.identityToken && operatorSession?.tenantId) loadStatus();
    // The session object changes on sign-in/tenant switch; the explicit
    // Refresh button handles subsequent status checks without polling.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [operatorSession?.identityToken, operatorSession?.tenantId]);

  useEffect(() => {
    if (!operatorSession?.identityToken || !operatorSession?.tenantId) return undefined;

    // OAuth opens in a separate tab. Refresh the metadata-only status when the
    // operator returns so a successful callback (or an explicit reauthorization
    // failure) is visible without requiring a second manual click. This does
    // not probe Salesforce or poll while the operator remains in Driftline.
    const refreshOnReturn = () => {
      // Starting OAuth can briefly return focus to this tab before the
      // authorization URL has rendered. Do not immediately overwrite the
      // handoff with the stale reauthorization state; refresh only after the
      // operator actually returns from the provider tab.
      if (!document.hidden && !authorizing) void refreshStatus({ clearHealth: false });
    };
    window.addEventListener("focus", refreshOnReturn);
    document.addEventListener("visibilitychange", refreshOnReturn);
    return () => {
      window.removeEventListener("focus", refreshOnReturn);
      document.removeEventListener("visibilitychange", refreshOnReturn);
    };
    // Session identity and the short authorization-handoff guard are the only
    // lifecycle inputs; refreshStatus is intentionally excluded to avoid
    // re-registering listeners every render.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [operatorSession?.identityToken, operatorSession?.tenantId, authorizing]);

  const beginAuthorization = async () => {
    setAuthorizing(true);
    setError("");
    try {
      const result = await startSalesforceConnection();
      setStatus((current) => ({
        ...(current || {}),
        status: "oauth_ready",
        mode: "awaiting_authorization",
        authorization_required: true,
        authorize_url: result.authorize_url,
        expires_in_seconds: result.expires_in_seconds,
      }));
    } catch (requestError) {
      setError(requestError.message || "Salesforce authorization could not start");
    } finally {
      setAuthorizing(false);
    }
  };

  const runHealth = async () => {
    if (!operatorSession?.identityToken || !operatorSession?.tenantId) return;
    setLoading(true);
    setError("");
    try {
      const [nextHealth, nextStatus] = await Promise.all([getSalesforceHealth(), getSalesforceStatus()]);
      setHealth(nextHealth);
      setStatus(nextStatus);
    } catch (requestError) {
      setError(requestError.message || "Salesforce read probe failed");
    } finally {
      setLoading(false);
    }
  };

  const signedIn = Boolean(operatorSession?.identityToken);
  const owner = operatorSession?.role === "owner";
  const bindingConnected = status?.status === "connected_read_only";
  const aggregateReadVerified = Boolean(status?.aggregate_read_verified);
  const objects = status?.allowed_objects || fallbackObjects;

  return (
    <section id="settings-section" className="panel salesforce-panel" aria-labelledby="salesforce-title">
      <header className="panel-header">
        <div><h2 id="salesforce-title">Salesforce CRM context</h2><span className={`live-label ${signedIn ? "public" : "synthetic"}`}>{signedIn ? "Read-only" : "Prepared · consent required"}</span></div>
        <span className="muted">No CRM writes</span>
      </header>
      <div className="salesforce-body">
        <div className="salesforce-heading">
          <div className="salesforce-icon"><ShieldCheck size={17} /></div>
          <div><strong>Ground impact decisions with bounded CRM context</strong><small>Driftline reads aggregate metadata only. It never copies Salesforce records into the workflow or creates CRM changes.</small></div>
        </div>
        {!signedIn && <p className="salesforce-note"><AlertCircle size={14} /><strong>No CRM context is available in this public lane.</strong> Sign in with Google above to manage a tenant-scoped, read-only Salesforce connection; the aggregate probe must pass all three allowlisted objects before any CRM context can influence a workflow.</p>}
        {signedIn && <>
          <div className="salesforce-status-row">
            <span className={aggregateReadVerified ? "salesforce-status ready" : "salesforce-status"}>{aggregateReadVerified ? <CheckCircle2 size={14} /> : <AlertCircle size={14} />}{statusCopy(status?.status, aggregateReadVerified)}</span>
            <span className="salesforce-tenant">{operatorSession.tenantId} · {operatorSession.role}</span>
            <button className="secondary compact" type="button" onClick={loadStatus} disabled={loading}><RefreshCw size={13} className={loading ? "spin" : ""} />Refresh</button>
          </div>
          {status?.instance_hostname && <small className="salesforce-instance">Instance: {status.instance_hostname}</small>}
          <div className="salesforce-scope"><strong>Allowlisted objects</strong><span>{objects.join(" · ")}</span></div>
          {status?.aggregate_read_status && <div className={`salesforce-read-proof${status.aggregate_read_verified ? " verified" : ""}`} role="status">
            <strong>{status.aggregate_read_verified ? "Aggregate read verified" : status.aggregate_read_status === "reauthorization_required" ? "Aggregate read needs reauthorization" : status.aggregate_read_status === "setup_incomplete" ? "Aggregate read setup incomplete" : "Aggregate read not verified"}</strong>
            <span>{status.aggregate_read_verified
              ? `${status.aggregate_read_objects?.map((item) => `${item.object}: ${item.total}`).join(" · ") || "Allowlisted object counts recorded"}${status.aggregate_read_verified_at ? ` · ${new Date(status.aggregate_read_verified_at).toLocaleString()}` : ""}`
              : status.aggregate_read_reason === "refresh_token_rejected" ? "Salesforce rejected the stored refresh token; reconnect before using CRM context." : status.aggregate_read_reason === "connector_binding_missing" ? "A prior connection record exists, but its tenant binding is incomplete. Reconnect to rerun the verification gate; no CRM context is used." : status.aggregate_read_failures?.length ? `The probe reached Salesforce but these allowlisted objects did not read: ${status.aggregate_read_failures.map((item) => `${item.object} (${item.reason})`).join(" · ")}. No CRM context is used until all three pass.` : "Run the explicit read probe after authorization."}</span>
            {!status.aggregate_read_verified && status.aggregate_read_objects?.length > 0 && <small className="salesforce-read-partial">Read successfully: {status.aggregate_read_objects.map((item) => `${item.object} (${item.total})`).join(" · ")}</small>}
            {status.next_step && !status.aggregate_read_verified && <small className="salesforce-next-step">Next step · {status.next_step}</small>}
          </div>}
          {status?.authorization_required && <div className="salesforce-connect-action"><p>{status.status === "reauthorization_required" || status.status === "setup_incomplete" ? "Reconnect Driftline’s read-only Salesforce access. The callback reruns all three aggregate queries before activating the tenant binding; no partial credential is treated as connected." : "Authorize Driftline’s read-only access in Salesforce. The one-time state and PKCE verifier stay server-side; the refresh token is stored only in the tenant Secret Manager namespace."}</p>{status.authorize_url ? <a className="primary salesforce-auth-link" href={status.authorize_url} target="_blank" rel="noreferrer"><ExternalLink size={14} />Continue to Salesforce consent</a> : <button className="primary" type="button" onClick={beginAuthorization} disabled={!owner || authorizing}>{authorizing ? "Preparing…" : status.status === "reauthorization_required" || status.status === "setup_incomplete" ? "Reconnect read-only" : "Prepare Salesforce authorization"}</button>}{!owner && <small>Tenant owner role required to authorize a connector.</small>}</div>}
          {bindingConnected && <div className="salesforce-connect-action"><div className="salesforce-action-row"><button className="secondary" type="button" onClick={runHealth} disabled={loading}>{loading ? <><RefreshCw size={14} className="spin" />Reading…</> : <><ShieldCheck size={14} />Run aggregate read probe</>}</button><button className="text-button" type="button" onClick={beginAuthorization} disabled={authorizing}>{authorizing ? "Preparing…" : "Reauthorize read-only"}</button></div>{health && <div className={`salesforce-health${health.aggregate_read_verified ? "" : " warning"}`} role="status"><strong>{health.aggregate_read_verified ? "Read verified" : health.status === "reauthorization_required" ? "Reauthorization required" : "Read unavailable"}</strong>{health.status === "reauthorization_required" && <span>Salesforce rejected the stored refresh token. Use “Reauthorize read-only” to renew consent.</span>}{health.status === "connected_read_only" && health.objects?.map((item) => <span key={item.object}>{item.object}: {item.total}</span>)}{health.status === "failed" && <><span>No CRM context was attached because the full allowlist did not pass.</span>{health.failed_objects?.map((item) => <span key={item.object}>{item.object}: {item.reason}</span>)}</>}</div>}</div>}
        </>}
        {error && <p className="salesforce-error" role="alert"><AlertCircle size={14} />{error}</p>}
      </div>
      <footer className="salesforce-footer">Scope: <strong>read_only_context</strong> · External writes: <strong>No</strong> · Credential values exposed: <strong>No</strong></footer>
    </section>
  );
}
