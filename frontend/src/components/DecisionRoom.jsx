import { ArrowRight, BrainCircuit, CheckCircle2, CircleAlert, LoaderCircle, Play, Sparkles } from "lucide-react";
import { useEffect, useState } from "react";
import { approveDecisionTwin, getDecisionTwinEvaluation, recordDecisionTwinOutcome, startDecisionTwin } from "../api";
import CounterfactualCompare from "./CounterfactualCompare";
import EvidenceCouncil from "./EvidenceCouncil";
import LearningReceipt from "./LearningReceipt";

const stages = ["Evidence", "Perspectives", "Choose", "Learn"];

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
      setDecisionCase(await approveDecisionTwin(
        decisionCase.case_id,
        selectedId,
        decisionCase.council.synthesis_hash,
        decisionCase.generation,
      ));
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
      <div className="decision-room-hero-copy"><span className="decision-room-kicker"><Sparkles size={14} />Decision Twin</span><h2 id="decision-room-hero-title">Know when a product decision stopped being true.</h2><p>Driftline brings customer, usage, support, screenshot, and roadmap evidence into one decision. You choose what to do; a later result can reopen the call.</p><div className="decision-room-hero-actions"><button className="primary decision-room-run" type="button" onClick={runCouncil} disabled={Boolean(busy)}>{busy ? <LoaderCircle className="spin" size={18} /> : <Play size={18} />}{busy ? "Running the council…" : "Run the council"}</button><span>One case · five perspectives · your decision</span></div>{error && <p className="decision-room-error" role="alert"><CircleAlert size={16} />{error}</p>}</div>
      <div className="decision-room-promise"><BrainCircuit size={28} /><strong>A decision that can learn</strong><span>See the evidence, compare the perspectives, choose a plan, and check what happened.</span><div><span>Gemini + Google ADK</span><span>Google Cloud</span><span>Human approval</span></div></div>
    </section>
  );

  const waitingForDecision = ["needs_approval", "reopened"].includes(decisionCase.status);
  const selectedOption = decisionCase.council.options.find((option) => option.option_id === selectedId);
  return (
    <section className="decision-room" aria-labelledby="decision-room-title">
      <header className="decision-room-header">
        <div><span className="decision-room-kicker"><Sparkles size={14} />Decision Twin · round {decisionCase.generation}</span><h2 id="decision-room-title">{decisionCase.title}</h2><p>{decisionCase.question}</p></div>
        <button className="secondary compact" type="button" onClick={runCouncil} disabled={Boolean(busy)}>Start over</button>
      </header>
      <nav className="decision-room-stages" aria-label="Decision Twin progress">{stages.map((stage, index) => <span className={index < activeStage ? "complete" : index === activeStage ? "current" : ""} key={stage}>{index < activeStage ? <CheckCircle2 size={15} /> : <b>{index + 1}</b>}{stage}{index < stages.length - 1 && <ArrowRight size={14} />}</span>)}</nav>
      <section className="decision-at-risk"><div><span>Decision at risk</span><strong>{decisionCase.current_commitment}</strong></div><p>{decisionCase.urgency}</p></section>
      <EvidenceCouncil decisionCase={decisionCase} />
      <CounterfactualCompare options={decisionCase.council.options} recommendedId={decisionCase.council.recommendation} selectedId={selectedId} onSelect={setSelectedId} />
      {waitingForDecision && <section className="decision-approval-gate"><div><span className="decision-room-kicker">Your decision</span><h3>{decisionCase.status === "reopened" ? "New evidence needs a call" : "Choose a plan"}</h3><p>The AI can recommend and challenge. You decide, and nothing changes until you approve.</p></div><button className="primary" type="button" onClick={approve} disabled={Boolean(busy)}>{busy === "approval" ? <LoaderCircle className="spin" size={17} /> : <CheckCircle2 size={17} />}{busy === "approval" ? "Saving your choice…" : `Approve: ${selectedOption?.title || "selected plan"}`}</button></section>}
      {decisionCase.status !== "needs_approval" && <LearningReceipt decisionCase={decisionCase} evaluation={evaluation} busy={Boolean(busy)} onOutcome={observeOutcome} />}
      {error && <p className="decision-room-error" role="alert"><CircleAlert size={16} />{error}</p>}
    </section>
  );
}
