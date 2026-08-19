import { Activity, CheckCircle2, Clock3, RotateCcw, ShieldAlert, XCircle } from "lucide-react";

const statusLabel = (status) => (status || "queued").replace(/_/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());

function StatusIcon({ status }) {
  if (status === "complete") return <CheckCircle2 size={15} />;
  if (status === "failed") return <XCircle size={15} />;
  if (status === "needs_approval") return <ShieldAlert size={15} />;
  if (status === "running") return <Activity size={15} />;
  return <Clock3 size={15} />;
}

export default function RunHistory({ jobs, loading }) {
  return (
    <section className="panel run-history" id="history-section">
      <header className="panel-header">
        <div><h2>Run history</h2><span className="live-label">Durable activity</span></div>
        <span className="muted">Cloud Tasks + Firestore</span>
      </header>
      {loading && <p className="empty-state">Loading the latest durable runs…</p>}
      {!loading && !jobs.length && <p className="empty-state">No runs yet. Start a scan to create the first durable record.</p>}
      {!loading && jobs.length > 0 && (
        <div className="run-history-list">
          {jobs.map((job) => {
            const status = job.status || "queued";
            return (
              <div className="run-history-row" key={job.job_id}>
                <span className={`run-status ${status}`}><StatusIcon status={status} />{statusLabel(status)}</span>
                <span className="run-kind">{job.run_mode === "monitor" ? "Historical monitor" : "Change scan"}</span>
                <span className="run-time">{job.created_at ? new Date(job.created_at).toLocaleString() : "—"}</span>
                <span className="run-result">{job.response || (job.workflow_id ? "Workflow created · awaiting decision" : "Awaiting result")}</span>
                {job.workflow_id && <span className="run-workflow"><RotateCcw size={13} /> workflow linked</span>}
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}
