const API_BASE = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "");

// The ID token is held in memory only. It is never written to localStorage,
// URL parameters, analytics, or the repository. The backend revalidates it on
// every signed request and resolves the selected tenant from Firestore.
let operatorSession = { identityToken: null, email: null, tenants: [], tenantId: null, role: null };
const operatorListeners = new Set();

export function getOperatorSession() {
  return operatorSession;
}

export function subscribeOperatorSession(listener) {
  operatorListeners.add(listener);
  return () => operatorListeners.delete(listener);
}

export function setOperatorSession(next = {}) {
  operatorSession = { ...operatorSession, ...next };
  operatorListeners.forEach((listener) => listener(operatorSession));
}

export function clearOperatorSession() {
  operatorSession = { identityToken: null, email: null, tenants: [], tenantId: null, role: null };
  operatorListeners.forEach((listener) => listener(operatorSession));
}

function signedContext() {
  if (!operatorSession.identityToken || !operatorSession.tenantId) return {};
  // Keep the short-lived Google ID token in the Authorization header only.
  // The API middleware reads that header for every signed route; duplicating
  // it in JSON would unnecessarily widen exposure to request-body telemetry.
  return {
    operator: operatorSession.email || "Google operator",
    tenant_id: operatorSession.tenantId,
    approval_mode: "signed",
  };
}

async function request(path, options = {}) {
  const { authenticated = false, ...fetchOptions } = options;
  const headers = new Headers({ "Content-Type": "application/json", ...(fetchOptions.headers || {}) });
  if (authenticated && operatorSession.identityToken) {
    headers.set("Authorization", `Bearer ${operatorSession.identityToken}`);
  }
  const response = await fetch(`${API_BASE}${path}`, { ...fetchOptions, headers });
  if (!response.ok) {
    let detail = "";
    try { detail = (await response.json()).detail || ""; } catch { /* non-JSON response */ }
    throw new Error(detail || `Driftline API returned ${response.status}`);
  }
  return response.json();
}

export const apiEnabled = true;

export function startDemo() {
  return request("/api/workflows/demo", { method: "POST" });
}

export function startDemoJob(sourceId = "public/pricing", runMode = null) {
  const tenantRunMode = runMode || "tenant_demo";
  return request("/api/jobs/demo", {
    method: "POST",
    authenticated: Boolean(operatorSession.identityToken),
    body: JSON.stringify({
      query: `Inspect the selected allowlisted source change, verify the evidence, map the affected offerings and downstream artifacts, and stop at the human approval gate.`,
      user_id: "demo-operator",
      source_id: sourceId,
      ...(operatorSession.identityToken && operatorSession.tenantId
        ? {
            // Registered public URLs must use the production monitor lane. A
            // tenant_demo run is intentionally limited to pinned fixtures.
            run_mode: tenantRunMode,
            user_id: operatorSession.email || "google-operator",
            operator: operatorSession.email || "Google operator",
            tenant_id: operatorSession.tenantId,
          }
        : {}),
    }),
  });
}

export function getJob(jobId) {
  const params = operatorSession.identityToken && operatorSession.tenantId
    ? `?operator=${encodeURIComponent(operatorSession.email || "Google operator")}&tenant_id=${encodeURIComponent(operatorSession.tenantId)}`
    : "";
  return request(`/api/jobs/${jobId}${params}`, { authenticated: Boolean(operatorSession.identityToken) });
}

export function retryJob(jobId) {
  return request(`/api/jobs/${encodeURIComponent(jobId)}/retry`, {
    method: "POST",
    authenticated: true,
    body: JSON.stringify(signedContext()),
  });
}

export function listJobs(limit = 8) {
  const params = new URLSearchParams({ limit: String(limit) });
  if (operatorSession.identityToken && operatorSession.tenantId) {
    params.set("operator", operatorSession.email || "Google operator");
    params.set("tenant_id", operatorSession.tenantId);
  }
  return request(`/api/jobs?${params.toString()}`, { authenticated: Boolean(operatorSession.identityToken) });
}

export function getAuthConfig() {
  return request("/api/auth/config");
}

export function getAvailableTenants(identityToken) {
  return request("/api/tenants/available", {
    authenticated: Boolean(identityToken),
    headers: identityToken ? { Authorization: `Bearer ${identityToken}` } : undefined,
  });
}

