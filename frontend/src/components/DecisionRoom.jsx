import { ArrowRight, BrainCircuit, CheckCircle2, CircleAlert, LoaderCircle, Play, Sparkles } from "lucide-react";
import { useEffect, useState } from "react";
import { approveDecisionTwin, getDecisionTwinEvaluation, recordDecisionTwinOutcome, startDecisionTwin } from "../api";
import CounterfactualCompare from "./CounterfactualCompare";
import EvidenceCouncil from "./EvidenceCouncil";
import LearningReceipt from "./LearningReceipt";

const stages = ["Evidence", "Council", "Decide", "Learn"];

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
      <div className="decision-room-hero-copy"><span className="decision-room-kicker"><Sparkles size={14} />Decision Twin · PM operating loop</span><h2 id="decision-room-hero-title">Know when a product decision stopped being true.</h2><p>Driftline turns customer evidence, product usage, interface screenshots, support themes, and roadmap commitments into one falsifiable decision—and reopens it when the outcome breaks the original assumption.</p><div className="decision-room-hero-actions"><button className="primary decision-room-run" type="button" onClick={runCouncil} disabled={Boolean(busy)}>{busy ? <LoaderCircle className="spin" size={18} /> : <Play size={18} />}{busy ? "Running Product Council…" : "Run the Product Council"}</button><span>One case · five bounded perspectives · human authority</span></div>{error && <p className="decision-room-error" role="alert"><CircleAlert size={16} />{error}</p>}</div>
      <div className="decision-room-promise"><BrainCircuit size={28} /><strong>Not another feedback summary</strong><span>Evidence → disagreement → counterfactual → reversible experiment → measured learning</span><div><span>Gemini 3.5+</span><span>Google ADK</span><span>Cloud Run</span><span>Firestore</span><span>BigQuery-ready</span></div></div>
    </section>
  );

  const waitingForDecision = ["needs_approval", "reopened"].includes(decisionCase.status);
  return (
    <section className="decision-room" aria-labelledby="decision-room-title">
      <header className="decision-room-header">
        <div><span className="decision-room-kicker"><Sparkles size={14} />Decision Twin · generation {decisionCase.generation}</span><h2 id="decision-room-title">{decisionCase.title}</h2><p>{decisionCase.question}</p></div>
        <button className="secondary compact" type="button" onClick={runCouncil} disabled={Boolean(busy)}>Reset demo</button>
      </header>
      <nav className="decision-room-stages" aria-label="Decision Twin progress">{stages.map((stage, index) => <span className={index < activeStage ? "complete" : index === activeStage ? "current" : ""} key={stage}>{index < activeStage ? <CheckCircle2 size={15} /> : <b>{index + 1}</b>}{stage}{index < stages.length - 1 && <ArrowRight size={14} />}</span>)}</nav>
      <section className="decision-at-risk"><div><span>Decision at risk</span><strong>{decisionCase.current_commitment}</strong></div><p>{decisionCase.urgency}</p></section>
      <EvidenceCouncil decisionCase={decisionCase} />
      <CounterfactualCompare options={decisionCase.council.options} recommendedId={decisionCase.council.recommendation} selectedId={selectedId} onSelect={setSelectedId} />
      {waitingForDecision && <section className="decision-approval-gate"><div><span className="decision-room-kicker">Human authority</span><h3>{decisionCase.status === "reopened" ? "The prior decision no longer holds" : "Approve one reversible learning plan"}</h3><p>The agents can recommend and challenge. They cannot approve, publish, or change a product system.</p></div><button className="primary" type="button" onClick={approve} disabled={Boolean(busy)}>{busy === "approval" ? <LoaderCircle className="spin" size={17} /> : <CheckCircle2 size={17} />}{busy === "approval" ? "Recording decision…" : `Approve ${selectedId}`}</button></section>}
      {decisionCase.status !== "needs_approval" && <LearningReceipt decisionCase={decisionCase} evaluation={evaluation} busy={Boolean(busy)} onOutcome={observeOutcome} />}
      {error && <p className="decision-room-error" role="alert"><CircleAlert size={16} />{error}</p>}
    </section>
  );
}
