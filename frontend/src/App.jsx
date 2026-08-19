import { useEffect, useRef, useState } from "react";
import { AlertTriangle, CheckCircle2, ChevronDown, Play, X } from "lucide-react";
import Sidebar from "./components/Sidebar";
import EvidenceDiff from "./components/EvidenceDiff";
import ImpactMap from "./components/ImpactMap";
import DecisionPanel from "./components/DecisionPanel";
import ArtifactTable from "./components/ArtifactTable";
import ArtifactDetail from "./components/ArtifactDetail";
import WorkflowTimeline from "./components/WorkflowTimeline";
import ActivityLog from "./components/ActivityLog";
import AgentTrace from "./components/AgentTrace";
import SourcePanel from "./components/SourcePanel";
import TrustPanel from "./components/TrustPanel";
import { artifacts, demoEvidence } from "./data";
import { apiEnabled, approveWorkflow, getJob, getSources, listJobs, packetUrl, startDemoJob, undoWorkflow } from "./api";
import ActionItems from "./components/ActionItems";
import RunHistory from "./components/RunHistory";
import IntegrationPanel from "./components/IntegrationPanel";
import ChangeTimeline from "./components/ChangeTimeline";

const delay = (milliseconds) => new Promise((resolve) => setTimeout(resolve, milliseconds));