export function getSources() {
  const params = new URLSearchParams();
  if (operatorSession.identityToken && operatorSession.tenantId) {
    params.set("operator", operatorSession.email || "Google operator");
    params.set("tenant_id", operatorSession.tenantId);
  }
  return request(`/api/sources${params.toString() ? `?${params}` : ""}`, { authenticated: Boolean(operatorSession.identityToken) });
}

export function getMonitorRegistry() {
  const params = new URLSearchParams();
  if (operatorSession.identityToken && operatorSession.tenantId) {
    params.set("operator", operatorSession.email || "Google operator");
    params.set("tenant_id", operatorSession.tenantId);
  }
  return request(`/api/monitor/registry${params.toString() ? `?${params}` : ""}`, { authenticated: Boolean(operatorSession.identityToken) });
}

export function registerSource(source) {
  return request("/api/operator/sources", {
    method: "POST",
    authenticated: true,
    body: JSON.stringify({
      ...source,
      tenant_id: operatorSession.tenantId,
      registered_by: operatorSession.email || "Google operator",
      ...signedContext(),
    }),
  });
}

export function getOpsSummary() {
  const params = new URLSearchParams();
  if (operatorSession.identityToken && operatorSession.tenantId) {
    params.set("operator", operatorSession.email || "Google operator");
    params.set("tenant_id", operatorSession.tenantId);
  }
  return request(`/api/ops/summary${params.toString() ? `?${params}` : ""}`, { authenticated: Boolean(operatorSession.identityToken) });
}

export function getConnectorContextSummary() {
  return request("/api/connectors/context/summary", {
    method: "POST",
    authenticated: true,
    body: JSON.stringify(signedContext()),
  });
}

export function getConnectorBindingsHealth() {
  const params = new URLSearchParams();
  if (operatorSession.identityToken && operatorSession.tenantId) {
    params.set("operator", operatorSession.email || "Google operator");
    params.set("tenant_id", operatorSession.tenantId);
  }
  return request(`/api/connectors/bindings/health?${params.toString()}`, { authenticated: true });
}

export function getSalesforceStatus() {
  const params = new URLSearchParams({
    operator: operatorSession.email || "Google operator",
  });
  if (operatorSession.tenantId) params.set("tenant_id", operatorSession.tenantId);
  return request(`/api/connectors/salesforce/status?${params.toString()}`, { authenticated: true });
}

export function startSalesforceConnection() {
  return request("/api/connectors/salesforce/start", {
    method: "POST",
    authenticated: true,
    body: JSON.stringify(signedContext()),
  });
}

export function getSalesforceHealth() {
  return request("/api/connectors/salesforce/health", {
    method: "POST",
    authenticated: true,
    body: JSON.stringify(signedContext()),
  });
}

export function getValueProof() {
  return request("/api/ops/value-proof");
}

export function getPilotReport(cohortLabel = "") {
  const params = new URLSearchParams();
  if (cohortLabel.trim()) params.set("cohort_label", cohortLabel.trim());
  if (operatorSession.identityToken && operatorSession.tenantId) {
    params.set("operator", operatorSession.email || "Google operator");
    params.set("tenant_id", operatorSession.tenantId);
  }
  return request(`/api/ops/pilot-report?${params.toString()}`, { authenticated: true });
}

export function recordOutcomeMeasurement(measurement) {
  return request("/api/ops/outcomes", {
    method: "POST",
    authenticated: true,
    body: JSON.stringify({ ...measurement, ...signedContext() }),
  });
}

export function getSourceHistory(sourceId, limit = 8) {
  const params = new URLSearchParams({ limit: String(limit) });
  if (operatorSession.identityToken && operatorSession.tenantId) {
    params.set("operator", operatorSession.email || "Google operator");
    params.set("tenant_id", operatorSession.tenantId);
  }
  return request(`/api/sources/${encodeURIComponent(sourceId)}/history?${params}`, { authenticated: Boolean(operatorSession.identityToken) });
}

export function getMultimodalEvidence(assetId = "promise-card", mode = "live") {
  return request(`/api/multimodal/evidence/${encodeURIComponent(assetId)}?mode=${mode}`);
}

export function analyzeMultimodalEvidence(assetId = "promise-card", mode = "live") {
  return request("/api/multimodal/analyze", {
    method: "POST",
    body: JSON.stringify({ asset_id: assetId, mode }),
  });
}

