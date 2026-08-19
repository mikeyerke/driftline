const API_BASE = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "");

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) throw new Error(`Driftline API returned ${response.status}`);
  return response.json();
}

export const apiEnabled = true;

export function startDemo() {
  return request("/api/workflows/demo", { method: "POST" });
}

export function startDemoJob(sourceId = "public/pricing") {
  return request("/api/jobs/demo", {
    method: "POST",
    body: JSON.stringify({
      query: `Inspect the selected allowlisted source change, verify the evidence, map the affected offerings and downstream artifacts, and stop at the human approval gate.`,
      user_id: "demo-operator",
      source_id: sourceId,
    }),
  });
}

export function getJob(jobId) {
  return request(`/api/jobs/${jobId}`);
}

export function listJobs(limit = 8) {
  return request(`/api/jobs?limit=${limit}`);
}

export function getSources() {
  return request("/api/sources");
}

export function approveWorkflow(workflowId, artifactDecisions, decision = "grandfather_existing_customers") {
  return request(`/api/workflows/${workflowId}/approve`, {
    method: "POST",
    body: JSON.stringify({
      approver: "Demo operator",
      decision,
      artifact_decisions: artifactDecisions,
    }),
  });
}

export function undoWorkflow(workflowId) {
  return request(`/api/workflows/${workflowId}/undo`, {
    method: "POST",
    body: JSON.stringify({ actor: "Demo operator" }),
  });
}

export function claimAction(workflowId, itemId) {
  return request(`/api/workflows/${workflowId}/actions/${itemId}/claim`, {
    method: "POST",
    body: JSON.stringify({ actor: "Demo operator" }),
  });
}

export function completeAction(workflowId, itemId) {
  return request(`/api/workflows/${workflowId}/actions/${itemId}/complete`, {
    method: "POST",
    body: JSON.stringify({ actor: "Demo operator" }),
  });
}

export function packetUrl(workflowId) {
  return `${API_BASE}/api/workflows/${workflowId}/packet`;
}
