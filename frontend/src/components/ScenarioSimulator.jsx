import { useEffect, useState } from "react";
import { ArrowRight, GitBranch, LoaderCircle } from "lucide-react";
import { getWorkflowScenarios } from "../api";

export default function ScenarioSimulator({ workflowId }) {
  const [payload, setPayload] = useState(null);
  const [selected, setSelected] = useState("approve");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!workflowId) return undefined;
    let active = true;
    setLoading(true);
    getWorkflowScenarios(workflowId)
      .then((value) => active && setPayload(value))
      .catch((requestError) => active && setError(requestError.message || "Scenario preview unavailable"))
      .finally(() => active && setLoading(false));
    return () => { active = false; };
  }, [workflowId]);

  if (!workflowId) return null;
  const scenario = payload?.scenarios?.find((item) => item.id === selected);
  return (
    <section className="panel scenario-panel" aria-labelledby="scenario-title">
      <header className="panel-header"><div><h2 id="scenario-title"><GitBranch size={17} />Compare response plans</h2><span className="live-label">Preview only</span></div><span className="muted">Compare before approval</span></header>
      {loading && <p className="multimodal-empty"><LoaderCircle size={15} className="spin" />Comparing possible outcomes…</p>}
      {error && <p className="trace-error" role="alert">{error}</p>}
      {payload && <><div className="scenario-tabs">{payload.scenarios.map((item) => <button className={item.id === selected ? "scenario-tab active" : "scenario-tab"} type="button" key={item.id} onClick={() => setSelected(item.id)}>{item.label}</button>)}</div>{scenario && <><p className="scenario-description">{scenario.description}</p><div className="scenario-summary"><span><strong>{scenario.summary.artifact_count}</strong> surfaces</span><span><strong>{scenario.summary.deferred_count}</strong> deferred</span><span><strong>{scenario.summary.jira_actions}</strong> Jira previews</span><span><strong>0</strong> external writes</span></div><div className="scenario-list">{scenario.artifacts.map((item) => <div className="scenario-row" key={item.artifact}><span><strong>{item.artifact}</strong><small>{item.owner} · {item.risk} risk</small></span><span className="scenario-outcome">{item.outcome.replaceAll("_", " ")}<ArrowRight size={13} /><small>{item.jira.status.replaceAll("_", " ")}</small></span></div>)}</div><small className="scenario-note">Preview is deterministic and evidence-bound. It does not approve, create, or reverse Jira issues.</small></>}</>}
    </section>
  );
}