export function multimodalAssetUrl(assetId, side, mode = "live") {
  return `${API_BASE}/api/multimodal/assets/${encodeURIComponent(assetId)}/${side}?mode=${mode}`;
}

export function getWorkflowScenarios(workflowId) {
  const params = operatorSession.identityToken && operatorSession.tenantId
    ? `?operator=${encodeURIComponent(operatorSession.email || "Google operator")}&tenant_id=${encodeURIComponent(operatorSession.tenantId)}`
    : "";
  return request(`/api/workflows/${encodeURIComponent(workflowId)}/scenarios${params}`, { authenticated: Boolean(operatorSession.identityToken) });
}

export async function downloadPacket(workflowId) {
  const params = operatorSession.identityToken && operatorSession.tenantId
    ? `?operator=${encodeURIComponent(operatorSession.email || "Google operator")}&tenant_id=${encodeURIComponent(operatorSession.tenantId)}`
    : "";
  const headers = operatorSession.identityToken
    ? { Authorization: `Bearer ${operatorSession.identityToken}` }
    : {};
  const response = await fetch(`${API_BASE}/api/workflows/${encodeURIComponent(workflowId)}/packet${params}`, { headers });
  if (!response.ok) throw new Error(`Driftline API returned ${response.status}`);
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `driftline-change-packet-${workflowId}.md`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export function getMemorySummary(limit = 50) {
  return request(`/api/memory/summary?limit=${limit}`);
}

export function approveWorkflow(workflowId, artifactDecisions, decision = "grandfather_existing_customers", copilotOptionId = null, copilotArtifactOverride = false, copilotOverrideReason = null) {
  return request(`/api/workflows/${workflowId}/approve`, {
    method: "POST",
    authenticated: Boolean(operatorSession.identityToken),
    body: JSON.stringify({
      approver: operatorSession.email || "Demo operator",
      decision,
      artifact_decisions: artifactDecisions,
      copilot_option_id: copilotOptionId,
      copilot_artifact_override: copilotArtifactOverride,
      copilot_override_reason: copilotOverrideReason,
      ...signedContext(),
    }),
  });
}

export function undoWorkflow(workflowId) {
  return request(`/api/workflows/${workflowId}/undo`, {
    method: "POST",
    authenticated: Boolean(operatorSession.identityToken),
    body: JSON.stringify({ actor: operatorSession.email || "Demo operator", ...signedContext() }),
  });
}

export function dismissWorkflow(workflowId, reason = "Reviewed as non-material for the current segment") {
  return request(`/api/workflows/${workflowId}/dismiss`, {
    method: "POST",
    authenticated: Boolean(operatorSession.identityToken),
    body: JSON.stringify({ actor: operatorSession.email || "Demo operator", reason, ...signedContext() }),
  });
}

export function claimAction(workflowId, itemId) {
  return request(`/api/workflows/${workflowId}/actions/${itemId}/claim`, {
    method: "POST",
    authenticated: Boolean(operatorSession.identityToken),
    body: JSON.stringify({ actor: operatorSession.email || "Demo operator", ...signedContext() }),
  });
}

export function completeAction(workflowId, itemId) {
  return request(`/api/workflows/${workflowId}/actions/${itemId}/complete`, {
    method: "POST",
    authenticated: Boolean(operatorSession.identityToken),
    body: JSON.stringify({ actor: operatorSession.email || "Demo operator", ...signedContext() }),
  });
}

export function failAction(workflowId, itemId, reason = "Owner action needs a retry") {
  return request(`/api/workflows/${workflowId}/actions/${itemId}/fail`, {
    method: "POST",
    authenticated: Boolean(operatorSession.identityToken),
    body: JSON.stringify({ actor: operatorSession.email || "Demo operator", reason, ...signedContext() }),
  });
}

export function retryAction(workflowId, itemId) {
  return request(`/api/workflows/${workflowId}/actions/${itemId}/retry`, {
    method: "POST",
    authenticated: Boolean(operatorSession.identityToken),
    body: JSON.stringify({ actor: operatorSession.email || "Demo operator", ...signedContext() }),
  });
}

export function packetUrl(workflowId) {
  return `${API_BASE}/api/workflows/${workflowId}/packet`;
}