function displayStatus(status) {
  return (status || "draft_ready").replace(/_/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function defaultDecisionsFor(state) {
  return (state?.impacts || []).reduce((result, item) => {
    result[item.name] = item.name === "CRM guidance"
      ? "queued"
      : item.risk === "high" ? "packet" : "owner_review";
    return result;
  }, {});
}

const initialDecisions = {
  "Pricing battlecard": "packet",
  "Renewal playbook": "packet",
  "Enterprise FAQ": "owner_review",
  "CRM guidance": "queued",
};

export default function App() {
  const [selectedNav, setSelectedNav] = useState("Overview");
  const [workflowState, setWorkflowState] = useState(null);
  const [selectedArtifact, setSelectedArtifact] = useState("Pricing battlecard");
  const [evidenceCollapsed, setEvidenceCollapsed] = useState(false);
  const [artifactDecisions, setArtifactDecisions] = useState(initialDecisions);
  const [showEvidence, setShowEvidence] = useState(false);
  const [scanning, setScanning] = useState(false);
  const [decisionBusy, setDecisionBusy] = useState(false);
  const [scanMessage, setScanMessage] = useState("");
  const [workflowId, setWorkflowId] = useState(null);
  const [job, setJob] = useState(null);
  const [recentJobs, setRecentJobs] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [sources, setSources] = useState([]);
  const [selectedSource, setSelectedSource] = useState("public/pricing");
  const modalRef = useRef(null);
  const modalTriggerRef = useRef(null);

  const approved = workflowState?.status === "complete";
  const liveWorkflow = Boolean(workflowState?.workflow_id && workflowId);
  const evidence = workflowState?.evidence || demoEvidence;
  const impacts = workflowState?.impacts?.map((impact, index) => ({
    ...impact,
    status: displayStatus(impact.status),
    detail: impact.detail || artifacts[index]?.detail || "Downstream guidance",
    proposed: impact.proposed || artifacts[index]?.proposed || "Evidence-linked update",
    before: evidence.before,
    evidence_hash: impact.evidence_hash || evidence.evidence_hash,
  })) || artifacts.map((item) => ({ ...item, before: evidence.before }));
  const selectedItem = impacts.find((item) => item.name === selectedArtifact) || impacts[0];
  const approval = workflowState?.approval
    ? {
        ...workflowState.approval,
        audit_event_id: workflowState.events?.find((event) => event.outcome === "approval_recorded")?.event_id,
      }
    : null;
  const events = workflowState?.events || [];
  const scanFailed = scanMessage.startsWith("Unable");
  const packetHref = workflowId ? packetUrl(workflowId) : null;

  const refreshHistory = async () => {
    try {
      const payload = await listJobs();
      setRecentJobs(payload.jobs || []);
    } catch {
      setRecentJobs([]);
    } finally {
      setHistoryLoading(false);
    }
  };

  useEffect(() => {
    refreshHistory();
    getSources().then((payload) => setSources(payload.sources || [])).catch(() => setSources([]));
  }, []);

  const selectNav = (label) => {
    setSelectedNav(label);
    const targetId = `${label.toLowerCase()}-section`;
    window.requestAnimationFrame(() => document.getElementById(targetId)?.scrollIntoView({ behavior: "smooth", block: "start" }));
  };

  useEffect(() => {
    if (!showEvidence) return undefined;
    modalTriggerRef.current = document.activeElement;
    window.requestAnimationFrame(() => modalRef.current?.focus());
    const onKeyDown = (event) => {
      if (event.key === "Escape") setShowEvidence(false);
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [showEvidence]);

  useEffect(() => {
    if (!showEvidence && modalTriggerRef.current) {
      modalTriggerRef.current.focus?.();
      modalTriggerRef.current = null;
    }
  }, [showEvidence]);

  const runScan = async () => {
    setScanMessage("");
    setScanning(true);
    setWorkflowState(null);
    setWorkflowId(null);
    setJob(null);
    try {
      if (!apiEnabled) throw new Error("API disabled");
      const queued = await startDemoJob(selectedSource);
      setJob(queued);
      refreshHistory();
      setScanMessage("Agent queued · waiting for a durable run");
      for (let attempt = 0; attempt < 80; attempt += 1) {
        await delay(700);
        const current = await getJob(queued.job_id);
        setJob(current);
        if (current.status === "failed") throw new Error(current.error || "Agent job failed");
        if (["needs_approval", "complete"].includes(current.status) && current.workflow) {
          setWorkflowState(current.workflow);
          setWorkflowId(current.workflow.workflow_id);
          setArtifactDecisions(current.workflow.approval?.artifact_decisions || defaultDecisionsFor(current.workflow));
          setScanMessage("Scan complete · evidence verified · approval gate active");
          refreshHistory();
          return;
        }
        setScanMessage(current.status === "running" ? "Agent running · verifying source and mapping impact" : "Agent queued · waiting for a durable run");
      }
      throw new Error("The agent job timed out");
    } catch (error) {
      setScanMessage(`Unable to start the live scan · ${error.message || "retry the request"}`);
      setJob((current) => current ? { ...current, status: "failed", error: error.message } : current);
    } finally {
      setScanning(false);
    }
  };

  const approve = async () => {
    if (!workflowId || !liveWorkflow || decisionBusy) return;
    setDecisionBusy(true);
    try {
      const decision = workflowState?.impact_graph?.summary?.category?.startsWith("Competitor")
        ? "approve_competitive_response"
        : "grandfather_existing_customers";
      const state = await approveWorkflow(workflowId, artifactDecisions, decision);
      setWorkflowState(state);
      setJob((current) => current ? { ...current, status: state.status, workflow: state } : current);
      setScanMessage("Action plan recorded · sandbox packet created");
      refreshHistory();
    } catch (error) {
      setScanMessage(`Unable to record the decision · ${error.message || "retry the request"}`);
    } finally {
      setDecisionBusy(false);
    }
  };

  const reopen = async () => {
    if (!workflowId || !liveWorkflow || decisionBusy) return;
    setDecisionBusy(true);
    try {
      const state = await undoWorkflow(workflowId);
      setWorkflowState(state);
      setJob((current) => current ? { ...current, status: state.status, workflow: state } : current);
      setScanMessage("Decision reopened · no external systems were changed");
      refreshHistory();
    } catch (error) {
      setScanMessage(`Unable to reopen the decision · ${error.message || "retry the request"}`);
    } finally {
      setDecisionBusy(false);
    }
  };

  const updateArtifactDecision = (name, decision) => {
    setArtifactDecisions((current) => ({ ...current, [name]: decision }));
  };

  return (
    <div className="app-shell">
      <a className="skip-link" href="#main-content">Skip to main content</a>
      <Sidebar selected={selectedNav} onSelect={selectNav} />
      <main id="main-content">
        <header className="topbar">
          <h1>Promise drift operations</h1>
          <div className="topbar-actions">
            {scanMessage && <span className={`scan-message${scanFailed ? " error" : ""}`} role="status" aria-live="polite">{scanFailed ? <AlertTriangle size={15} /> : <CheckCircle2 size={15} />}{scanMessage}</span>}
            <span className="workspace-button">Evaluation sandbox<ChevronDown size={15} /></span>
            <span className="run-hint">Live allowlisted monitor · handoffs staged, no external writes</span>
            <button className="primary" onClick={runScan} disabled={scanning} type="button" aria-label="Run the live allowlisted monitor">
              <Play size={17} />{scanning ? "Running…" : "Run scan"}
            </button>
          </div>
        </header>

        <div className="content">
        <div className="workspace-banner"><strong>Evaluation sandbox</strong><span>Own + competitor public signals · offering impact graph · deterministic human gate</span><span className="banner-status">{liveWorkflow ? "Live workflow" : "Preview only"}</span></div>
          <section id="overview-section" className="overview-section">
            <p className="product-orientation">Driftline monitors public promises, maps downstream work, and prepares evidence-bound packets for human approval.</p>
            <section className="incident-header">
              <span className="incident-icon"><AlertTriangle size={30} /></span>
              <div className="incident-title">
              <h2>{workflowState?.title || (selectedSource === "competitor/pricing" ? "Competitor pricing moved" : selectedSource === "competitor/offerings" ? "Competitor offering changed" : selectedSource === "competitor/blog" ? "Competitor product narrative changed" : "Enterprise plan packaging changed")}</h2>
                <div className="metadata">
                  <span><strong>Source</strong>{evidence.source_name}</span><i /><span><strong>Detected</strong>{workflowState ? "Just now" : "Preview"}</span><i />
                  <span><strong>Confidence</strong><CheckCircle2 className="verified" size={15} />Verified</span><i /><span><strong>Severity</strong><b className="risk-dot high-dot" />High</span>
                </div>
              </div>
              <button className="secondary incident-details" onClick={() => setShowEvidence(true)} type="button">View source evidence<ChevronDown size={16} /></button>
            </section>

            <section className="change-brief" aria-label="Change decision brief">
              <div><span>Why this matters</span><strong>One source change can create conflicting promises across the business.</strong><p>Driftline turns the verified sentence-level change into owner-ready work, with evidence attached before anything can be approved.</p></div>
              <div><span>Decision scope</span><strong>{workflowState?.impact_graph?.summary?.artifact_count || 4} downstream surfaces</strong><p>Products, pricing, comparison maps, enablement, and customer guidance stay coordinated.</p></div>
              <div><span>Guardrail</span><strong>Human approval required</strong><p>High-risk changes stop here. The agent cannot approve its own action.</p></div>
            </section>

            <div className="dashboard-grid">
              <div className="main-column">
                <div className="upper-grid">
                  <EvidenceDiff collapsed={evidenceCollapsed} onToggle={() => setEvidenceCollapsed((current) => !current)} evidence={evidence} />
                  <ImpactMap items={impacts} graph={workflowState?.impact_graph} approved={approved} sourceName={evidence.source_name} />
                </div>
                <ArtifactTable items={impacts} onSelect={setSelectedArtifact} selected={selectedArtifact} />
                <ArtifactDetail item={selectedItem} live={liveWorkflow && !approved} decision={artifactDecisions[selectedItem?.name]} onDecisionChange={updateArtifactDecision} packetUrl={approved ? packetHref : null} />
              </div>
              <aside id="approvals-section">
                <DecisionPanel approved={approved} approval={approval} artifactDecisions={artifactDecisions} actionRecord={workflowState?.action_record} onApprove={approve} onUndo={reopen} onEvidence={() => setShowEvidence(true)} isLive={liveWorkflow && workflowState?.status === "needs_approval"} busy={decisionBusy} packetHref={packetHref} sourceCategory={workflowState?.impact_graph?.summary?.category} />
              </aside>
            </div>
            {approved && <ActionItems workflowId={workflowId} items={workflowState.action_items} onChange={(state) => { setWorkflowState(state); setJob((current) => current ? { ...current, status: state.status, workflow: state } : current); refreshHistory(); }} />}
            <IntegrationPanel targets={workflowState?.integration_targets} approved={approved} />
            <ChangeTimeline state={workflowState} />
            <WorkflowTimeline state={workflowState} />
          </section>

          <SourcePanel evidence={evidence} dataMode={workflowState?.data_mode || demoEvidence.data_mode} sources={sources} selectedSource={selectedSource} onSourceChange={setSelectedSource} />
          <RunHistory jobs={recentJobs} loading={historyLoading} />
          <AgentTrace job={job} />
          <section id="activity-section"><ActivityLog events={events} /></section>
          <TrustPanel />
          <footer className="demo-footer"><span>ⓘ Synthetic replay remains available when the public source cannot be fetched.</span><span>Approval gating is deterministic; external writes stay disabled until a connector is configured.</span></footer>
        </div>
      </main>

      {showEvidence && (
        <div className="modal-backdrop" role="presentation" onMouseDown={() => setShowEvidence(false)}>
          <section className="modal" role="dialog" aria-modal="true" aria-labelledby="evidence-title" tabIndex={-1} ref={modalRef} onMouseDown={(event) => event.stopPropagation()}>
            <header>
              <div><h2 id="evidence-title">Source evidence</h2><p>Hash-bound snapshot verification</p></div>
              <button className="icon-button" aria-label="Close source evidence" onClick={() => setShowEvidence(false)} type="button"><X size={20} /></button>
            </header>
            <div className="modal-source"><strong>{evidence.source_name}</strong><span>{evidence.source_id}</span></div>
            <EvidenceDiff collapsed={false} evidence={evidence} showToggle={false} />
            <div className="hash"><strong>Evidence hash</strong><code>{evidence.evidence_hash}</code></div>
            {evidence.source_url && <a className="source-link modal-link" href={evidence.source_url} target="_blank" rel="noreferrer">Open source snapshot</a>}
            <footer><button className="secondary" onClick={() => setShowEvidence(false)} type="button">Close evidence</button></footer>
          </section>
        </div>
      )}
    </div>
  );
}
