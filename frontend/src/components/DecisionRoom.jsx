import { ArrowRight, Bot, Check, CheckCircle2, CircleAlert, ClipboardCheck, Copy, Database, Download, FileCheck2, GitCompareArrows, History, LoaderCircle, PencilLine, Play, Plus, Radar, RotateCcw, ShieldCheck, Trash2 } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { approveDecisionTwin, downloadDecisionTwinPilotStarter, getDecisionTwin, getDecisionTwinEvaluation, recordDecisionTwinMeasurement, recordDecisionTwinOutcome, reviewDecisionTwinEvidence, startDecisionTwin, startDecisionTwinIntake } from "../api";
import CounterfactualCompare from "./CounterfactualCompare";
import EvidenceCouncil from "./EvidenceCouncil";
import LearningReceipt from "./LearningReceipt";

const stages = ["Detect drift", "Compare options", "Approve action", "Learn"];

const optionTitle = (options, id) => options.find((option) => option.option_id === id)?.title || id;

const humanize = (value) => String(value || "").replaceAll("_", " ");

function ProductOperatingLoop({ loop }) {
  if (!loop) return null;
  const harvest = loop.evidence_harvest;
  const alignment = loop.stakeholder_alignment;
  const execution = loop.execution_contract;
  const outcome = loop.outcome_autopilot;
  const memory = loop.compounding_memory;
  return <section className="product-operating-loop" aria-labelledby="product-operating-loop-title">
    <header>
      <div><span>Continuous PM operating loop</span><h3 id="product-operating-loop-title">Every decision leaves the next one smarter.</h3></div>
      <b>{humanize(loop.stage)}</b>
    </header>
    <ol className="product-operating-journey" aria-label="Signal to measured learning progress">
      {loop.journey.map((item) => <li className={item.state} key={item.step} aria-current={item.state === "active" ? "step" : undefined}>
        <span>{item.state === "done" ? <Check size={11} /> : item.step}</span><small>{item.label}</small>
      </li>)}
    </ol>
    <div className="product-operating-cards">
      <article>
        <div className="product-operating-card-heading"><Database size={16} /><h4>Evidence harvest agents</h4><b>{harvest.source_count} sources</b></div>
        <p>{harvest.disclosure}</p>
        <ul>{harvest.sources.slice(0, 4).map((source) => <li key={source.source_id}><strong>{humanize(source.channel)}</strong><span>{humanize(source.mode)} · {Math.round(source.confidence * 100)}%</span></li>)}</ul>
        {harvest.missing_channels.length > 0 && <small>Missing: {harvest.missing_channels.map(humanize).join(" · ")}</small>}
      </article>
      <article>
        <div className="product-operating-card-heading"><GitCompareArrows size={16} /><h4>Stakeholder alignment agent</h4><b>{humanize(alignment.status)}</b></div>
        <p>{alignment.unresolved_tradeoffs[0] || "The measured outcome resolved the active tradeoff."}</p>
        <ul>{alignment.positions.slice(0, 3).map((position) => <li key={position.position_id}><strong>{position.label}</strong><span>{optionTitle([], position.preferred_option)}</span></li>)}</ul>
        <small>{alignment.dissent_preserved ? "Dissent preserved" : "Consensus requires challenge"} · {alignment.evidence_requests[0] || "No open evidence request"}</small>
      </article>
      <article>
        <div className="product-operating-card-heading"><ClipboardCheck size={16} /><h4>Commitment &amp; execution agent</h4><b>{humanize(execution.status)}</b></div>
        <p>{execution.scope}</p>
        <dl><div><dt>Owner</dt><dd>{execution.owner || "Human approval required"}</dd></div><div><dt>Review</dt><dd>{execution.review_at || "Starts after approval"}</dd></div><div><dt>External writes</dt><dd>{execution.external_writes ? "Yes" : "None in public lane"}</dd></div></dl>
        <small>{execution.next_action}</small>
      </article>
      <article>
        <div className="product-operating-card-heading"><History size={16} /><h4>Outcome autopilot + product memory</h4><b>{memory.cycle_count} measured cycle{memory.cycle_count === 1 ? "" : "s"}</b></div>
        <p>{outcome.trigger}</p>
        <dl><div><dt>Monitor</dt><dd>{humanize(outcome.status)}</dd></div><div><dt>Next check</dt><dd>{outcome.next_check_at || "After approval"}</dd></div><div><dt>Generation</dt><dd>{memory.current_generation}</dd></div></dl>
        <small>{memory.insights.at(-1)?.statement} {memory.disclosure}</small>
      </article>
    </div>
  </section>;
}

function focusAfterRender(id) {
  window.requestAnimationFrame(() => document.getElementById(id)?.focus({ preventScroll: true }));
}

const emptyIntake = {
  question: "",
  current_commitment: "",
  urgency: "",
  positive_signal: "",
  risk_signal: "",
  evidence_inputs: [],
  affected_segment: "",
  primary_metric: "",
  risk_metric: "",
  metric_unit: "%",
  baseline: "",
  success_operator: "gte",
  success_threshold: "",
  risk_baseline: "",
  stop_operator: "gte",
  stop_threshold: "",
  review_days: "7",
  action_owner: "",
};

