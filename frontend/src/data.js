export const artifacts = [
  {
    name: "Pricing battlecard",
    owner: "Product Marketing",
    action: "Replace claim",
    risk: "High",
    status: "Draft ready",
    detail: "Claims & positioning",
  },
  {
    name: "Renewal playbook",
    owner: "Customer Success",
    action: "Add exception path",
    risk: "High",
    status: "Needs approval",
    detail: "Renewal motions",
  },
  {
    name: "Enterprise FAQ",
    owner: "Support",
    action: "Revise retention answer",
    risk: "Medium",
    status: "Draft ready",
    detail: "Support answers",
  },
  {
    name: "CRM guidance",
    owner: "RevOps",
    action: "Update qualification note",
    risk: "Low",
    status: "Scheduled",
    detail: "Sales qualification",
  },
];

export const demoEvidence = {
  source_id: "public/pricing",
  source_name: "Public pricing page",
  before: "Enterprise includes unlimited audit-log retention.",
  after: "Enterprise includes 365-day audit-log retention.",
  evidence_hash: "0b3a67f305258cd3ffee8e504739f1185d3c0f6e29f88964f755fef8d9355b57",
  confidence: 0.99,
  snapshot_label: "Synthetic demo fixture · public/pricing",
};
