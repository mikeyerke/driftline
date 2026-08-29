import { BarChart3, CalendarClock, CheckCircle2, Headphones, Image, MessageSquareQuote, SearchCheck, ShieldQuestion, Users } from "lucide-react";

const evidenceIcons = {
  customer: MessageSquareQuote,
  support: Headphones,
  image: Image,
  metric: BarChart3,
  commitment: CalendarClock,
};

const titleCase = (value) => String(value || "").replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
const observedDate = (value) => new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeZone: "UTC" }).format(new Date(value));

function EvidenceCard({ node, canReview, reviewed, reviewing, onReview }) {
  const Icon = evidenceIcons[node.kind] || ShieldQuestion;
  return (
    <article className="decision-evidence-item" key={node.node_id}>
      <span className={`decision-evidence-icon ${node.kind}`}><Icon size={17} /></span>
      <div>
        <span className="decision-evidence-source">{titleCase(node.kind)} · {node.source_label} · observed {observedDate(node.observed_at)}</span>
        <strong>{node.title}</strong>
        <p>{node.excerpt}</p>
        {canReview && <button className={`evidence-review-button ${reviewed ? "reviewed" : ""}`} type="button" onClick={() => onReview(node.node_id)} disabled={reviewed || reviewing}>{reviewed ? <><CheckCircle2 size={14} />Reviewed</> : <><SearchCheck size={14} />{reviewing ? "Recording review…" : "Mark source reviewed"}</>}</button>}
      </div>
    </article>
  );
}

