import { useEffect, useRef, useState } from "react";
import { AlertTriangle, CheckCircle2, ChevronDown, ShieldCheck, X } from "lucide-react";
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
import { artifacts, demoEvidence, demoEvidenceBySource } from "./data";
import { apiEnabled, approveWorkflow, dismissWorkflow, downloadPacket, getJob, getMonitorRegistry, getOperatorSession, getSources, listJobs, packetUrl, reconcileWorkflow, retryJob, startDemoJob, subscribeOperatorSession, undoWorkflow } from "./api";
import ActionItems from "./components/ActionItems";
import RunHistory from "./components/RunHistory";
import IntegrationPanel from "./components/IntegrationPanel";
import ChangeTimeline from "./components/ChangeTimeline";
import ScenarioSimulator from "./components/ScenarioSimulator";
import ChangeGenomePanel from "./components/ChangeGenomePanel";
import ChangeCardPanel from "./components/ChangeCardPanel";
import ValueProofPanel from "./components/ValueProofPanel";
import PilotMeasurementPanel from "./components/PilotMeasurementPanel";
import OperatorAccess from "./components/OperatorAccess";
import SalesforceConnectorPanel from "./components/SalesforceConnectorPanel";
import TraceEvalPanel from "./components/TraceEvalPanel";
import ReleaseProof from "./components/ReleaseProof";
import UtilityNextStep from "./components/UtilityNextStep";
import JudgeJourney from "./components/JudgeJourney";

const delay = (milliseconds) => new Promise((resolve) => setTimeout(resolve, milliseconds));

