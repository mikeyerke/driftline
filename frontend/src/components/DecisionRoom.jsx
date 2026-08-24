import { ArrowRight, CheckCircle2, CircleAlert, ClipboardCheck, FileCheck2, LoaderCircle, Play, RotateCcw, ShieldCheck } from "lucide-react";
import { useEffect, useState } from "react";
import { approveDecisionTwin, getDecisionTwinEvaluation, recordDecisionTwinOutcome, startDecisionTwin } from "../api";
import CounterfactualCompare from "./CounterfactualCompare";
import EvidenceCouncil from "./EvidenceCouncil";
import LearningReceipt from "./LearningReceipt";

const stages = ["Detect drift", "Compare options", "Approve action", "Learn"];

const optionTitle = (options, id) => options.find((option) => option.option_id === id)?.title || id;

export default function DecisionRoom() {
  const [decisionCase, setDecisionCase] = useState(null);
  const [selectedId, setSelectedId] = useState("segment");
  const [evaluation, setEvaluation] = useState(null);
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    if (!decisionCase?.case_id) return;
    getDecisionTwinEvaluation(decisionCase.case_id).then(setEvaluation).catch(() => setEvaluation(null));
  }, [decisionCase]);

  const runCouncil = async () => {
    setBusy("council"); setError("");
    try {
      const next = await startDecisionTwin();
      setDecisionCase(next);
      setSelectedId(next.council.recommendation);
    } catch (nextError) { setError(nextError.message); } finally { setBusy(""); }
  };

  const approve = async () => {
    setBusy("approval"); setError("");
    try {
      setDecisionCase(await approveDecisionTwin(decisionCase.case_id, selectedId, decisionCase.council.synthesis_hash));
    } catch (nextError) { setError(nextError.message); } finally { setBusy(""); }
  };

  const observeOutcome = async () => {
    setBusy("outcome"); setError("");
    try {
      setDecisionCase(await recordDecisionTwinOutcome(decisionCase.case_id, decisionCase.generation));
    } catch (nextError) { setError(nextError.message); } finally { setBusy(""); }
  };

  const activeStage = !decisionCase ? 0 : decisionCase.status === "needs_approval" || decisionCase.status === "reopened" ? 2 : 3;

  if (!decisionCase) return (
    <section className="decision-room-hero" aria-labelledby="decision-room-hero-title">
      <div className="decision-room-hero-copy">
        <h2 id="decision-room-hero-title">Catch when new evidence invalidates a roadmap decision.</h2>
        <p>Driftline connects customer signals, usage movement, support themes, and product commitments so a PM can choose the smallest safe response—and prove what happened next.</p>
        <div className="decision-room-hero-actions">
          <button className="primary decision-room-run" type="button" onClick={runCouncil} disabled={Boolean(busy)}>
            {busy ? <LoaderCircle className="spin" size={18} /> : <Play size={18} />}
            {busy ? "Reading the decision evidence…" : "Open the onboarding decision"}
          </button>
          <span>One decision · five bounded perspectives · human approval</span>
        </div>
        {busy === "council" && <p className="decision-room-status" role="status" aria-live="polite"><LoaderCircle className="spin" size={15} />Checking evidence, disagreement, and reversible options.</p>}
        {error && <p className="decision-room-error" role="alert"><CircleAlert size={16} />{error}</p>}
      </div>
      <div className="decision-room-promise">
        <div className="decision-room-proof-title"><ShieldCheck size={22} /><strong>A PM decision loop, not another dashboard</strong></div>
        <p>Detect drift, compare the counterfactuals, approve bounded owner work, and reopen the decision when a guardrail breaks.</p>
        <ol className="decision-room-proof-steps">
          <li><b>1</b><span><strong>Detect drift</strong><small>Evidence stops a stale commitment.</small></span></li>
          <li><b>2</b><span><strong>Choose safely</strong><small>Options show risks, guardrails, and rollback.</small></span></li>
          <li><b>3</b><span><strong>Learn</strong><small>Outcomes preserve the decision lineage.</small></span></li>
        </ol>
        <details className="decision-technical-proof"><summary>Google Cloud proof</summary><p>Gemini + Google ADK provide bounded council perspectives; Cloud Run, Firestore, and BigQuery preserve the production trail.</p></details>
      </div>
    </section>
  );

  const waitingForDecision = ["needs_approval", "reopened"].includes(decisionCase.status);
  const selectedOption = decisionCase.council.options.find((option) => option.option_id === selectedId);
  const approvalLabel = selectedId === "segment" ? "Approve segmented experiment" : `Approve ${optionTitle(decisionCase.council.options, selectedId).toLowerCase()}`;
  return (
    <section className="decision-room" aria-labelledby="decision-room-title">
      <header className="decision-room-header">
        <div>
          <div className="decision-room-meta"><span>Decision Twin</span><span>Generation {decisionCase.generation}</span></div>
          <h2 id="decision-room-title">{decisionCase.title}</h2>
          <p>{decisionCase.question}</p>
        </div>
        <button className="secondary compact" type="button" onClick={runCouncil} disabled={Boolean(busy)}><RotateCcw size={14} />Start over</button>
      </header>
      <nav className="decision-room-stages" aria-label="Decision Twin progress">
        {stages.map((stage, index) => <span className={index < activeStage ? "complete" : index === activeStage ? "current" : ""} key={stage}>
          {index < activeStage ? <CheckCircle2 size={15} /> : <b>{index + 1}</b>}{stage}{index < stages.length - 1 && <ArrowRight size={14} />}
        </span>)}
      </nav>
      <section className="decision-at-risk" aria-label="Decision at risk">
        <div><span>Current commitment</span><strong>{decisionCase.current_commitment}</strong></div>
        <div><span>Why this needs a decision now</span><p>{decisionCase.urgency}</p></div>
      </section>
      <EvidenceCouncil decisionCase={decisionCase} />
      <CounterfactualCompare options={decisionCase.council.options} recommendedId={decisionCase.council.recommendation} selectedId={selectedId} onSelect={setSelectedId} />
      {waitingForDecision && <section className="decision-approval-gate">
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
        <button className="primary" type="button" onClick={approve} disabled={Boolean(busy)}>
          {busy === "approval" ? <LoaderCircle className="spin" size={17} /> : <CheckCircle2 size={17} />}
          {busy === "approval" ? "Recording decision…" : approvalLabel}
        </button>
      </section>}
      {decisionCase.status !== "needs_approval" && <LearningReceipt decisionCase={decisionCase} evaluation={evaluation} busy={Boolean(busy)} onOutcome={observeOutcome} />}
      {busy === "outcome" && <p className="decision-room-status decision-room-status-bottom" role="status" aria-live="polite"><LoaderCircle className="spin" size={15} />Evaluating the guardrail and preserving the next generation.</p>}
      {error && <p className="decision-room-error" role="alert"><CircleAlert size={16} />{error}</p>}
      {selectedOption && waitingForDecision && <p className="decision-selection-note"><CheckCircle2 size={14} />Selected response: <strong>{selectedOption.title}</strong></p>}
    </section>
  );
}