export default function EvidenceCouncil({ decisionCase, canEdit, reviewingEvidenceId, onReviewEvidence }) {
  const council = decisionCase.council;
  const isProvidedIntake = decisionCase.events.some((event) => event.source_mode === "pm_provided_unverified");
  const priorityKinds = ["metric", "support", "customer"];
  const primaryNodes = priorityKinds.map((kind) => decisionCase.evidence_nodes.find((node) => node.kind === kind)).filter(Boolean);
  const supportingNodes = decisionCase.evidence_nodes.filter((node) => !primaryNodes.some((primary) => primary.node_id === node.node_id));
  const harvest = decisionCase.operating_loop?.evidence_harvest;
  const decisionChannels = (harvest?.covered_channels || []).filter((channel) => channel !== "roadmap");
  const independentlyObserved = (harvest?.sources || []).filter((source) => source.mode === "connected_observed").length;
  const citedNodeIds = new Set([
    ...council.evidence_node_ids,
    ...council.positions.flatMap((position) => [...position.supporting_node_ids, ...position.contradicting_node_ids]),
    ...council.options.flatMap((option) => option.evidence_node_ids),
  ]);
  const currentReviews = (decisionCase.evidence_reviews || [])
    .filter((review) => review.generation === decisionCase.generation
      && review.evidence_manifest_hash === council.evidence_manifest_hash
      && review.synthesis_hash === council.synthesis_hash);
  const reviewedNodeIds = new Set(currentReviews.map((review) => review.evidence_node_id));
  const citedCount = citedNodeIds.size;
  const reviewedCount = [...citedNodeIds].filter((nodeId) => reviewedNodeIds.has(nodeId)).length;
  const reviewCompletedAt = decisionCase.generation === 1 && reviewedCount === citedCount && citedCount > 0
    ? Math.max(
      ...currentReviews
        .filter((review) => reviewedNodeIds.has(review.evidence_node_id))
        .map((review) => Date.parse(review.reviewed_at)),
    )
    : null;
  const minutesToReviewedBrief = Number.isFinite(reviewCompletedAt) && decisionCase.intake_completed_at
    ? Math.max(0, (reviewCompletedAt - Date.parse(decisionCase.intake_completed_at)) / 60000)
    : null;
  const timingLabel = Number.isFinite(minutesToReviewedBrief)
    ? `${minutesToReviewedBrief < 1 ? "<1" : Math.round(minutesToReviewedBrief)} min from complete intake`
    : null;
  const evidenceCard = (node) => <EvidenceCard node={node} key={node.node_id} canReview={isProvidedIntake && canEdit && citedNodeIds.has(node.node_id)} reviewed={reviewedNodeIds.has(node.node_id)} reviewing={reviewingEvidenceId === node.node_id} onReview={onReviewEvidence} />;
  return (
    <section className="decision-room-section evidence-council" aria-labelledby="evidence-council-title">
      <header className="decision-room-section-header">
        <div><span className="decision-room-kicker">Evidence snapshot</span><h3 id="evidence-council-title">{isProvidedIntake ? "Your decision-driving signals, kept honest" : "Three signals changed the decision"}</h3><p className="section-dek">{isProvidedIntake ? "These inputs shape the comparison, but remain explicitly unverified until a connected source corroborates them." : "Usage moved in opposite directions, while customer and support evidence explain why."}</p></div>
        <span className={`council-mode ${council.mode === "google_adk" ? "live" : "fixture"}`}>{council.mode === "google_adk" ? "Live evidence analysis" : isProvidedIntake ? "Provisional analysis" : "Pinned demo data"}</span>
      </header>
      <div className="decision-evidence-grid priority">
        {primaryNodes.map(evidenceCard)}
      </div>
      {isProvidedIntake && <section className="evidence-corroboration" aria-labelledby="evidence-corroboration-title">
        <div className="evidence-review-summary"><SearchCheck size={16} /><span><strong>Source review: {reviewedCount} of {citedCount}</strong><small>{reviewedCount === citedCount && citedCount > 0 ? `Every cited source has a capability-bound review receipt${timingLabel ? ` · ${timingLabel}` : ""}.` : "Open each cited source and mark it reviewed before making a validation claim."}</small></span></div>
        <div className="evidence-pack-summary"><span><strong>{decisionCase.evidence_nodes.length - 1} separately cited signals</strong><small>{decisionChannels.length} evidence channels captured</small></span><b>{independentlyObserved} independently observed</b></div>
        <header>
          <div><SearchCheck size={19} /><span><strong id="evidence-corroboration-title">Evidence readiness: 0 of 3 checks corroborated</strong><small>Driftline can structure the call now. These checks turn it into a defensible operating decision.</small></span></div>
          <b>Next best evidence</b>
        </header>
        <ol>
          <li><BarChart3 size={16} /><span><strong>Quantify the segment split</strong><small>Compare the primary outcome and one guardrail against baseline.</small></span></li>
          <li><MessageSquareQuote size={16} /><span><strong>Corroborate the risk theme</strong><small>Confirm it across customer calls, support themes, or research notes.</small></span></li>
          <li><Users size={16} /><span><strong>Verify owner feasibility</strong><small>Name the rollout owner, stop authority, and rollback window.</small></span></li>
        </ol>
        <p><CheckCircle2 size={14} />The recommendation stays provisional until connected evidence replaces the PM-provided inputs.</p>
      </section>}
      <div className="council-conflict"><ShieldQuestion size={20} /><div><strong>The useful disagreement</strong><p>{council.decisive_conflict}</p></div></div>
      <details className="council-reasoning">
        <summary>Open full evidence and detailed reasoning <span>{decisionCase.evidence_nodes.length} sources · {council.positions.length} perspectives</span></summary>
        {supportingNodes.length > 0 && <div className="decision-evidence-grid supporting">{supportingNodes.map(evidenceCard)}</div>}
        <div className="council-position-list" aria-label="Product council positions">
          {council.positions.map((position) => (
            <details className={`council-position ${position.role === "challenger" ? "challenger" : ""}`} key={position.role}>
              <summary><span className="council-role">{titleCase(position.role)}</span><span className={`council-vote ${position.recommendation}`}>{titleCase(position.recommendation)}</span><span>{position.thesis}</span></summary>
              <div><strong>Risk</strong><p>{position.risks.join(" · ")}</p><strong>Would change this position</strong><p>{position.would_change_mind_if}</p></div>
            </details>
          ))}
        </div>
      </details>
    </section>
  );
}