function displayStatus(status) {
  return (status || "draft_ready").replace(/_/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function artifactRowId(name) {
  return `artifact-row-${String(name || "artifact").replace(/[^a-z0-9]+/gi, "-").toLowerCase()}`;
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
  "Comparison map": "packet",
  "Pricing battlecard": "owner_review",
  "Deal desk guidance": "packet",
  "Executive weekly brief": "queued",
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
  const [sourceHealth, setSourceHealth] = useState([]);
  const [sourceHealthState, setSourceHealthState] = useState("loading");
  const [sourceHistoryRefreshKey, setSourceHistoryRefreshKey] = useState(0);
  const [selectedSource, setSelectedSource] = useState("competitor/pricing");
  const [operatorSession, setOperatorSession] = useState(getOperatorSession());
  const [judgeMode, setJudgeMode] = useState(true);
  const modalRef = useRef(null);
  const modalTriggerRef = useRef(null);
  const navScrollTimersRef = useRef([]);
  const lastTenantRef = useRef(operatorSession.tenantId || null);
  const sessionKeyRef = useRef(`${operatorSession.tenantId || "public"}:${operatorSession.identityToken ? "signed" : "anonymous"}`);
  const sessionEpochRef = useRef(0);
  const historyRequestRef = useRef(0);
  const sourceHealthRequestRef = useRef(0);
  const lastGuidedStatusRef = useRef(null);

  const approved = workflowState?.status === "complete";
  const dismissed = workflowState?.status === "dismissed";
  const liveWorkflow = Boolean(workflowState?.workflow_id && workflowId);
  const previewEvidence = demoEvidenceBySource[selectedSource] || {
    source_id: selectedSource,
    source_name: selectedSource,
    before: "No snapshot captured yet.",
    after: "Run a scan to capture evidence from this registered source.",
    confidence: 0,
    snapshot_label: "Awaiting first capture",
    data_mode: "awaiting_capture",
  };
  const evidence = workflowState?.evidence || previewEvidence;
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
  const structuredAnalysis = job?.workflow?.agent_trace?.structured_analysis;
  const actionRecord = workflowState?.action_record;
  const jiraWriteOccurred = ["created", "reused", "reactivated", "reversed"].includes(actionRecord?.jira_status);
  const selectedSourceDefinition = sources.find((source) => source.source_id === selectedSource);
  const selectedSourcePaused = selectedSourceDefinition?.enabled === false;
  const refreshHistory = async (expectedEpoch = sessionEpochRef.current) => {
    const requestId = historyRequestRef.current + 1;
    historyRequestRef.current = requestId;
    try {
      const payload = await listJobs();
      // A scan, approval, and lazy in-view load can overlap. Only the newest
      // response may replace the list; otherwise an older Firestore read can
      // briefly put a just-finished run back into "Running" in the console.
      if (sessionEpochRef.current !== expectedEpoch || historyRequestRef.current !== requestId) return;
      setRecentJobs(payload.jobs || []);
    } catch {
      if (sessionEpochRef.current !== expectedEpoch || historyRequestRef.current !== requestId) return;
      setRecentJobs([]);
    } finally {
      if (sessionEpochRef.current === expectedEpoch && historyRequestRef.current === requestId) setHistoryLoading(false);
    }
  };

  const refreshSourceHealth = async (expectedEpoch = sessionEpochRef.current) => {
    const requestId = sourceHealthRequestRef.current + 1;
    sourceHealthRequestRef.current = requestId;
    if (sessionEpochRef.current === expectedEpoch) setSourceHealthState("loading");
    try {
      const payload = await getMonitorRegistry();
      if (sessionEpochRef.current !== expectedEpoch || sourceHealthRequestRef.current !== requestId) return;
      setSourceHealth(payload.sources || []);
      setSourceHealthState("ready");
    } catch {
      if (sessionEpochRef.current !== expectedEpoch || sourceHealthRequestRef.current !== requestId) return;
      setSourceHealth([]);
      setSourceHealthState("unavailable");
    }
  };

  useEffect(() => {
    const callbackEpoch = sessionEpochRef.current;
    getSources().then((payload) => {
      if (sessionEpochRef.current === callbackEpoch) setSources(payload.sources || []);
    }).catch(() => {
      if (sessionEpochRef.current === callbackEpoch) setSources([]);
    });
  }, []);

  useEffect(() => subscribeOperatorSession((next) => {
    const nextSessionKey = `${next.tenantId || "public"}:${next.identityToken ? "signed" : "anonymous"}`;
    if (sessionKeyRef.current !== nextSessionKey) {
      sessionKeyRef.current = nextSessionKey;
      sessionEpochRef.current += 1;
    }
    const callbackEpoch = sessionEpochRef.current;
    setOperatorSession(next);
    refreshHistory(callbackEpoch);
    getSources().then((payload) => {
      if (sessionEpochRef.current === callbackEpoch) setSources(payload.sources || []);
    }).catch(() => {
      if (sessionEpochRef.current === callbackEpoch) setSources([]);
    });
    refreshSourceHealth(callbackEpoch);
  }), []);

  useEffect(() => {
    const previousTenant = lastTenantRef.current;
    const nextTenant = operatorSession.tenantId || null;
    if (previousTenant !== nextTenant) {
      // Never carry a workflow across an identity boundary. This includes
      // anonymous -> signed-in (a public packet must not appear as tenant
      // work), tenant -> tenant, and signed-in -> anonymous transitions. The
      // next lane must start from its own filtered history and an explicit
      // scan.
      setWorkflowState(null);
      setWorkflowId(null);
      setJob(null);
      setArtifactDecisions(initialDecisions);
      setSelectedSource("competitor/pricing");
      setScanMessage("Tenant changed · previous workflow cleared");
    }
    lastTenantRef.current = nextTenant;
  }, [operatorSession.tenantId]);

  const selectNav = (label) => {
    setSelectedNav(label);
    const targetId = `${label.toLowerCase()}-section`;
    navScrollTimersRef.current.forEach((timer) => window.clearTimeout(timer));
    navScrollTimersRef.current = [];
    window.requestAnimationFrame(() => {
      const target = document.getElementById(targetId);
      if (!target) return;
      target.scrollIntoView({ behavior: "smooth", block: "start" });

      // Below-the-fold panels use near-viewport loading. They can mount while
      // this scroll is moving, shifting a deep target after the browser has
      // already computed its destination. Reconcile once after those panels
      // have had a chance to mount, and once more only if the document grew.
      const firstSettleTimer = window.setTimeout(() => {
        const currentTarget = document.getElementById(targetId);
        if (!currentTarget) return;
        const heightBeforeSettle = document.documentElement.scrollHeight;
        currentTarget.scrollIntoView({ behavior: "auto", block: "start" });
        const secondSettleTimer = window.setTimeout(() => {
          const finalTarget = document.getElementById(targetId);
          if (finalTarget && document.documentElement.scrollHeight !== heightBeforeSettle) {
            finalTarget.scrollIntoView({ behavior: "auto", block: "start" });
          }
        }, 350);
        navScrollTimersRef.current.push(secondSettleTimer);
      }, 750);
      navScrollTimersRef.current.push(firstSettleTimer);
    });
  };

  const handleSourceChange = (nextSource) => {
    if (!nextSource || nextSource === selectedSource) return;
    // A source selector change starts a new inspection context. Invalidate a
    // poll that may still be completing for the old source so it cannot
    // repopulate the new selection with stale evidence or impact nodes.
    sessionEpochRef.current += 1;
    setSelectedSource(nextSource);
    setWorkflowState(null);
    setWorkflowId(null);
    setJob(null);
    setArtifactDecisions(initialDecisions);
    setSelectedArtifact("Pricing battlecard");
    setScanMessage("Source changed · run a new scan to verify this change");
  };

  useEffect(() => {
    if (!showEvidence) return undefined;
    modalTriggerRef.current = document.activeElement;
    window.requestAnimationFrame(() => modalRef.current?.focus());
    const getFocusable = () => [...(modalRef.current?.querySelectorAll(
      'button:not([disabled]), a[href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])',
    ) || [])].filter((element) => element.getClientRects().length > 0);
    const onKeyDown = (event) => {
      if (event.key === "Escape") {
        event.preventDefault();
        setShowEvidence(false);
        return;
      }
      if (event.key !== "Tab") return;
      const focusable = getFocusable();
      if (!focusable.length) {
        event.preventDefault();
        modalRef.current?.focus();
        return;
      }
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      const active = document.activeElement;
      const focusOutsideModal = !modalRef.current?.contains(active);
      const shiftAtBoundary = event.shiftKey && (active === first || active === modalRef.current || focusOutsideModal);
      const forwardAtBoundary = !event.shiftKey && (active === last || focusOutsideModal);
      if (shiftAtBoundary || forwardAtBoundary) {
        event.preventDefault();
        (event.shiftKey ? last : first).focus();
      }
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

  const runScan = async (sourceId = selectedSource, requestedRunMode = null) => {
    const scanEpoch = sessionEpochRef.current;
    setScanMessage("");
    setScanning(true);
    setWorkflowState(null);
    setWorkflowId(null);
    setJob(null);
    try {
      if (!apiEnabled) throw new Error("API disabled");
      const selectedDefinition = sources.find((source) => source.source_id === sourceId);
      if (selectedDefinition?.enabled === false) {
        throw new Error("This source is paused; resume monitoring before scanning.");
      }
      const runMode = requestedRunMode
        || (operatorSession.identityToken && selectedDefinition?.mode === "public_only"
          ? "monitor"
          : null);
      const queued = await startDemoJob(sourceId, runMode);
      if (sessionEpochRef.current !== scanEpoch) return;
      setJob(queued);
      refreshHistory();
      setScanMessage(runMode === "monitor"
        ? "Monitor queued · capturing the registered public source"
        : "Agent queued · waiting for a durable run");
      // ADK + Gemini can legitimately take over a minute on a cold Cloud Run
      // instance. Keep polling well inside the server's 300-second job budget
      // instead of turning a slow-but-successful run into a false UI failure.
      for (let attempt = 0; attempt < 180; attempt += 1) {
        await delay(700);
        const current = await getJob(queued.job_id);
        if (sessionEpochRef.current !== scanEpoch) return;
        setJob(current);
        if (current.status === "failed") {
          throw new Error(current.error || (runMode === "monitor" ? "The source monitor failed after bounded retries." : "Agent job failed"));
        }
        // A source outage is a durable monitor outcome, not an agent timeout
        // and not a material business change. Surface it immediately so the
        // operator can inspect the source health card while Scheduler retries
        // on its normal cadence.
        if (
          current.status === "complete"
          && !current.workflow
          && current.source_status === "source_fetch_failed"
        ) {
          setScanMessage("Monitor unavailable · source fetch failed; Scheduler will retry");
          setSourceHistoryRefreshKey((value) => value + 1);
          await Promise.all([
            refreshHistory(scanEpoch),
            refreshSourceHealth(scanEpoch),
          ]);
          return;
        }
        // A monitor no-op is a successful, durable outcome without a
        // workflow. Exit the poller immediately so an unchanged source is
        // presented as useful signal suppression instead of timing out as a
        // false failure. The backend only emits these dispositions after the
        // append-only source comparison has completed.
        if (
          current.status === "complete"
          && !current.workflow
          && ["unchanged", "baseline_established"].includes(current.source_status)
        ) {
          setScanMessage(
            current.source_status === "unchanged"
              ? "Monitor complete · no material change; prior baseline retained"
              : "Monitor complete · baseline established; awaiting next observation",
          );
          // A no-op/baseline monitor has no workflow evidence to change the
          // SourcePanel dependency graph. Explicitly invalidate its history
          // read so the operator can see the durable comparison immediately.
          setSourceHistoryRefreshKey((value) => value + 1);
          await Promise.all([
            refreshHistory(scanEpoch),
            refreshSourceHealth(scanEpoch),
          ]);
          return;
        }
        if (["needs_approval", "complete"].includes(current.status) && current.workflow) {
          setWorkflowState(current.workflow);
          setWorkflowId(current.workflow.workflow_id);
          const recommendedOption = current.workflow.agent_trace?.decision_copilot?.options?.find((option) => option.option_id === current.workflow.agent_trace?.decision_copilot?.recommendation_id);
          setArtifactDecisions(current.workflow.approval?.artifact_decisions || recommendedOption?.artifact_decisions || defaultDecisionsFor(current.workflow));
          setScanMessage("Scan complete · evidence verified · approval gate active");
          setSourceHistoryRefreshKey((value) => value + 1);
          await Promise.all([
            refreshHistory(scanEpoch),
            refreshSourceHealth(scanEpoch),
          ]);
          return;
        }
        setScanMessage(current.status === "running"
          ? (attempt > 80
            ? "Agent still running · Gemini is completing the evidence-bound impact pass"
            : "Agent running · verifying source and mapping impact")
          : "Agent queued · waiting for a durable run");
      }
      throw new Error("The agent job timed out");
    } catch (error) {
      if (sessionEpochRef.current !== scanEpoch) return;
      setScanMessage(`${runMode === "monitor" ? "Monitor unavailable" : "Unable to complete the live scan"} · ${error.message || "retry the request"}`);
      setJob((current) => current ? { ...current, status: "failed", error: error.message } : current);
    } finally {
      setScanning(false);
    }
  };

  const runSourceNow = async (sourceId) => {
    setSelectedSource(sourceId);
    selectNav("Overview");
    // The registry action is an operational check, not a synthetic replay.
    // Keep the top-level signed demo repeatable for judges, while this path
    // always compares the selected source against its tenant ledger.
    return runScan(sourceId, "monitor");
  };

  const approve = async (selectedOption) => {
    if (!workflowId || !liveWorkflow || decisionBusy) return;
    const decisionEpoch = sessionEpochRef.current;
    setDecisionBusy(true);
    try {
      const decision = selectedOption?.workflow_decision || (workflowState?.impact_graph?.summary?.category?.startsWith("Competitor")
        ? "approve_competitive_response"
        : "grandfather_existing_customers");
      const state = await approveWorkflow(
        workflowId,
        artifactDecisions,
        decision,
        selectedOption?.option_id,
        selectedOption?.copilot_artifact_override || false,
        selectedOption?.copilot_override_reason || null,
      );
      if (sessionEpochRef.current !== decisionEpoch) return;
      setWorkflowState(state);
      setJob((current) => current ? {
        ...current,
        status: state.status,
        workflow: state,
        public_summary: state.status === "reconciliation_required"
          ? "Action safely paused · same-operation recovery required"
          : "Action plan recorded · reversible packet created",
      } : current);
      setScanMessage(state.status === "reconciliation_required"
        ? "Action safely paused · reconcile the claimed operation"
        : "Action plan recorded · reversible packet created");
      refreshHistory();
    } catch (error) {
      if (sessionEpochRef.current !== decisionEpoch) return;
      setScanMessage(`Unable to record the decision · ${error.message || "retry the request"}`);
    } finally {
      setDecisionBusy(false);
    }
  };

  const reopen = async () => {
    if (!workflowId || !liveWorkflow || decisionBusy) return;
    const decisionEpoch = sessionEpochRef.current;
    setDecisionBusy(true);
    try {
      const state = await undoWorkflow(workflowId);
      if (sessionEpochRef.current !== decisionEpoch) return;
      setWorkflowState(state);
      setJob((current) => current ? {
        ...current,
        status: state.status,
        workflow: state,
        public_summary: state.status === "reconciliation_required"
          ? "Reversal safely paused · same-operation recovery required"
          : "Decision reopened · no external systems were changed",
      } : current);
      setScanMessage(state.status === "reconciliation_required"
        ? "Reversal safely paused · reconcile the claimed operation"
        : "Decision reopened · no external systems were changed");
      refreshHistory();
    } catch (error) {
      if (sessionEpochRef.current !== decisionEpoch) return;
      setScanMessage(`Unable to reopen the decision · ${error.message || "retry the request"}`);
    } finally {
      setDecisionBusy(false);
    }
  };

  const reconcile = async () => {
    if (!workflowId || !liveWorkflow || decisionBusy) return;
    const decisionEpoch = sessionEpochRef.current;
    setDecisionBusy(true);
    try {
      const state = await reconcileWorkflow(workflowId);
      if (sessionEpochRef.current !== decisionEpoch) return;
      setWorkflowState(state);
      setJob((current) => current ? {
        ...current,
        status: state.status,
        workflow: state,
        public_summary: state.status === "complete" ? "Operation reconciled · durable receipt confirmed" : "Operation recovery remains safely queued",
      } : current);
      setScanMessage(state.status === "reconciliation_required" ? "Recovery still required · no conflicting action allowed" : "Operation reconciled · durable outcome confirmed");
      refreshHistory();
    } catch (error) {
      if (sessionEpochRef.current !== decisionEpoch) return;
      setScanMessage(`Unable to reconcile the operation · ${error.message || "retry the request"}`);
    } finally {
      setDecisionBusy(false);
    }
  };

  const dismissSignal = async (reason) => {
    if (!workflowId || !liveWorkflow || decisionBusy) return;
    const decisionEpoch = sessionEpochRef.current;
    setDecisionBusy(true);
    try {
      const state = await dismissWorkflow(workflowId, reason);
      if (sessionEpochRef.current !== decisionEpoch) return;
      setWorkflowState(state);
      setJob((current) => current ? {
        ...current,
        status: state.status,
        workflow: state,
        public_summary: "Signal dismissed · reason recorded in the audit trail",
      } : current);
      setScanMessage("Signal dismissed · reason recorded in the audit trail");
      refreshHistory();
    } catch (error) {
      if (sessionEpochRef.current !== decisionEpoch) return;
      setScanMessage(`Unable to dismiss the signal · ${error.message || "retry the request"}`);
    } finally {
      setDecisionBusy(false);
    }
  };

  const retryFailedJob = async (jobId) => {
    const retryEpoch = sessionEpochRef.current;
    try {
      await retryJob(jobId);
      if (sessionEpochRef.current !== retryEpoch) return;
      setScanMessage("Retry queued · preserving the tenant source and policy boundary");
      refreshHistory(retryEpoch);
    } catch (error) {
      if (sessionEpochRef.current !== retryEpoch) return;
      setScanMessage(`Unable to retry the job · ${error.message || "retry the request"}`);
    }
  };

  const openHistoryJob = async (historyJob) => {
    const openEpoch = sessionEpochRef.current;
    try {
      setScanMessage("Loading durable workflow · restoring evidence and policy state");
      const loaded = await getJob(historyJob.job_id);
      if (sessionEpochRef.current !== openEpoch) return;
      if (!loaded.workflow?.workflow_id) throw new Error("This run has no recoverable workflow yet");
      const restored = loaded.workflow;
      const recommendedOption = restored.agent_trace?.decision_copilot?.options?.find((option) => option.option_id === restored.agent_trace?.decision_copilot?.recommendation_id);
      setJob(loaded);
      setWorkflowState(restored);
      setWorkflowId(restored.workflow_id);
      setSelectedSource(restored.evidence?.source_id || historyJob.source_id || selectedSource);
      setSelectedArtifact(restored.impacts?.[0]?.name || "Pricing battlecard");
      setArtifactDecisions(restored.approval?.artifact_decisions || recommendedOption?.artifact_decisions || defaultDecisionsFor(restored));
      setScanMessage("Durable run restored · evidence and approval state are ready to review");
      selectNav("Overview");
    } catch (error) {
      if (sessionEpochRef.current !== openEpoch) return;
      setScanMessage(`Unable to restore the durable run · ${error.message || "retry the request"}`);
    }
  };

  const updateArtifactDecision = (name, decision) => {
    setArtifactDecisions((current) => ({ ...current, [name]: decision }));
  };

  const focusArtifactWorklist = (name) => {
    setSelectedArtifact(name);
    window.requestAnimationFrame(() => {
      document.getElementById(artifactRowId(name))?.scrollIntoView({ behavior: "smooth", block: "center" });
    });
  };

  const focusSection = (sectionId) => {
    window.requestAnimationFrame(() => {
      document.getElementById(sectionId)?.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  };

  useEffect(() => {
    const status = workflowState?.status || (scanning ? "scanning" : "idle");
    if (!judgeMode || lastGuidedStatusRef.current === status) return;
    lastGuidedStatusRef.current = status;
    const target = status === "needs_approval"
      ? "approvals-section"
      : status === "complete"
        ? "proof-section"
        : ["approval_executing", "reversal_executing", "reconciliation_required"].includes(status)
          ? "approvals-section"
          : null;
    if (target) {
      const timer = window.setTimeout(() => focusSection(target), 150);
      return () => window.clearTimeout(timer);
    }
    return undefined;
  }, [judgeMode, scanning, workflowState?.status]);

  return (
    <div className="app-shell">
      <a className="skip-link" href="#main-content">Skip to main content</a>
      <Sidebar selected={selectedNav} onSelect={selectNav} />
      <main id="main-content">
        <header className="topbar">
          <h1>Promise change control room</h1>
          <div className="topbar-actions">
            <OperatorAccess />
            {scanMessage && <span className={`scan-message${scanFailed ? " error" : ""}`} role="status" aria-live="polite" title={scanMessage}>{scanFailed ? <AlertTriangle size={15} /> : <CheckCircle2 size={15} />}{scanning ? "Agent running" : scanFailed ? "Scan needs attention" : liveWorkflow ? "Ready for decision" : "Status updated"}</span>}
            <span className="lane-indicator"><ShieldCheck size={15} />{operatorSession.identityToken ? "Signed operator lane" : "Public judge lane"}</span>
          </div>
        </header>

        <div className="content">
        <div className="workspace-banner"><div className="workspace-banner-copy"><strong>Live production proof</strong><span>{operatorSession.identityToken ? `Signed tenant lane · ${operatorSession.tenantId} · human-gated connector execution` : "Public judge lane · real ADK + Gemini workflow · no external writes"}</span></div><span className="banner-status">{liveWorkflow ? (operatorSession.identityToken ? "Tenant workflow" : "Live agent workflow") : (operatorSession.identityToken ? "Ready to monitor" : "Safe to evaluate")}</span><ReleaseProof /></div>
          <section id="overview-section" className="overview-section">
            <p className="product-orientation">{approved ? "The source change is verified, the human decision is recorded, and every owner action remains traceable and reversible." : "A public promise changed. Driftline verifies the evidence, maps every affected owner, and stops at a human decision."}</p>
            <UtilityNextStep workflow={workflowState} job={job} scanning={scanning} sourcePaused={selectedSourcePaused} onRunScan={() => runScan()} onNavigate={focusSection} />
            <section className="incident-header">
              <span className="incident-icon"><AlertTriangle size={30} /></span>
              <div className="incident-title">
              <h2>{workflowState?.title || (selectedSource === "competitor/pricing" ? "Competitor pricing moved" : selectedSource === "competitor/offerings" ? "Competitor offering changed" : selectedSource === "competitor/blog" ? "Competitor product narrative changed" : "Enterprise plan packaging changed")}</h2>
                <div className="metadata">
                  <span><strong>Source</strong>{evidence.source_name}</span><i /><span><strong>Detected</strong>{workflowState ? "Just now" : "Awaiting scan"}</span><i />
                  <span><strong>Confidence</strong>{workflowState ? <><CheckCircle2 className="verified" size={15} />Verified</> : <em className="metadata-preview">Fixture · scan to verify</em>}</span><i /><span><strong>{workflowState ? "Severity" : "Scenario risk"}</strong><b className="risk-dot high-dot" />High</span>
                </div>
              </div>
              <button className="secondary incident-details" onClick={() => setShowEvidence(true)} type="button">View source evidence<ChevronDown size={16} /></button>
            </section>

            <JudgeJourney workflow={workflowState} scanning={scanning} judgeMode={judgeMode} onToggleJudgeMode={() => setJudgeMode((current) => !current)} onNavigate={focusSection} />

            <ChangeCardPanel card={workflowState?.change_card} />

            {structuredAnalysis && (
              <section className={`analysis-brief ${structuredAnalysis.mode === "gemini_structured" ? "verified" : "fallback"}`} aria-label="Structured impact analysis">
                <div className="analysis-brief-heading"><div><span className="analysis-kicker">Agent conclusion</span><strong>{structuredAnalysis.mode === "gemini_structured" ? "Gemini impact analysis" : "Deterministic demo fallback"}</strong></div><span className="live-label">{structuredAnalysis.artifact_count || 0} evidence-bound surfaces</span></div>
                {structuredAnalysis.summary && <p>{structuredAnalysis.summary}</p>}
                {structuredAnalysis.rationale && <small>{structuredAnalysis.rationale}</small>}
              </section>
            )}

            <div className="dashboard-grid">
              <div className="main-column">
                <div id="evidence-section" className="upper-grid">
                  <EvidenceDiff collapsed={evidenceCollapsed} onToggle={() => setEvidenceCollapsed((current) => !current)} evidence={evidence} />
                  <ImpactMap items={impacts} graph={workflowState?.impact_graph} approved={approved} sourceName={evidence.source_name} sourceCategory={selectedSourceDefinition?.category || (selectedSource.startsWith("competitor/") ? "Competitor pricing" : "Own pricing")} onSelectArtifact={focusArtifactWorklist} />
                </div>
                <ArtifactTable items={impacts} onSelect={setSelectedArtifact} selected={selectedArtifact} />
                <ArtifactDetail item={selectedItem} live={liveWorkflow && !approved} decision={artifactDecisions[selectedItem?.name]} onDecisionChange={updateArtifactDecision} packetUrl={approved ? packetHref : null} onPacket={operatorSession.identityToken && workflowId ? () => downloadPacket(workflowId).catch((error) => setScanMessage(`Unable to download packet · ${error.message}`)) : null} />
              </div>
              <aside id="approvals-section">
              <DecisionPanel status={workflowState?.status} operation={workflowState?.operation} approved={approved} dismissed={dismissed} approval={approval} artifactDecisions={artifactDecisions} copilot={job?.workflow?.agent_trace?.decision_copilot} evidence={evidence} actionRecord={workflowState?.action_record} onApprove={approve} onOptionSelect={(option) => setArtifactDecisions(option.artifact_decisions)} onUndo={reopen} onReconcile={reconcile} onDismiss={dismissSignal} onEvidence={() => setShowEvidence(true)} onPacket={operatorSession.identityToken && workflowId ? () => downloadPacket(workflowId).catch((error) => setScanMessage(`Unable to download packet · ${error.message}`)) : null} isLive={liveWorkflow && workflowState?.status === "needs_approval"} busy={decisionBusy} packetHref={packetHref} sourceCategory={workflowState?.impact_graph?.summary?.category || selectedSourceDefinition?.category || (selectedSource.startsWith("competitor/") ? "Competitor pricing" : "Own pricing")} requiresDecisionCopilot={Boolean(operatorSession.identityToken)} />
              </aside>
            </div>
            {workflowState?.action_items?.length > 0 && <ActionItems workflowId={workflowId} items={workflowState.action_items} workflowStatus={workflowState.status} onChange={(state) => { setWorkflowState(state); setJob((current) => current ? { ...current, status: state.status, workflow: state } : current); refreshHistory(); }} />}
            <IntegrationPanel targets={workflowState?.integration_targets} approved={approved} dismissed={dismissed} actionRecord={actionRecord} operatorSession={operatorSession} />
            {workflowId && <ScenarioSimulator workflowId={workflowId} />}
            <ChangeTimeline state={workflowState} />
            <WorkflowTimeline state={workflowState} />
          </section>

          <SourcePanel historyRefreshKey={sourceHistoryRefreshKey} monitorOutcome={job?.run_mode === "monitor" && job?.source_id === selectedSource ? job?.source_status : null} evidence={evidence} dataMode={workflowState?.data_mode || evidence.data_mode || demoEvidence.data_mode} hasLiveWorkflow={Boolean(workflowState)} sources={sources} sourceHealth={sourceHealth} sourceHealthState={sourceHealthState} selectedSource={selectedSource} onSourceChange={handleSourceChange} operatorSession={operatorSession} onRunSource={runSourceNow} onVisible={() => refreshSourceHealth()} onRegistered={(payload) => { if (payload?.source?.source_id) handleSourceChange(payload.source.source_id); setSourceHistoryRefreshKey((value) => value + 1); getSources().then((next) => setSources(next.sources || [])).catch(() => {}); refreshSourceHealth(); }} onLifecycleChanged={() => { getSources().then((next) => setSources(next.sources || [])).catch(() => {}); refreshSourceHealth(); }} />
          <ChangeGenomePanel operatorSession={operatorSession} />
          <TraceEvalPanel workflowId={workflowId} />
          <ValueProofPanel operatorSession={operatorSession} />
          <PilotMeasurementPanel operatorSession={operatorSession} />
          <SalesforceConnectorPanel operatorSession={operatorSession} />
          <RunHistory jobs={recentJobs} loading={historyLoading} publicMode={!operatorSession.identityToken} canRetry={Boolean(operatorSession.identityToken)} onRetry={retryFailedJob} onOpen={openHistoryJob} onVisible={() => refreshHistory()} />
          <AgentTrace job={job} />
          <section id="activity-section"><ActivityLog events={events} /></section>
          <TrustPanel actionRecord={actionRecord} />
          <footer className="demo-footer"><span>ⓘ Synthetic replay remains available when the public source cannot be fetched.</span><span>Approval gating is deterministic; the public evaluation lane is packet-safe and configured writes require signed operator approval.</span><span className="legal-links"><a href="/privacy.html">Privacy</a><a href="/terms.html">Terms</a></span></footer>
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
