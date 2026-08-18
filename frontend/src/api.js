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

export function approveWorkflow(workflowId) {
  return request(`/api/workflows/${workflowId}/approve`, {
    method: "POST",
    body: JSON.stringify({
      approver: "Demo operator",
      decision: "grandfather_existing_customers",
    }),
  });
}

export function undoWorkflow(workflowId) {
  return request(`/api/workflows/${workflowId}/undo`, {
    method: "POST",
    body: JSON.stringify({ actor: "Demo operator" }),
  });
}
