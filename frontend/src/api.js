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

const RETRYABLE_READ_STATUSES = new Set([502, 503, 504]);
const RETRYABLE_READ_ATTEMPTS = 3;
const REQUEST_TIMEOUT_MS = 30000;
const COUNCIL_TIMEOUT_MS = 180000;

async function fetchWithTimeout(url, options = {}, timeoutMs = REQUEST_TIMEOUT_MS) {
  const controller = new AbortController();
  const timer = globalThis.setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(url, { ...options, signal: controller.signal });
  } catch (error) {
    if (error?.name === "AbortError") {
      throw new Error("Driftline API request timed out; retry the operation.");
    }
    throw error;
  } finally {
    globalThis.clearTimeout(timer);
  }
}

function waitForRetry(attempt) {
  // Keep cold-start recovery bounded and quiet. Only idempotent reads use
  // this path; mutations must never be replayed without an explicit
  // idempotency contract from the caller.
  return new Promise((resolve) => window.setTimeout(resolve, 250 * (2 ** attempt)));
}

async function request(path, options = {}) {
  const {
    authenticated = false,
    timeoutMs = REQUEST_TIMEOUT_MS,
    ...fetchOptions
  } = options;
  const headers = new Headers({ "Content-Type": "application/json", ...(fetchOptions.headers || {}) });
  if (authenticated && operatorSession.identityToken) {
    headers.set("Authorization", `Bearer ${operatorSession.identityToken}`);
  }
  const method = (fetchOptions.method || "GET").toUpperCase();
  const canRetry = method === "GET" || method === "HEAD" || method === "OPTIONS";
  let response;
  let lastError;
  for (let attempt = 0; attempt < (canRetry ? RETRYABLE_READ_ATTEMPTS : 1); attempt += 1) {
    try {
      response = await fetchWithTimeout(
        `${API_BASE}${path}`,
        { ...fetchOptions, headers },
        timeoutMs,
      );
    } catch (error) {
      lastError = error;
      if (!canRetry || attempt === RETRYABLE_READ_ATTEMPTS - 1) throw error;
      await waitForRetry(attempt);
      continue;
    }
    if (!canRetry || !RETRYABLE_READ_STATUSES.has(response.status) || attempt === RETRYABLE_READ_ATTEMPTS - 1) break;
    await waitForRetry(attempt);
  }
  if (!response) throw lastError || new Error("Driftline API did not return a response");
  if (response.status === 401 && authenticated && operatorSession.identityToken) {
    // Google ID tokens are intentionally short-lived and are held only in
    // memory. Once the backend rejects one, fail closed immediately instead
    // of leaving the console in a stale authenticated tenant lane. The
    // public evaluation lane remains available and the operator can sign in
    // again without reloading the page.
    clearOperatorSession();
    if (typeof window !== "undefined") {
      window.dispatchEvent(new CustomEvent("driftline:operator-session-expired"));
    }
  }
  if (!response.ok) {
    let detail = "";
    try {
      const payload = await response.json();
      detail = typeof payload?.detail === "string"
        ? payload.detail
        : payload?.detail?.message || "";
    } catch { /* non-JSON response */ }
    if (response.status === 429) {
      const retryAfter = Number(response.headers.get("Retry-After"));
      if (Number.isFinite(retryAfter) && retryAfter > 0) {
        const minutes = Math.max(1, Math.ceil(retryAfter / 60));
        const recovery = `Retry after approximately ${minutes} minute${minutes === 1 ? "" : "s"}.`;
        detail = detail ? `${detail} ${recovery}` : recovery;
      }
    }
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

export function getHealth() {
  return request("/health");
}

export function startDecisionTwin() {
  return request("/api/decision-twin/demo", {
    method: "POST",
    timeoutMs: COUNCIL_TIMEOUT_MS,
  });
}

export function getDecisionTwin(caseId) {
  return request(`/api/decision-twin/${encodeURIComponent(caseId)}`);
}

export function getDecisionTwinEvaluation(caseId) {
  return request(`/api/decision-twin/${encodeURIComponent(caseId)}/evaluation`);
}

export function approveDecisionTwin(caseId, optionId, synthesisHash, generation, approver = "Demo Product Manager") {
  return request(`/api/decision-twin/${encodeURIComponent(caseId)}/approve`, {
    method: "POST",
    body: JSON.stringify({
      approver,
      option_id: optionId,
      expected_synthesis_hash: synthesisHash,
      expected_generation: generation,
    }),
  });
}

export function recordDecisionTwinOutcome(caseId, generation, scenario = "guardrail_breach") {
  return request(`/api/decision-twin/${encodeURIComponent(caseId)}/outcomes/demo`, {
    method: "POST",
    body: JSON.stringify({ expected_generation: generation, scenario }),
  });
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

export function updateSourceLifecycle(sourceId, enabled, reason = "") {
  return request(`/api/operator/sources/${encodeURIComponent(sourceId)}/lifecycle`, {
    method: "POST",
    authenticated: true,
    body: JSON.stringify({
      enabled: Boolean(enabled),
      reason,
      operator: operatorSession.email || "Google operator",
      tenant_id: operatorSession.tenantId,
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
  const params = new URLSearchParams();
  if (operatorSession.identityToken && operatorSession.tenantId) {
    params.set("operator", operatorSession.email || "Google operator");
    params.set("tenant_id", operatorSession.tenantId);
  }
  return request(`/api/ops/value-proof${params.toString() ? `?${params}` : ""}`, {
    authenticated: Boolean(operatorSession.identityToken),
  });
}

export function getLatestEvaluation() {
  const params = new URLSearchParams();
  if (operatorSession.identityToken && operatorSession.tenantId) {
    params.set("operator", operatorSession.email || "Google operator");
    params.set("tenant_id", operatorSession.tenantId);
  }
  return request(`/api/evals/latest${params.toString() ? `?${params}` : ""}`, {
    authenticated: Boolean(operatorSession.identityToken),
  });
}

export function getEvaluationHistory(limit = 12) {
  const params = new URLSearchParams({ limit: String(limit) });
  if (operatorSession.identityToken && operatorSession.tenantId) {
    params.set("operator", operatorSession.email || "Google operator");
    params.set("tenant_id", operatorSession.tenantId);
  }
  return request(`/api/evals/history?${params.toString()}`, {
    authenticated: Boolean(operatorSession.identityToken),
  });
}

export function runEvaluation(workflowId = null) {
  return request("/api/evals/run", {
    method: "POST",
    authenticated: Boolean(operatorSession.identityToken),
    body: JSON.stringify({
      ...(workflowId ? { workflow_id: workflowId } : {}),
      ...(operatorSession.identityToken && operatorSession.tenantId ? signedContext() : {}),
    }),
  });
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

export async function downloadPilotPacket(cohortLabel = "") {
  const params = new URLSearchParams();
  if (cohortLabel.trim()) params.set("cohort_label", cohortLabel.trim());
  if (operatorSession.identityToken && operatorSession.tenantId) {
    params.set("operator", operatorSession.email || "Google operator");
    params.set("tenant_id", operatorSession.tenantId);
  }
  const headers = operatorSession.identityToken
    ? { Authorization: `Bearer ${operatorSession.identityToken}` }
    : {};
  const response = await fetchWithTimeout(`${API_BASE}/api/ops/pilot-packet?${params}`, { headers });
  if (!response.ok) throw new Error(`Driftline API returned ${response.status}`);
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "driftline-pilot-packet.md";
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
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
  const response = await fetchWithTimeout(`${API_BASE}/api/workflows/${encodeURIComponent(workflowId)}/packet${params}`, { headers });
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

export function getMemorySummary(limit = 50, operatorSession = {}) {
  const params = new URLSearchParams({ limit: String(limit) });
  if (operatorSession.identityToken && operatorSession.tenantId) {
    params.set("operator", operatorSession.email || "Google operator");
    params.set("tenant_id", operatorSession.tenantId);
  }
  return request(`/api/memory/summary?${params.toString()}`, {
    authenticated: Boolean(operatorSession.identityToken),
  });
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

export function reconcileWorkflow(workflowId) {
  return request(`/api/workflows/${workflowId}/reconcile`, {
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
