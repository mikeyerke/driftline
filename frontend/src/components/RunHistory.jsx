import { Activity, CheckCircle2, Clock3, RefreshCw, RotateCcw, ShieldAlert, XCircle } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import useNearViewport from "../hooks/useNearViewport";

const statusLabel = (status) => (status || "queued").replace(/_/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());

function StatusIcon({ status }) {
  if (status === "complete") return <CheckCircle2 size={15} />;
  if (status === "failed") return <XCircle size={15} />;
  if (status === "needs_approval") return <ShieldAlert size={15} />;
  if (status === "running") return <Activity size={15} />;
  return <Clock3 size={15} />;
}

export default function RunHistory({ jobs, loading, publicMode = false, canRetry = false, onRetry, onOpen, onVisible }) {
  const [panelRef, nearViewport] = useNearViewport();
  const visibleNotifiedRef = useRef(false);
  const [retryingJobId, setRetryingJobId] = useState(null);
  const [openingJobId, setOpeningJobId] = useState(null);

  useEffect(() => {
    if (nearViewport && !visibleNotifiedRef.current) {
      visibleNotifiedRef.current = true;
      onVisible?.();
    }
  }, [nearViewport, onVisible]);
  const visibleJobs = publicMode ? jobs.slice(0, 3) : jobs;
  const hiddenCount = Math.max(0, jobs.length - visibleJobs.length);

  const handleRetry = async (jobId) => {
    setRetryingJobId(jobId);
    try {
      await onRetry?.(jobId);
    } finally {
      setRetryingJobId(null);
    }
  };

  const handleOpen = async (job) => {
    if (!onOpen || openingJobId) return;
    setOpeningJobId(job.job_id);
    try {
      await onOpen(job);
    } finally {
      setOpeningJobId(null);
    }
  };

  return (
    <section ref={panelRef} className="panel run-history" id="history-section">
      <header className="panel-header">
        <div><h2>Run history</h2><span className="live-label">{publicMode ? "Public lane" : "Durable activity"}</span></div>
        <span className="muted">{publicMode ? "Latest tenantless runs · signed history stays scoped" : "Cloud Tasks + Firestore"}</span>
      </header>
      {!nearViewport && <p className="empty-state">Latest durable runs load when this panel enters view.</p>}
      {nearViewport && loading && <p className="empty-state">Loading the latest durable runs…</p>}
      {nearViewport && !loading && !jobs.length && <p className="empty-state">No runs yet. Start a scan to create the first durable record.</p>}
      {nearViewport && !loading && jobs.length > 0 && (
        <div className="run-history-list">
          {visibleJobs.map((job) => {
            const status = job.status || "queued";
            return (
              <div className="run-history-row" key={job.job_id}>
                <span className={`run-status ${status}`}><StatusIcon status={status} />{statusLabel(status)}</span>
                <span className="run-kind"><strong>{job.run_mode === "monitor" ? "Historical monitor" : "Change scan"}</strong><small>{job.source_id || "public/pricing"}</small></span>
                <span className="run-time">{job.created_at ? new Date(job.created_at).toLocaleString() : "—"}</span>
                <span className="run-result">
                  <span className="run-result-copy">{job.public_summary || job.response || (job.workflow_id ? "Workflow created · awaiting decision" : "Awaiting result")}</span>
                  {job.workflow_id && <button className="secondary compact run-open" type="button" disabled={openingJobId !== null} onClick={() => handleOpen(job)}>{openingJobId === job.job_id ? "Opening…" : "Open run"}</button>}
                </span>
                {job.workflow_id && <span className="run-workflow"><RotateCcw size={13} /> workflow linked</span>}
                {canRetry && status === "failed" && <button className="secondary compact run-retry" type="button" disabled={retryingJobId === job.job_id} onClick={() => handleRetry(job.job_id)}><RefreshCw size={13} />{retryingJobId === job.job_id ? "Retrying…" : "Retry"}</button>}
              </div>
            );
          })}
          {hiddenCount > 0 && <p className="run-history-note">Showing the latest {visibleJobs.length} public runs. {hiddenCount} older tenantless records remain available to the deployment audit; signed operators see their own tenant history.</p>}
        </div>
      )}
    </section>
  );
}
