import { CheckCircle2, Clock3, Cpu, Wrench } from "lucide-react";

const label = (value) => (value || "—").replace(/_/g, " ");

export default function AgentTrace({ job }) {
  const trace = job?.workflow?.agent_trace;
  const calls = job?.tool_calls || trace?.tool_calls?.map((item) => item.name) || [];
  const analysis = trace?.structured_analysis;
  const running = job?.status === "queued" || job?.status === "running";
  const failed = job?.status === "failed";

  return (
    <section className="panel agent-trace" id="workflows-section">
      <header className="panel-header">
        <div>
          <h2>Agent run</h2>
          <span className={`live-label ${running ? "running" : failed ? "failed" : ""}`}>
            {running ? "Running" : failed ? "Failed" : job ? "Recorded" : "Not started"}
          </span>
        </div>
        <span className="muted">Google ADK execution trace</span>
      </header>
      {!job && <p className="empty-state">Run a scan to see the live model and allowlisted tool path.</p>}
      {job && (
        <div className="trace-body">
          <div className="trace-summary">
            <span><Cpu size={15} /><strong>Model</strong>{job.model || trace?.model || "Waiting for model"}</span>
            <span><Wrench size={15} /><strong>Tools</strong>{calls.length ? calls.join(", ") : "Waiting for tool calls"}</span>
            <span><Clock3 size={15} /><strong>Events</strong>{job.event_count || trace?.event_count || "—"}</span>
          </div>
          {analysis && (
            <div className="analysis-proof" aria-label="Structured impact analysis">
              <div className="analysis-proof-header">
                <strong>Impact analysis</strong>
                <span className={`live-label ${analysis.mode === "gemini_structured" ? "public" : "synthetic"}`}>
                  {label(analysis.mode)}
                </span>
              </div>
              {analysis.summary && <p>{analysis.summary}</p>}
              {analysis.rationale && <small>{analysis.rationale}</small>}
              {analysis.artifact_count && <span className="analysis-count">{analysis.artifact_count} evidence-bound artifacts</span>}
              {analysis.reason && <small className="analysis-fallback">{analysis.reason}</small>}
            </div>
          )}
          <div className="trace-path" aria-label="Agent execution path">
            <div className={job.status === "queued" ? "trace-step current" : "trace-step complete"}><span>1</span><strong>Queued</strong><small>Durable job</small></div>
            <div className={running ? "trace-step current" : "trace-step complete"}><span>2</span><strong>ADK turn</strong><small>{job.execution_mode || "Google ADK"}</small></div>
            <div className={job.workflow_id ? "trace-step complete" : "trace-step current"}><span>3</span><strong>Workflow</strong><small>{job.workflow_id ? "Firestore state" : "Awaiting state"}</small></div>
            <div className={job.workflow?.status === "needs_approval" ? "trace-step current" : job.workflow ? "trace-step complete" : "trace-step"}><span>4</span><strong>Policy gate</strong><small>{job.workflow?.status === "needs_approval" ? "Human decision" : job.workflow?.status === "complete" ? "Decision recorded" : "Awaiting run"}</small></div>
          </div>
          {(job.public_summary || job.response) && <p className="trace-response"><CheckCircle2 size={15} />{job.public_summary || job.response}</p>}
          {job.error && <p className="trace-error" role="alert">{job.error}</p>}
        </div>
      )}
    </section>
  );
}
