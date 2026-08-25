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
      setEvaluation(null);
      setSelectedId(next.council.recommendation);
    } catch (nextError) { setError(nextError.message); } finally { setBusy(""); }
  };

  const approve = async () => {
    setBusy("approval"); setError("");
    try {
      setDecisionCase(await approveDecisionTwin(decisionCase.case_id, selectedId, decisionCase.council.synthesis_hash, decisionCase.generation));
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
    <>
    <section className="decision-room-hero" aria-labelledby="decision-room-hero-title">
      <div className="decision-room-hero-copy">
        <div className="decision-room-kicker">Driftline Decision Twin <span>for product decisions</span></div>
        <h2 id="decision-room-hero-title">Catch when new evidence invalidates a roadmap decision.</h2>
        <p>Driftline connects customer signals, usage movement, support themes, and product commitments so a PM can choose the smallest safe response, then prove what happened next.</p>
        <div className="decision-room-case-preview" aria-label="Live decision in this demo">
          <span>Live decision in this demo</span>
          <strong>Should the onboarding redesign ship to every workspace next week?</strong>
          <small>Enterprise activation is down while the rollout commitment is seven days away.</small>
        </div>
        <div className="decision-room-reusable-scope" aria-label="Reusable decision types">
          <span>Same loop for</span>
          <b>Rollouts</b><b>Launches</b><b>Pricing</b><b>Packaging</b>
        </div>
        <div className="decision-room-hero-actions">
          <button className="primary decision-room-run" type="button" onClick={runCouncil} disabled={Boolean(busy)} aria-busy={busy === "council"}>
            {busy ? <LoaderCircle className="spin" size={18} /> : <Play size={18} />}
            {busy ? "Reading the decision evidence…" : "Review the onboarding decision"}
          </button>
          <span>One decision · five bounded perspectives · human approval</span>
        </div>
        {busy === "council" && <p className="decision-room-status" role="status" aria-live="polite"><LoaderCircle className="spin" size={15} />Checking evidence, disagreement, and reversible options.</p>}
        {error && <p className="decision-room-error" role="alert"><CircleAlert size={16} />{error}</p>}
      </div>
      <div className="decision-room-promise decision-room-risk-card">
        <div className="decision-room-risk-heading"><span><ShieldCheck size={18} />Decision at risk</span><strong>7 days to rollout</strong></div>
        <h3>Onboarding redesign</h3>
        <p>Small-workspace activation improved <b className="decision-positive">+9%</b>, while enterprise activation fell <b className="decision-negative">-11%</b>.</p>
        <dl className="decision-room-risk-facts">
          <div><dt>Driftline finds</dt><dd>Segment conflict, not a global answer</dd></div>
          <div><dt>PM receives</dt><dd>Recommendation, guardrail, and rollback</dd></div>
        </dl>
        <div className="decision-room-safe-note"><ShieldCheck size={15} />No external writes before approval</div>
      </div>
    </section>
    <section className="decision-room-utility-bridge" aria-labelledby="decision-room-utility-title">
      <header>
        <div>
          <span className="decision-room-bridge-kicker">The PM utility</span>
          <h2 id="decision-room-utility-title">One decision loop, not another dashboard.</h2>
        </div>
        <p>Start with the decision you need to defend. Leave with a bounded experiment your team can execute and revisit.</p>
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
      <small className="decision-room-demo-disclosure">This public lane uses a pinned, redacted decision case. The approval, outcome, and reopen loop is the same workflow a signed workspace uses with bounded sources.</small>
    </section>
    </>
  );

  const waitingForDecision = ["needs_approval", "reopened"].includes(decisionCase.status);
  const selectedOption = decisionCase.council.options.find((option) => option.option_id === selectedId);
  const recommendedOption = decisionCase.council.options.find((option) => option.option_id === decisionCase.council.recommendation);
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
      {recommendedOption && <section className="decision-recommendation-strip" aria-label="Council recommendation">
        <div className="decision-recommendation-heading"><CheckCircle2 size={18} /><span>Council recommendation</span><strong>{recommendedOption.title}</strong></div>
        <p>{decisionCase.council.executive_summary}</p>
        <span className="decision-recommendation-proof">5 bounded perspectives · disagreement preserved</span>
      </section>}
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
