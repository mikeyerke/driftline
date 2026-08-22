import { Activity, CheckCircle2, History, ShieldCheck, TrendingDown, TrendingUp, XCircle } from "lucide-react";
import { useEffect, useState } from "react";
import { getEvaluationHistory, getLatestEvaluation, runEvaluation } from "../api";
import useNearViewport from "../hooks/useNearViewport";

const percent = (value) => value === null || value === undefined ? "—" : `${Math.round(Number(value) * 100)}%`;
const trendLabel = (trend) => {
  if (!trend || trend.status === "first_run") return "First recorded run";
  if (trend.status === "improved") return "Improving vs prior run";
  if (trend.status === "regressed") return "Regression detected";
  return "Stable vs prior run";
};

const historyDate = (value) => {
  if (!value) return "Recorded";
  const date = new Date(value);
  return Number.isNaN(date.valueOf())
    ? "Recorded"
    : date.toLocaleDateString([], { month: "short", day: "numeric" });
};

const shortRelease = (value) => {
  if (!value || value === "unknown") return "unbound";
  return `${value.slice(0, 7)}…`;
};

export default function TraceEvalPanel({ workflowId = null }) {
  const [panelRef, nearViewport] = useNearViewport();
  const [evaluation, setEvaluation] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  const refresh = async (evaluateWorkflow = false) => {
    setLoading(true);
    setMessage("");
    try {
      const payload = evaluateWorkflow
        ? await runEvaluation(workflowId)
        : await getLatestEvaluation();
      setEvaluation(payload.evaluation || null);
    } catch (error) {
      setMessage(error.message || "Quality gate is unavailable");
    }
    try {
      const trajectory = await getEvaluationHistory();
      setHistory(trajectory.evaluations || []);
    } catch {
      // The latest report remains useful when a history read is temporarily
      // unavailable; keep the failure visible without replacing the report.
      setHistory([]);
      setMessage((current) => current || "Quality trajectory is temporarily unavailable");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!nearViewport) return undefined;
    refresh(Boolean(workflowId));
    return undefined;
  }, [nearViewport, workflowId]);

  const cases = evaluation?.cases || [];
  const passed = evaluation?.gate_status === "pass";
  const trend = evaluation?.trend;
  const trajectory = [...history].reverse();

  return (
    <section ref={panelRef} className="panel trace-eval-panel" aria-labelledby="trace-eval-title">
      <header className="panel-header">
        <div><h2 id="trace-eval-title"><ShieldCheck size={17} />Trace-to-eval quality gate</h2><span className={`live-label ${passed ? "public" : evaluation ? "failed" : "synthetic"}`}>{evaluation ? (passed ? "Gate passed" : "Gate blocked") : "Not run"}</span></div>
        <span className="muted">Safety + usefulness over time</span>
      </header>
      <p className="trace-eval-scope">Deterministic checks score the bounded agent trace, not customer ROI. Raw prompts, source bodies, and credentials never enter the evaluation ledger.</p>
      {!nearViewport && <p className="multimodal-empty">Quality evidence loads when this panel enters view.</p>}
      {nearViewport && loading && <p className="multimodal-empty"><Activity size={15} className="spin" />Running the quality gate…</p>}
      {nearViewport && !loading && evaluation && <>
        <div className="trace-eval-summary">
          <div className={passed ? "pass" : "fail"}><strong>{percent(evaluation.overall_score)}</strong><small>overall gate score</small></div>
          <div><strong>{percent(evaluation.safety_score)}</strong><small>safety score</small></div>
          <div><strong>{percent(evaluation.usefulness_score)}</strong><small>usefulness score</small></div>
          <div><strong>{evaluation.passed_case_count}/{evaluation.case_count}</strong><small>checks passed</small></div>
        </div>
        <div className={`trace-eval-trend ${trend?.status === "regressed" ? "regressed" : ""}`}>
          {trend?.status === "regressed" ? <TrendingDown size={14} /> : <TrendingUp size={14} />}
          <strong>{trendLabel(trend)}</strong>
          <span>{evaluation.release_sha === "unknown" ? "Local / unpinned release" : `Release ${evaluation.release_sha.slice(0, 12)}…`}</span>
        </div>
        {trajectory.length > 0 && <div className="trace-eval-history" aria-label="Trace evaluation quality trajectory">
          <div className="trace-eval-history-heading"><span><History size={14} />Quality trajectory</span><small>Oldest → newest · {trajectory.length} recorded run{trajectory.length === 1 ? "" : "s"}</small></div>
          <ol className="trace-eval-history-list">
            {trajectory.map((point) => {
              const score = Math.max(0, Math.min(1, Number(point.overall_score) || 0));
              const pointPassed = point.gate_status === "pass";
              return <li className={`trace-eval-history-item ${pointPassed ? "pass" : "fail"}`} key={point.evaluation_id} title={`${pointPassed ? "Passed" : "Blocked"} · ${percent(point.overall_score)} overall · ${shortRelease(point.release_sha)}`}>
                <span className="trace-eval-history-bar"><i style={{ height: `${Math.max(8, Math.round(score * 100))}%` }} /></span>
                <strong>{percent(point.overall_score)}</strong>
                <small>{historyDate(point.evaluated_at)}</small>
                <code>{shortRelease(point.release_sha)}</code>
              </li>;
            })}
          </ol>
          <p className="trace-eval-history-note">Each point is a redacted deterministic evaluation report. A failed or regressed point blocks the release; the trajectory is evaluation telemetry, not customer ROI.</p>
        </div>}
        <ul className="trace-eval-cases">
          {cases.map((item) => <li key={item.case_id} className={item.status === "pass" ? "pass" : "fail"}>
            {item.status === "pass" ? <CheckCircle2 size={14} /> : <XCircle size={14} />}
            <span><strong>{item.case_id.replaceAll("_", " ")}</strong><small>{item.reason}</small></span>
          </li>)}
        </ul>
        <p className="trace-eval-note">Suite {evaluation.suite_version} · {evaluation.execution_mode} · {evaluation.model} · data mode: {evaluation.trace_data_mode || "unknown"}. This is evaluation telemetry, not a customer outcome or willingness-to-pay claim.</p>
      </>}
      {nearViewport && !loading && !evaluation && <div className="trace-eval-empty"><p className="empty-state">No persisted gate result yet.</p><button className="secondary compact" type="button" onClick={() => refresh(false)}>Run deterministic gate</button></div>}
      {message && <p className="trace-eval-message" role="status">{message}</p>}
    </section>
  );
}
