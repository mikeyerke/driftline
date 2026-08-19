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

export function startDemoJob() {
  return request("/api/jobs/demo", {
    method: "POST",
    body: JSON.stringify({
      query: "Inspect the allowlisted public/pricing change, verify the evidence, map the affected artifacts, and stop at the human approval gate.",
      user_id: "demo-operator",
    }),
  });
}

export function getJob(jobId) {
  return request(`/api/jobs/${jobId}`);
}

export function getSources() {
  return request("/api/sources");
}

export function approveWorkflow(workflowId, artifactDecisions) {
  return request(`/api/workflows/${workflowId}/approve`, {
    method: "POST",
    body: JSON.stringify({
      approver: "Demo operator",
      decision: "grandfather_existing_customers",
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

export function packetUrl(workflowId) {
  return `${API_BASE}/api/workflows/${workflowId}/packet`;
}
