import { AlertTriangle, ArrowRight, Bot, CheckCircle2, Clock3, GitBranch, Link2, RefreshCw, ShieldCheck, Sparkles } from "lucide-react";

const lanes = [
  ["needs_decision", "Needs your decision", "Driftline prepared the evidence; authority stays with you."],
  ["outcomes_to_review", "Unexpected outcomes", "Measured results crossed a review or reopen boundary."],
  ["commitments_at_risk", "Commitments at risk", "High-materiality changes connected to active owner work."],
  ["important_changes", "Important changes", "New findings promoted above the monitoring noise."],
];

function percentage(value) {
  const number = Number(value);
  return Number.isFinite(number) ? `${Math.round(number * 100)}%` : "—";
}

function DecisionCard({ item, onReview }) {
  return (
    <article className={`decision-inbox-card severity-${item.severity}`}>
      <header>
        <div className="decision-inbox-card-title">
          <span className="decision-inbox-attention"><AlertTriangle size={14} />{item.attention}</span>
          <h4>{item.title}</h4>
        </div>
        <span className="decision-inbox-score" aria-label={`Materiality ${item.materiality_score} out of 100`}><strong>{item.materiality_score}</strong><small>materiality</small></span>
      </header>
      <div className="decision-inbox-finding"><span>New finding</span><p>{item.what_changed}</p></div>
      <p className="decision-inbox-why"><strong>Why it matters</strong>{item.why_it_matters}</p>
      <dl className="decision-inbox-facts">
        <div><dt>Commitment</dt><dd>{item.commitments?.[0] || "Owner review"}{item.commitments?.length > 1 ? ` +${item.commitments.length - 1}` : ""}</dd></div>
        <div><dt>Owner</dt><dd>{item.owners?.[0] || "Unassigned"}{item.owners?.length > 1 ? ` +${item.owners.length - 1}` : ""}</dd></div>
        <div><dt>Decision window</dt><dd><Clock3 size={13} />{item.decision_window}</dd></div>
        <div><dt>Evidence confidence</dt><dd>{percentage(item.confidence)}</dd></div>
      </dl>
      <div className="decision-inbox-automation"><Bot size={16} /><div><strong>Prepared for you</strong><span>{item.automation?.completed?.join(" · ")}</span></div></div>
      <footer>
        <div className="decision-inbox-links">
          <span><Link2 size={13} />{item.relationship_summary}</span>
          {item.duplicate_observations_collapsed > 0 && <span><CheckCircle2 size={13} />{item.duplicate_observations_collapsed} repeat {item.duplicate_observations_collapsed === 1 ? "signal" : "signals"} collapsed</span>}
        </div>
        <button className="primary compact" type="button" onClick={() => onReview(item)}>Review decision<ArrowRight size={15} /></button>
      </footer>
    </article>
  );
}

export default function DecisionInbox({ inbox, loading, error, onRefresh, onReview, onStart }) {
  const items = inbox?.items || [];
  const summary = inbox?.summary || {};
  const findings = inbox?.findings || [];
  const quietItems = items.filter((item) => item.lane === "monitoring_normally");
  const hasObservedWork = inbox?.mode === "observed_workflows";
  return (
    <section id="inbox-section" className="decision-inbox" aria-labelledby="decision-inbox-title">
      <header className="decision-inbox-header">
        <div><span className="decision-inbox-eyebrow"><Sparkles size={14} />Decision inbox</span><h2 id="decision-inbox-title">What needs your attention</h2><p>Driftline monitors, clusters, and prepares the work. You decide what changes.</p></div>
        <button className="secondary compact" type="button" onClick={onRefresh} disabled={loading}><RefreshCw size={15} className={loading ? "spin" : ""} />{loading ? "Refreshing" : "Refresh"}</button>
      </header>
      {error && <div className="decision-inbox-error" role="status"><AlertTriangle size={16} />{error}</div>}
      <div className="decision-inbox-summary" aria-label="Decision portfolio summary">
        <div className="attention"><strong>{summary.requires_attention || 0}</strong><span>Need attention</span><small>Only material work is promoted</small></div>
        <div><strong>{summary.monitoring_quietly || 0}</strong><span>Quietly monitored</span><small>No PM interruption</small></div>
        <div><strong>{summary.duplicate_observations_collapsed || 0}</strong><span>Repeats collapsed</span><small>One thread, not duplicate alerts</small></div>
        <div><strong>{summary.linked_decisions || 0}</strong><span>Linked decisions</span><small>Shared commitments surfaced</small></div>
      </div>
      {findings.length > 0 && <section className="decision-inbox-findings" aria-labelledby="portfolio-findings-title"><header><div><span><Sparkles size={14} />Portfolio intelligence</span><h3 id="portfolio-findings-title">What Driftline found across decisions</h3></div><small>Observed records · bounded window</small></header><div>{findings.map((finding) => <article key={finding.kind}><strong>{finding.title}</strong><p>{finding.finding}</p><span>{finding.recommended_response}</span><small>Sample: {finding.sample_size}</small></article>)}</div></section>}
      {!loading && !hasObservedWork && <div className="decision-inbox-empty"><span><GitBranch size={22} /></span><div><strong>Your decision portfolio is quiet</strong><p>No observed workflow currently needs attention in this lane. Run a source review to create the first evidence-bound decision thread.</p></div><button className="primary" type="button" onClick={onStart}>Analyze a change<ArrowRight size={16} /></button></div>}
      {hasObservedWork && lanes.map(([lane, title, description]) => {
        const laneItems = items.filter((item) => item.lane === lane);
        if (!laneItems.length) return null;
        return <section className="decision-inbox-lane" key={lane} aria-labelledby={`inbox-${lane}`}><header><div><h3 id={`inbox-${lane}`}>{title}</h3><p>{description}</p></div><span>{laneItems.length}</span></header><div className="decision-inbox-list">{laneItems.map((item) => <DecisionCard key={item.decision_id} item={item} onReview={onReview} />)}</div></section>;
      })}
      {quietItems.length > 0 && <details className="decision-inbox-quiet"><summary><span><CheckCircle2 size={16} />Monitoring normally</span><strong>{quietItems.length} hidden from your active queue</strong></summary><div>{quietItems.map((item) => <span key={item.decision_id}><b>{item.title}</b>{item.next_action}</span>)}</div></details>}
      <aside className="decision-inbox-boundary">
        <div><Bot size={19} /><span><strong>Automated for you</strong>Monitor sources, deduplicate signals, score materiality, connect commitments, prepare next steps, and flag reopen candidates.</span></div>
        <div><ShieldCheck size={19} /><span><strong>Reserved for you</strong>Approve, dismiss, revise commitments, authorize external writes, and publish customer-facing claims.</span></div>
      </aside>
    </section>
  );
}
