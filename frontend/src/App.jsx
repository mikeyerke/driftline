import { useEffect, useState } from "react";
import { AlertTriangle, CheckCircle2, ChevronDown, Play, X } from "lucide-react";
import Sidebar from "./components/Sidebar";
import EvidenceDiff from "./components/EvidenceDiff";
import ImpactMap from "./components/ImpactMap";
import DecisionPanel from "./components/DecisionPanel";
import ArtifactTable from "./components/ArtifactTable";
import WorkflowTimeline from "./components/WorkflowTimeline";
import ActivityLog from "./components/ActivityLog";
import { artifacts, demoEvidence } from "./data";
import { apiEnabled, approveWorkflow, startDemo, undoWorkflow } from "./api";

const delay = (milliseconds) => new Promise((resolve) => setTimeout(resolve, milliseconds));

function displayStatus(status) {
  return (status || "draft_ready").replace(/_/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export default function App() {
  const [selectedNav, setSelectedNav] = useState("Overview");
  const [localApproved, setLocalApproved] = useState(false);
  const [workflowState, setWorkflowState] = useState(null);
  const [collapsed, setCollapsed] = useState(false);
  const [selectedArtifact, setSelectedArtifact] = useState("Pricing battlecard");
  const [showEvidence, setShowEvidence] = useState(false);
  const [showActivity, setShowActivity] = useState(false);
  const [scanning, setScanning] = useState(false);
  const [scanMessage, setScanMessage] = useState("");
  const [workflowId, setWorkflowId] = useState(null);

  const approved = localApproved || workflowState?.status === "complete";
  const evidence = workflowState?.evidence || demoEvidence;
  const impacts = workflowState?.impacts?.map((impact, index) => ({
    ...impact,
    status: displayStatus(impact.status),
    detail: artifacts[index]?.detail || "Downstream guidance",
  })) || artifacts;
  const approval = workflowState?.approval
    ? {
        ...workflowState.approval,
        audit_event_id: workflowState.events?.find((event) => event.outcome === "approval_recorded")?.event_id,
      }
    : localApproved
      ? { approver: "Demo operator", timestamp: null, audit_event_id: "Local synthetic fallback" }
      : null;
  const events = workflowState?.events || [];
  const scanFailed = scanMessage.startsWith("API unavailable");

  useEffect(() => {
    if (!showEvidence) return undefined;
    const onKeyDown = (event) => {
      if (event.key === "Escape") setShowEvidence(false);
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [showEvidence]);

  const runScan = async () => {
    setScanMessage("");
    setScanning(true);
    setLocalApproved(false);
    setShowActivity(false);
    try {
      if (!apiEnabled) throw new Error("API disabled");
      const [state] = await Promise.all([startDemo(), delay(700)]);
      setWorkflowState(state);
      setWorkflowId(state.workflow_id);
      setScanMessage("Scan complete · 1 verified change");
    } catch {
      await delay(700);
      setWorkflowState(null);
      setWorkflowId(null);
      setScanMessage("API unavailable · synthetic preview active");
    } finally {
      setScanning(false);
    }
  };

  const approve = async () => {
    if (workflowId && apiEnabled) {
      try {
        const state = await approveWorkflow(workflowId);
        setWorkflowState(state);
        setLocalApproved(false);
        setShowActivity(true);
        return;
      } catch {
        setScanMessage("API unavailable · decision was not recorded");
        return;
      }
    }
    setLocalApproved(true);
    setShowActivity(true);
  };

  const undo = async () => {
    if (workflowId && apiEnabled) {
      try {
        const state = await undoWorkflow(workflowId);
        setWorkflowState(state);
        setLocalApproved(false);
        setShowActivity(true);
        return;
      } catch {
        setScanMessage("API unavailable · decision was not changed");
        return;
      }
    }
    setLocalApproved(false);
    setShowActivity(false);
  };

  return (
    <div className="app-shell">
      <Sidebar selected={selectedNav} onSelect={setSelectedNav} />
      <main>
        <header className="topbar">
          <h1>Change operations</h1>
          <div className="topbar-actions">
            {scanMessage && <span className={`scan-message${scanFailed ? " error" : ""}`} role="status" aria-live="polite">{scanFailed ? <AlertTriangle size={15} /> : <CheckCircle2 size={15} />}{scanMessage}</span>}
            <span className="workspace-button">Synthetic workspace<ChevronDown size={15} /></span>
            <button className="primary" onClick={runScan} disabled={scanning}>
              <Play size={17} />{scanning ? "Scanning…" : "Run scan"}
            </button>
          </div>
        </header>

        <div className="content">
          {selectedNav !== "Overview" && (
            <div className="view-notice">The {selectedNav} view is represented in this demo through the Overview workflow. Select Overview to return.</div>
          )}
          <section className="incident-header">
            <span className="incident-icon"><AlertTriangle size={30} /></span>
            <div className="incident-title">
              <h2>Enterprise plan packaging changed</h2>
              <div className="metadata">
                <span><strong>Source</strong>{evidence.source_name}</span>
                <i /><span><strong>Detected</strong>{workflowState ? "Just now" : "Synthetic fixture"}</span><i />
                <span><strong>Confidence</strong><CheckCircle2 className="verified" size={15} />Verified</span><i />
                <span><strong>Severity</strong><b className="risk-dot high-dot" />High</span>
              </div>
            </div>
            <button className="secondary incident-details" onClick={() => setShowEvidence(true)}>View incident evidence<ChevronDown size={16} /></button>
          </section>

          <div className="dashboard-grid">
            <div className="main-column">
              <div className="upper-grid">
                <EvidenceDiff collapsed={collapsed} onToggle={() => setCollapsed(!collapsed)} evidence={evidence} />
                <ImpactMap items={impacts} approved={approved} sourceName={evidence.source_name} />
              </div>
              <ArtifactTable items={impacts} onSelect={setSelectedArtifact} selected={selectedArtifact} />
            </div>
            <DecisionPanel approved={approved} approval={approval} onApprove={approve} onUndo={undo} onEvidence={() => setShowEvidence(true)} />
          </div>

          <WorkflowTimeline approved={approved} />
          {showActivity && <ActivityLog events={events} onClose={() => setShowActivity(false)} />}
          <footer className="demo-footer"><span>ⓘ Synthetic demo data. Not connected to live systems.</span><span>Approval gating is on for high-risk changes.</span></footer>
        </div>
      </main>

      {showEvidence && (
        <div className="modal-backdrop" role="presentation" onMouseDown={() => setShowEvidence(false)}>
          <section className="modal" role="dialog" aria-modal="true" aria-labelledby="evidence-title" onMouseDown={(event) => event.stopPropagation()}>
            <header>
              <div><h2 id="evidence-title">Source evidence</h2><p>SHA-256 snapshot verified</p></div>
              <button className="icon-button" aria-label="Close evidence" onClick={() => setShowEvidence(false)}><X size={20} /></button>
            </header>
            <div className="modal-source"><strong>{evidence.source_name}</strong><span>{evidence.source_id}</span></div>
            <EvidenceDiff collapsed={false} evidence={evidence} showToggle={false} />
            <div className="hash"><strong>Evidence hash</strong><code>{evidence.evidence_hash}</code></div>
            <footer><button className="secondary" onClick={() => setShowEvidence(false)}>Close</button></footer>
          </section>
        </div>
      )}
    </div>
  );
}