export default function DecisionRoom({ onOpenWorkflow }) {
  const [decisionCase, setDecisionCase] = useState(null);
  const [selectedId, setSelectedId] = useState("segment");
  const [evaluation, setEvaluation] = useState(null);
  const [busy, setBusy] = useState("");
  const [monitoring, setMonitoring] = useState(false);
  const [error, setError] = useState("");
  const [intakeOpen, setIntakeOpen] = useState(false);
  const [intakeStep, setIntakeStep] = useState(1);
  const [intake, setIntake] = useState(emptyIntake);
  const [copyStatus, setCopyStatus] = useState("");
  const [linkStatus, setLinkStatus] = useState("");
  const [pilotExportStatus, setPilotExportStatus] = useState("");
  const [reviewingEvidenceId, setReviewingEvidenceId] = useState("");
  const [approverName, setApproverName] = useState("");
  const intakeSectionRef = useRef(null);
  const intakeTitleRef = useRef(null);
  const isProvidedIntake = Boolean(decisionCase?.events?.some((event) => event.source_mode === "pm_provided_unverified"));
  const canEdit = decisionCase?.can_edit !== false;

  const applyDecisionCase = (next) => {
    setDecisionCase(next);
    setEvaluation(null);
    setSelectedId(next.council.recommendation);
    const url = new URL(window.location.href);
    url.searchParams.set("decision", next.case_id);
    window.history.replaceState(null, "", url);
  };

  useEffect(() => {
    const caseId = new URLSearchParams(window.location.search).get("decision");
    if (!caseId || !/^[a-z0-9][a-z0-9_-]{2,100}$/.test(caseId)) return;
    let cancelled = false;
    setBusy("restore");
    getDecisionTwin(caseId)
      .then((next) => {
        if (!cancelled) applyDecisionCase(next);
      })
      .catch(() => {
        if (!cancelled) setError("This decision return link is unavailable or expired.");
      })
      .finally(() => {
        if (!cancelled) setBusy("");
      });
    return () => { cancelled = true; };
  }, []);

  useEffect(() => {
    if (!intakeOpen) return undefined;
    const frame = window.requestAnimationFrame(() => {
      intakeTitleRef.current?.focus({ preventScroll: true });
      intakeSectionRef.current?.scrollIntoView({
        behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth",
        block: "start",
      });
    });
    return () => window.cancelAnimationFrame(frame);
  }, [intakeOpen, intakeStep]);

  useEffect(() => {
    if (!decisionCase?.case_id) return;
    getDecisionTwinEvaluation(decisionCase.case_id).then(setEvaluation).catch(() => setEvaluation(null));
  }, [decisionCase]);

  useEffect(() => {
    if (decisionCase?.status !== "experiment_active" || isProvidedIntake) {
      setMonitoring(false);
      return undefined;
    }
    if (decisionCase.monitor_status === "fallback_required") {
      setMonitoring(false);
      return undefined;
    }
    let cancelled = false;
    let attempts = 0;
    let timer;
    setMonitoring(true);
    const poll = async () => {
      attempts += 1;
      try {
        const latest = await getDecisionTwin(decisionCase.case_id);
        if (cancelled) return;
        if (latest.status !== "experiment_active") {
          setDecisionCase(latest);
          setSelectedId(latest.council.recommendation);
          setApproverName("");
          setMonitoring(false);
          return;
        }
      } catch {
        // A transient read does not cancel the durable Cloud Tasks monitor.
      }
      if (!cancelled && attempts < 20) timer = window.setTimeout(poll, 1000);
      else if (!cancelled) setMonitoring(false);
    };
    timer = window.setTimeout(poll, 700);
    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [decisionCase?.case_id, decisionCase?.generation, decisionCase?.status, isProvidedIntake]);

  const runCouncil = async () => {
    setBusy("council"); setError("");
    try {
      const next = await startDecisionTwin();
      applyDecisionCase(next);
      focusAfterRender("decision-room-title");
    } catch (nextError) { setError(nextError.message); } finally { setBusy(""); }
  };

  const toggleIntake = () => {
    const nextOpen = !intakeOpen;
    setIntakeOpen(nextOpen);
    if (nextOpen) {
      setIntakeStep(1);
      setError("");
    }
  };

  const addEvidenceInput = () => {
    if (intake.evidence_inputs.length >= 4) return;
    setIntake({
      ...intake,
      evidence_inputs: [...intake.evidence_inputs, {
        source_type: "customer",
        source_label: "",
        title: "",
        observation: "",
        observed_on: "",
        stance: "supports",
      }],
    });
  };

  const updateEvidenceInput = (index, field, value) => {
    setIntake({
      ...intake,
      evidence_inputs: intake.evidence_inputs.map((item, itemIndex) => (
        itemIndex === index ? { ...item, [field]: value } : item
      )),
    });
  };

  const removeEvidenceInput = (index) => {
    setIntake({
      ...intake,
      evidence_inputs: intake.evidence_inputs.filter((_, itemIndex) => itemIndex !== index),
    });
  };

  const submitIntake = async (event) => {
    event.preventDefault();
    if (intakeStep === 1) {
      setError("");
      setIntakeStep(2);
      return;
    }
    setBusy("intake"); setError("");
    try {
      const baseline = Number(intake.baseline);
      const successThreshold = Number(intake.success_threshold);
      const riskBaseline = Number(intake.risk_baseline);
      const stopThreshold = Number(intake.stop_threshold);
      const successMoves = intake.success_operator === "gte"
        ? successThreshold > baseline
        : successThreshold < baseline;
      const riskWorsens = intake.stop_operator === "gte"
        ? stopThreshold > riskBaseline
        : stopThreshold < riskBaseline;
      if (!successMoves) {
        throw new Error("Success threshold must improve on the stated outcome baseline.");
      }
      if (!riskWorsens) {
        throw new Error("Stop threshold must worsen from the stated risk baseline.");
      }
      const payload = {
        question: intake.question,
        current_commitment: intake.current_commitment,
        urgency: intake.urgency,
        positive_signal: intake.positive_signal,
        risk_signal: intake.risk_signal,
        evidence_inputs: intake.evidence_inputs,
        affected_segment: intake.affected_segment,
        measurement_contract: {
          primary_metric: intake.primary_metric,
          risk_metric: intake.risk_metric,
          metric_unit: intake.metric_unit,
          baseline,
          success_operator: intake.success_operator,
          success_threshold: successThreshold,
          risk_baseline: riskBaseline,
          stop_operator: intake.stop_operator,
          stop_threshold: stopThreshold,
          review_days: Number(intake.review_days),
          action_owner: intake.action_owner,
        },
      };
      if (!payload.affected_segment.trim()) delete payload.affected_segment;
      applyDecisionCase(await startDecisionTwinIntake(payload));
      focusAfterRender("decision-room-title");
    } catch (nextError) { setError(nextError.message); } finally { setBusy(""); }
  };

  const approve = async () => {
    setBusy("approval"); setError("");
    try {
      setDecisionCase(await approveDecisionTwin(decisionCase.case_id, selectedId, decisionCase.council.synthesis_hash, decisionCase.generation, approverName.trim()));
      focusAfterRender("learning-receipt-title");
    } catch (nextError) { setError(nextError.message); } finally { setBusy(""); }
  };

  const observeOutcome = async () => {
    setBusy("outcome"); setError("");
    try {
      const next = await recordDecisionTwinOutcome(decisionCase.case_id, decisionCase.generation);
      applyDecisionCase(next);
      if (["reopened", "review_required"].includes(next.status)) setApproverName("");
    } catch (nextError) { setError(nextError.message); } finally { setBusy(""); }
  };

  const attachMeasurement = async (measurement) => {
    setBusy("measurement"); setError("");
    try {
      const next = await recordDecisionTwinMeasurement(
        decisionCase.case_id,
        decisionCase.generation,
        measurement,
      );
      applyDecisionCase(next);
      if (["reopened", "review_required"].includes(next.status)) setApproverName("");
    } catch (nextError) { setError(nextError.message); } finally { setBusy(""); }
  };

  const resetDecision = () => {
    setDecisionCase(null);
    setEvaluation(null);
    setSelectedId("segment");
    setMonitoring(false);
    setBusy("");
    setError("");
    setCopyStatus("");
    setLinkStatus("");
    setPilotExportStatus("");
    setReviewingEvidenceId("");
    setApproverName("");
    setIntakeOpen(false);
    setIntakeStep(1);
    setIntake(emptyIntake);
    const url = new URL(window.location.href);
    url.searchParams.delete("decision");
    window.history.replaceState(null, "", url);
    focusAfterRender("decision-room-hero-title");
  };

  const copyReturnLink = async () => {
    try {
      await navigator.clipboard.writeText(window.location.href);
      setLinkStatus("Copied view-only link");
      window.setTimeout(() => setLinkStatus(""), 1800);
    } catch {
      setError("Copy was blocked by the browser. Copy the current address manually.");
    }
  };

  const downloadPilotStarter = async () => {
    setPilotExportStatus("Preparing private starter…");
    setError("");
    try {
      await downloadDecisionTwinPilotStarter(decisionCase.case_id);
      setPilotExportStatus("Private starter downloaded");
      window.setTimeout(() => setPilotExportStatus(""), 1800);
    } catch (nextError) {
      setPilotExportStatus("");
      setError(nextError.message);
    }
  };

  const reviewEvidence = async (evidenceNodeId) => {
    setReviewingEvidenceId(evidenceNodeId);
    setError("");
    try {
      const next = await reviewDecisionTwinEvidence(
        decisionCase.case_id,
        evidenceNodeId,
        decisionCase.generation,
      );
      setDecisionCase(next);
      setEvaluation(null);
    } catch (nextError) {
      setError(nextError.message);
    } finally {
      setReviewingEvidenceId("");
    }
  };

  const copyDecisionBrief = async () => {
    const option = decisionCase.council.options.find((item) => item.option_id === selectedId)
      || decisionCase.council.options.find((item) => item.option_id === decisionCase.council.recommendation);
    const contract = decisionCase.measurement_contract;
    const plan = decisionCase.experiment_plan;
    const thresholdPhrase = (operator) => operator === "gte" ? "at least" : "at most";
    const operatingContract = contract ? [
      "",
      "Operating contract:",
      `Owner: ${plan?.owner || contract.action_owner}`,
      `Segment: ${plan?.target_segment || option?.affected_segments?.join(", ") || "Define before approval"}`,
      `Primary: ${contract.primary_metric} from ${contract.baseline} ${contract.metric_unit} to ${thresholdPhrase(contract.success_operator)} ${contract.success_threshold} ${contract.metric_unit}`,
      `Risk stop: ${contract.risk_metric} from ${contract.risk_baseline} ${contract.metric_unit} to ${thresholdPhrase(contract.stop_operator)} ${contract.stop_threshold} ${contract.metric_unit}`,
      `Review: ${plan?.review_at ? new Date(plan.review_at).toISOString() : `${contract.review_days} days after approval`}`,
    ] : [];
    const brief = [
      `# ${decisionCase.title}`,
      "",
      ...(decisionCase.decision_debt ? [
        `Decision debt: ${decisionCase.decision_debt.title}`,
        `Debt score: ${decisionCase.decision_debt.score}/100 · ${decisionCase.decision_debt.state}`,
        `Trigger: ${decisionCase.decision_debt.trigger}`,
        `Next: ${decisionCase.decision_debt.recommended_next_step}`,
        "",
      ] : []),
      `Decision: ${decisionCase.question}`,
      `Why now: ${decisionCase.urgency}`,
      `Current commitment: ${decisionCase.current_commitment}`,
      "",
      `Recommendation: ${option?.title || decisionCase.council.recommendation}`,
      decisionCase.council.executive_summary,
      `Decisive conflict: ${decisionCase.council.decisive_conflict}`,
      "",
      `Guardrail: ${option?.guardrails?.[0] || "Define before action"}`,
      `Rollback: ${option?.rollback || "Return to the prior state"}`,
      ...operatingContract,
      "",
      "Evidence:",
      ...decisionCase.evidence_nodes.map((node) => `- ${node.title}: ${node.excerpt} (${node.source_label})`),
      ...(decisionCase.events.some((event) => event.source_mode === "pm_provided_unverified") ? [
        "",
        "Evidence readiness: PM-provided and unverified",
        "Next validation: quantify the segment split; corroborate the risk theme; verify owner feasibility.",
      ] : []),
    ].join("\n");
    try {
      await navigator.clipboard.writeText(brief);
      setCopyStatus("Copied");
      window.setTimeout(() => setCopyStatus(""), 1800);
    } catch {
      setError("Copy was blocked by the browser. Select the brief and copy it manually.");
    }
  };

  const activeStage = !decisionCase ? 0 : decisionCase.status === "needs_approval" || decisionCase.status === "reopened" ? 2 : 3;

  if (!decisionCase) return (
    <>
    <section className="decision-room-hero" aria-labelledby="decision-room-hero-title">
      <div className="decision-room-hero-copy">
        <div className="decision-room-kicker">For product managers <span>making high-stakes product calls</span></div>
        <h2 id="decision-room-hero-title">Turn conflicting evidence into a decision your team can defend.</h2>
        <p>When usage, customer calls, support, and roadmap commitments disagree, Driftline shows what changed, compares the safe responses, and turns your choice into a measurable experiment.</p>
        <div className="decision-room-hero-actions">
          <button className="primary decision-room-run" type="button" onClick={runCouncil} disabled={Boolean(busy)} aria-busy={busy === "council"}>
            {busy ? <LoaderCircle className="spin" size={18} /> : <Play size={18} />}
            {busy ? "Reading the decision evidence…" : "Run the decision workflow"}
          </button>
          <button className="secondary decision-room-intake-trigger" type="button" onClick={toggleIntake} disabled={Boolean(busy)} aria-expanded={intakeOpen} aria-controls="decision-intake-form">
            <PencilLine size={17} />Use my decision
          </button>
          <span>One approval starts the autonomous monitor · no second PM prompt</span>
        </div>
        {busy === "council" && <p className="decision-room-status" role="status" aria-live="polite"><LoaderCircle className="spin" size={15} />Checking evidence, disagreement, and reversible options.</p>}
        {error && !intakeOpen && <p className="decision-room-error" role="alert"><CircleAlert size={16} />{error}</p>}
        <div className="decision-room-outcome-rail" aria-label="What Driftline produces">
          <span><b>Understand</b>What changed—and which segment is at risk</span>
          <span><b>Decide</b>Ship, segment, roll back, or defer</span>
          <span><b>Prove</b>Guardrail, rollback, and outcome receipt</span>
        </div>
        <div className="decision-room-case-preview" aria-label="Live decision in this demo">
          <span>Live decision in this demo</span>
          <strong>Should the onboarding redesign ship to every workspace next week?</strong>
          <small>Enterprise activation is down while the rollout commitment is seven days away.</small>
        </div>
        <div className="decision-room-reusable-scope" aria-label="Reusable decision types">
          <span>Same loop for</span>
          <b>Rollouts</b><b>Launches</b><b>Pricing</b><b>Packaging</b>
        </div>
      </div>
      <div className="decision-room-promise decision-room-risk-card">
        <div className="decision-room-risk-heading"><span><ShieldCheck size={18} />Example decision at risk</span><strong>7 days to rollout</strong></div>
        <h3>Onboarding redesign</h3>
        <p>Small-workspace activation improved <b className="decision-positive">+9%</b>, while enterprise activation fell <b className="decision-negative">-11%</b>.</p>
        <dl className="decision-room-risk-facts">
          <div><dt>The hidden problem</dt><dd>One rollout has opposite results by segment</dd></div>
          <div><dt>The usable answer</dt><dd>Segment, test the failure mode, and stop automatically</dd></div>
        </dl>
        <div className="decision-room-safe-note"><ShieldCheck size={15} />No external writes before approval</div>
      </div>
    </section>
    {intakeOpen && <section ref={intakeSectionRef} className="decision-intake" id="decision-intake-form" aria-labelledby="decision-intake-title">
      <header>
        <div><span className="decision-room-bridge-kicker">Bring your own decision</span><h2 ref={intakeTitleRef} tabIndex="-1" id="decision-intake-title">Turn the decision already blocking your team into a bounded brief.</h2></div>
        <p>{intakeStep === 1 ? "Start with the commitment and the strongest evidence on each side. No metrics or configuration yet." : "Now define what success, harm, ownership, and review mean before any response can be approved."}</p>
      </header>
      <ol className="decision-intake-progress" aria-label="Decision intake progress">
        <li aria-current={intakeStep === 1 ? "step" : undefined} className={intakeStep === 1 ? "active" : "complete"}><b>1</b><span>Decision context<small>Question, commitment, and conflict</small></span></li>
        <li aria-current={intakeStep === 2 ? "step" : undefined} className={intakeStep === 2 ? "active" : ""}><b>2</b><span>Operating contract<small>Metric, guardrail, owner, and review</small></span></li>
      </ol>
      <form onSubmit={submitIntake}>
        {intakeStep === 1 ? <>
          <label className="decision-intake-wide"><span>Decision question</span><textarea required minLength="12" maxLength="280" rows="2" value={intake.question} onChange={(event) => setIntake({ ...intake, question: event.target.value })} placeholder="Should we expand the beta to all mid-market accounts next month?" /></label>
          <label><span>Current commitment</span><textarea required minLength="12" maxLength="320" rows="3" value={intake.current_commitment} onChange={(event) => setIntake({ ...intake, current_commitment: event.target.value })} placeholder="Launch to every mid-market account on September 15." /></label>
          <label><span>Why now</span><textarea required minLength="12" maxLength="320" rows="3" value={intake.urgency} onChange={(event) => setIntake({ ...intake, urgency: event.target.value })} placeholder="Sales has committed the date and the allocation decision is due Friday." /></label>
          <label><span>Strongest signal in favor</span><textarea required minLength="12" maxLength="500" rows="3" value={intake.positive_signal} onChange={(event) => setIntake({ ...intake, positive_signal: event.target.value })} placeholder="Beta users complete the core workflow faster and renewal intent improved." /></label>
          <label><span>Strongest risk signal</span><textarea required minLength="12" maxLength="500" rows="3" value={intake.risk_signal} onChange={(event) => setIntake({ ...intake, risk_signal: event.target.value })} placeholder="Admins report permission confusion and support volume is rising." /></label>
          <fieldset className="decision-evidence-pack">
            <legend>Corroborating evidence pack <small>Optional · up to four redacted observations</small></legend>
            <div className="decision-evidence-pack-intro">
              <p>Add signals from research, support, analytics, or the product surface. Driftline preserves each source and its direction instead of flattening them into one note.</p>
              <button className="secondary" type="button" onClick={addEvidenceInput} disabled={intake.evidence_inputs.length >= 4}><Plus size={15} />Add source</button>
            </div>
            {intake.evidence_inputs.length === 0 && <div className="decision-evidence-pack-empty"><Database size={18} /><span>The two strongest signals above are enough to continue. Add sources when you want a decision packet that can be independently challenged.</span></div>}
            {intake.evidence_inputs.map((evidence, index) => <article className="decision-evidence-input" key={`evidence-${index}`}>
              <header><strong>Source {index + 1}</strong><button type="button" className="icon-button" aria-label={`Remove source ${index + 1}`} onClick={() => removeEvidenceInput(index)}><Trash2 size={15} /></button></header>
              <label><span>Source type</span><select value={evidence.source_type} onChange={(event) => updateEvidenceInput(index, "source_type", event.target.value)}><option value="customer">Customer research</option><option value="support">Support signal</option><option value="metric">Product analytics</option><option value="image">Product surface</option></select></label>
              <label><span>Direction</span><select value={evidence.stance} onChange={(event) => updateEvidenceInput(index, "stance", event.target.value)}><option value="supports">Supports the commitment</option><option value="contradicts">Contradicts the commitment</option></select></label>
              <label><span>Source label</span><input required minLength="2" maxLength="100" value={evidence.source_label} onChange={(event) => updateEvidenceInput(index, "source_label", event.target.value)} placeholder="Q3 onboarding interviews" /></label>
              <label><span>Observed on</span><input required type="date" value={evidence.observed_on} onChange={(event) => updateEvidenceInput(index, "observed_on", event.target.value)} /></label>
              <label><span>Observation title</span><input required minLength="2" maxLength="120" value={evidence.title} onChange={(event) => updateEvidenceInput(index, "title", event.target.value)} placeholder="Admins hesitate at role setup" /></label>
              <label className="decision-intake-wide"><span>Redacted observation</span><textarea required minLength="12" maxLength="600" rows="2" value={evidence.observation} onChange={(event) => updateEvidenceInput(index, "observation", event.target.value)} placeholder="Three of five interviewed admins could not predict which permissions a new role would inherit." /></label>
            </article>)}
            <small className="decision-evidence-pack-disclosure"><ShieldCheck size={13} />Do not paste names, transcripts, credentials, account IDs, or raw customer records. Every added source remains PM-provided and unverified.</small>
          </fieldset>
          <div className="decision-intake-submit"><div><ShieldCheck size={15} /><span>Use non-confidential context. Every note remains PM-provided and unverified.</span></div><button className="primary" type="submit"><ArrowRight size={17} />Continue to operating contract</button></div>
        </> : <>
          <fieldset className="decision-intake-contract">
          <legend>Define the operating contract before approval</legend>
          <p>The result stays provisional until you name what success means, what stops the action, who owns it, and when the team reviews it.</p>
          <label><span>Affected segment</span><input required minLength="2" maxLength="80" value={intake.affected_segment} onChange={(event) => setIntake({ ...intake, affected_segment: event.target.value })} placeholder="Mid-market admins" /></label>
          <label><span>Action owner</span><input required minLength="2" maxLength="120" value={intake.action_owner} onChange={(event) => setIntake({ ...intake, action_owner: event.target.value })} placeholder="Taylor, Product Lead" /></label>
          <label><span>Primary outcome metric</span><input required minLength="2" maxLength="100" value={intake.primary_metric} onChange={(event) => setIntake({ ...intake, primary_metric: event.target.value })} placeholder="Workflow completion rate" /></label>
          <label><span>Risk guardrail metric</span><input required minLength="2" maxLength="100" value={intake.risk_metric} onChange={(event) => setIntake({ ...intake, risk_metric: event.target.value })} placeholder="Failed workflow rate" /></label>
          <label><span>Unit</span><input required minLength="1" maxLength="20" value={intake.metric_unit} onChange={(event) => setIntake({ ...intake, metric_unit: event.target.value })} placeholder="%" /></label>
          <label><span>Review window</span><select required value={intake.review_days} onChange={(event) => setIntake({ ...intake, review_days: event.target.value })}><option value="3">3 days</option><option value="7">7 days</option><option value="14">14 days</option><option value="30">30 days</option></select></label>
          <label><span>Outcome baseline</span><input required type="number" step="any" value={intake.baseline} onChange={(event) => setIntake({ ...intake, baseline: event.target.value })} placeholder="38" /></label>
          <label><span>Success threshold</span><span className="decision-intake-threshold"><select aria-label="Success direction" value={intake.success_operator} onChange={(event) => setIntake({ ...intake, success_operator: event.target.value })}><option value="gte">At least</option><option value="lte">At most</option></select><input aria-label="Success threshold" required type="number" step="any" value={intake.success_threshold} onChange={(event) => setIntake({ ...intake, success_threshold: event.target.value })} placeholder="45" /></span></label>
          <label><span>Risk baseline</span><input required type="number" step="any" value={intake.risk_baseline} onChange={(event) => setIntake({ ...intake, risk_baseline: event.target.value })} placeholder="3" /></label>
          <label><span>Stop threshold</span><span className="decision-intake-threshold"><select aria-label="Stop direction" value={intake.stop_operator} onChange={(event) => setIntake({ ...intake, stop_operator: event.target.value })}><option value="gte">At least</option><option value="lte">At most</option></select><input aria-label="Stop threshold" required type="number" step="any" value={intake.stop_threshold} onChange={(event) => setIntake({ ...intake, stop_threshold: event.target.value })} placeholder="8" /></span></label>
          </fieldset>
          <div className="decision-intake-submit"><div><ShieldCheck size={15} /><span>No external actions. A human still approves the response.</span></div><div className="decision-intake-actions"><button className="secondary" type="button" onClick={() => { setIntakeStep(1); setError(""); }} disabled={Boolean(busy)}>Back to decision context</button><button className="primary" type="submit" disabled={Boolean(busy)}>{busy === "intake" ? <LoaderCircle className="spin" size={17} /> : <ArrowRight size={17} />}{busy === "intake" ? "Building the decision brief…" : "Build my decision brief"}</button></div></div>
        </>}
      </form>
      {error && <p className="decision-room-error" role="alert"><CircleAlert size={16} />{error}</p>}
    </section>}
    <section className="decision-room-utility-bridge" aria-labelledby="decision-room-utility-title">
      <header>
        <div>
          <span className="decision-room-bridge-kicker">What this replaces</span>
          <h2 id="decision-room-utility-title">The alignment meeting, evidence hunt, and post-launch guesswork.</h2>
        </div>
        <p>Start with a contested commitment. Leave with cited tradeoffs, a named choice, and proof of what reality did next.</p>
      </header>
      <div className="decision-room-utility-steps">
        <article>
          <b>1</b>
          <div><strong>Bring a contested decision</strong><span>Rollout, launch, pricing, packaging, or positioning commitment.</span></div>
        </article>
        <article>
          <b>2</b>
          <div><strong>Make the conflict visible</strong><span>Customer, usage, support, strategy, and feasibility evidence stay cited.</span></div>
        </article>
        <article>
          <b>3</b>
          <div><strong>Leave with a safer experiment</strong><span>Recommendation, guardrail, rollback path, and a receipt when reality changes.</span></div>
        </article>
      </div>
      <div className="decision-room-deliverables" aria-label="PM deliverables">
        <div className="decision-room-deliverables-heading">
          <span>What the PM leaves with</span>
          <small>Shareable, measurable, and reversible—not a vague AI opinion.</small>
        </div>
        <ul>
          <li><CheckCircle2 size={15} /><span><strong>Decision brief</strong><small>What changed and why now</small></span></li>
          <li><CheckCircle2 size={15} /><span><strong>Chosen response</strong><small>Tradeoffs compared side by side</small></span></li>
          <li><CheckCircle2 size={15} /><span><strong>Guardrail + rollback</strong><small>How to stop or reopen safely</small></span></li>
          <li><CheckCircle2 size={15} /><span><strong>Learning receipt</strong><small>What reality proved afterward</small></span></li>
        </ul>
      </div>
      <div className="decision-room-demo-footer">
        <small className="decision-room-demo-disclosure">This public lane uses a pinned, redacted decision case. The approval, outcome, and reopen loop is the same workflow a signed workspace uses with bounded sources.</small>
        {onOpenWorkflow && <button className="text-button decision-room-workspace-link" type="button" onClick={onOpenWorkflow}>Open source-connected workspace flow <ArrowRight size={14} /></button>}
      </div>
    </section>
    </>
  );

  const waitingForDecision = ["needs_approval", "reopened"].includes(decisionCase.status);
  const selectedOption = decisionCase.council.options.find((option) => option.option_id === selectedId);
  const recommendedOption = decisionCase.council.options.find((option) => option.option_id === decisionCase.council.recommendation);
  const councilVotes = new Set(decisionCase.council.positions.map((position) => position.recommendation)).size;
  const approvalLabel = selectedId === "segment" && !isProvidedIntake ? "Approve segmented experiment" : `Approve: ${optionTitle(decisionCase.council.options, selectedId)}`;
  return (
    <section className="decision-room" aria-labelledby="decision-room-title">
      <header className="decision-room-header">
        <div>
          <div className="decision-room-meta"><span>Decision Twin</span><span>Generation {decisionCase.generation}</span></div>
          <h2 id="decision-room-title" tabIndex="-1">{decisionCase.title}</h2>
          <p>{decisionCase.question}</p>
        </div>
        <div className="decision-room-header-actions"><button className="secondary compact" type="button" onClick={copyDecisionBrief}><span aria-live="polite">{copyStatus === "Copied" ? <Check size={14} /> : <Copy size={14} />}{copyStatus || "Copy decision brief"}</span></button>{isProvidedIntake && <button className="secondary compact" type="button" onClick={copyReturnLink}><span aria-live="polite">{linkStatus ? <Check size={14} /> : <Copy size={14} />}{linkStatus || "Copy view-only link"}</span></button>}{isProvidedIntake && canEdit && <button className="secondary compact" type="button" onClick={downloadPilotStarter} disabled={pilotExportStatus === "Preparing private starter…"}><Download size={14} /><span aria-live="polite">{pilotExportStatus || "Download private pilot starter"}</span></button>}<button className="secondary compact" type="button" onClick={resetDecision} disabled={Boolean(busy)}><RotateCcw size={14} />Back to overview</button></div>
      </header>
      {isProvidedIntake && <p className="decision-return-disclosure"><ShieldCheck size={13} />The copied link is view-only. This browser keeps a separate private edit capability for approval and measurements. Never enter secrets or customer-identifying data; the case expires under the deployment's bounded retention policy.</p>}
      {isProvidedIntake && canEdit && <p className="decision-return-disclosure"><ShieldCheck size={13} />The private pilot starter exports hashes and bounded counts—not your decision text, identity, consent, or a validation claim. Complete its manual fields only after a qualified session.</p>}
      {!canEdit && <p className="decision-return-disclosure"><ShieldCheck size={13} />Read-only shared view. Approval, measurements, and reopening require the originating browser's private edit capability.</p>}
      <nav className="decision-room-stages" aria-label="Decision Twin progress">
        {stages.map((stage, index) => <span className={index < activeStage ? "complete" : index === activeStage ? "current" : ""} key={stage}>
          {index < activeStage ? <CheckCircle2 size={15} /> : <b>{index + 1}</b>}{stage}{index < stages.length - 1 && <ArrowRight size={14} />}
        </span>)}
      </nav>
      {decisionCase.decision_debt && <section className={`decision-debt-radar ${decisionCase.decision_debt.state}`} aria-labelledby="decision-debt-title">
        <div className="decision-debt-radar-icon"><Radar size={21} /></div>
        <div className="decision-debt-radar-copy">
          <span>{decisionCase.decision_debt.detection_mode === "autonomous_monitor" ? "Autonomous decision inbox" : "PM-surfaced decision debt"}</span>
          <h3 id="decision-debt-title">{decisionCase.decision_debt.title}</h3>
          <p>{decisionCase.decision_debt.trigger}</p>
          <small><strong>Next:</strong> {decisionCase.decision_debt.recommended_next_step}</small>
        </div>
        <div className="decision-debt-radar-score" aria-label={`Decision debt score ${decisionCase.decision_debt.score} out of 100`}>
          <strong>{decisionCase.decision_debt.score}</strong><span>/100</span><small>{decisionCase.decision_debt.state.replaceAll("_", " ")}</small>
        </div>
        <dl>
          <div><dt>Commitment affected</dt><dd>{decisionCase.decision_debt.affected_commitment}</dd></div>
          <div><dt>Why now</dt><dd>{decisionCase.decision_debt.why_now}</dd></div>
          <div><dt>Still missing</dt><dd>{decisionCase.decision_debt.missing_evidence.length ? decisionCase.decision_debt.missing_evidence.join(" · ") : "No blocking evidence"}</dd></div>
          <div><dt>Compounding memory</dt><dd>{decisionCase.decision_debt_history?.length || 0} prior debt cycle{decisionCase.decision_debt_history?.length === 1 ? "" : "s"} preserved</dd></div>
        </dl>
      </section>}
      <ProductOperatingLoop loop={decisionCase.operating_loop} />
      <section className="decision-at-risk" aria-label="Decision at risk">
        <div><span>Current commitment</span><strong>{decisionCase.current_commitment}</strong></div>
        <div><span>Why this needs a decision now</span><p>{decisionCase.urgency}</p></div>
      </section>
      {recommendedOption && <section className="decision-recommendation-strip" aria-label="Council recommendation">
        <div className="decision-recommendation-heading"><CheckCircle2 size={18} /><span>Council recommendation</span><strong>{recommendedOption.title}</strong></div>
        <p>{recommendedOption.summary}</p>
        <span className="decision-recommendation-proof">5 bounded perspectives · disagreement preserved</span>
      </section>}
      <section className="decision-autonomy-proof" aria-label="What Driftline completed autonomously">
        <header><span>Completed before human approval</span><strong>{isProvidedIntake ? "Driftline structured your context without upgrading it to verified evidence." : "Driftline did the evidence work—not just the writing."}</strong></header>
        <div>
          <span><Database size={16} /><b>{decisionCase.evidence_nodes.length} cited {isProvidedIntake ? "inputs" : "signals"}</b><small>{isProvidedIntake ? "PM-provided · unverified" : "with source provenance"}</small></span>
          <span><Bot size={16} /><b>{decisionCase.council.positions.length} independent agents</b><small>{decisionCase.council.mode === "google_adk" ? "through Google ADK" : "bounded fallback"}</small></span>
          <span><GitCompareArrows size={16} /><b>{councilVotes} competing responses</b><small>dissent preserved</small></span>
          <span><ShieldCheck size={16} /><b>1 reversible plan</b><small>gated by a human</small></span>
        </div>
      </section>
      {decisionCase.precedents?.length > 0 && <section className="decision-memory-proof" aria-labelledby="decision-memory-title">
        <div className="decision-memory-icon"><History size={18} /></div>
        <div>
          <span>Decision memory</span>
          <h3 id="decision-memory-title">This decision has a precedent.</h3>
          <p>{decisionCase.precedents[0].lesson}</p>
        </div>
        <dl>
          <div><dt>Closest match</dt><dd>{decisionCase.precedents[0].title}</dd></div>
          <div><dt>Prior response</dt><dd>{optionTitle(decisionCase.council.options, decisionCase.precedents[0].chosen_response)}</dd></div>
          <div><dt>Match</dt><dd>{Math.round(decisionCase.precedents[0].similarity * 100)}% · {decisionCase.precedents[0].source_label}</dd></div>
        </dl>
      </section>}
      <EvidenceCouncil decisionCase={decisionCase} canEdit={canEdit} reviewingEvidenceId={reviewingEvidenceId} onReviewEvidence={reviewEvidence} />
      <CounterfactualCompare options={decisionCase.council.options} recommendedId={decisionCase.council.recommendation} selectedId={selectedId} onSelect={setSelectedId} />
      {waitingForDecision && canEdit && <section className="decision-approval-gate">
        <div>
          <div className="decision-approval-heading"><ClipboardCheck size={19} /><span>Human approval required</span></div>
          <h3>{decisionCase.status === "reopened" ? "The prior decision no longer holds" : "Turn the recommendation into bounded owner work"}</h3>
          <p>Driftline will record the choice, define success and stop conditions, and keep the rollback path attached. Agents cannot approve or publish it.</p>
          <ul className="decision-approval-outcomes">
            <li><FileCheck2 size={14} />A named decision record</li>
            <li><ShieldCheck size={14} />A measurable guardrail</li>
            <li><ArrowRight size={14} />A reversible experiment handoff</li>
          </ul>
        </div>
        <div className="decision-approver-control">
          <label htmlFor="decision-approver-name"><span>Human approver</span><input id="decision-approver-name" type="text" minLength="2" maxLength="120" autoComplete="name" value={approverName} onChange={(event) => setApproverName(event.target.value)} placeholder="Your name" /></label>
          <button className="primary" type="button" onClick={approve} disabled={Boolean(busy) || approverName.trim().length < 2}>
            {busy === "approval" ? <LoaderCircle className="spin" size={17} /> : <CheckCircle2 size={17} />}
            {busy === "approval" ? "Recording decision…" : approvalLabel}
          </button>
        </div>
      </section>}
      {decisionCase.status !== "needs_approval" && <LearningReceipt decisionCase={decisionCase} evaluation={evaluation} busy={Boolean(busy)} monitoring={monitoring} fixtureEligible={!isProvidedIntake} canEdit={canEdit} onOutcome={observeOutcome} onMeasuredOutcome={attachMeasurement} />}
      {busy === "outcome" && <p className="decision-room-status decision-room-status-bottom" role="status" aria-live="polite"><LoaderCircle className="spin" size={15} />Evaluating the guardrail and preserving the next generation.</p>}
      {error && <p className="decision-room-error" role="alert"><CircleAlert size={16} />{error}</p>}
      {selectedOption && waitingForDecision && <p className="decision-selection-note"><CheckCircle2 size={14} />Selected response: <strong>{selectedOption.title}</strong></p>}
    </section>
  );
}
