import { BarChart3, CalendarClock, Headphones, Image, MessageSquareQuote, ShieldQuestion } from "lucide-react";

const evidenceIcons = {
  customer: MessageSquareQuote,
  support: Headphones,
  image: Image,
  metric: BarChart3,
  commitment: CalendarClock,
};

const titleCase = (value) => String(value || "").replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());

function EvidenceCard({ node }) {
  const Icon = evidenceIcons[node.kind] || ShieldQuestion;
  return (
    <article className="decision-evidence-item" key={node.node_id}>
      <span className={`decision-evidence-icon ${node.kind}`}><Icon size={17} /></span>
      <div>
        <span className="decision-evidence-source">{titleCase(node.kind)} · {node.source_label}</span>
        <strong>{node.title}</strong>
        <p>{node.excerpt}</p>
      </div>
    </article>
  );
}

export default function EvidenceCouncil({ decisionCase }) {
  const council = decisionCase.council;
  const isProvidedIntake = decisionCase.events.some((event) => event.source_mode === "pm_provided_unverified");
  const priorityKinds = ["metric", "support", "customer"];
  const primaryNodes = priorityKinds.map((kind) => decisionCase.evidence_nodes.find((node) => node.kind === kind)).filter(Boolean);
  const supportingNodes = decisionCase.evidence_nodes.filter((node) => !primaryNodes.some((primary) => primary.node_id === node.node_id));
  return (
    <section className="decision-room-section evidence-council" aria-labelledby="evidence-council-title">
      <header className="decision-room-section-header">
        <div><span className="decision-room-kicker">Evidence snapshot</span><h3 id="evidence-council-title">{isProvidedIntake ? "Your decision-driving signals, kept honest" : "Three signals changed the decision"}</h3><p className="section-dek">{isProvidedIntake ? "These inputs shape the comparison, but remain explicitly unverified until a connected source corroborates them." : "Usage moved in opposite directions, while customer and support evidence explain why."}</p></div>
        <span className={`council-mode ${council.mode === "google_adk" ? "live" : "fixture"}`}>{council.mode === "google_adk" ? "Live Google ADK" : isProvidedIntake ? "Bounded fallback" : "Pinned demo data"}</span>
      </header>
      <div className="decision-evidence-grid priority">
        {primaryNodes.map((node) => <EvidenceCard node={node} key={node.node_id} />)}
      </div>
      <div className="council-conflict"><ShieldQuestion size={20} /><div><strong>The useful disagreement</strong><p>{council.decisive_conflict}</p></div></div>
      <details className="council-reasoning">
        <summary>Open full evidence and five council positions <span>{decisionCase.evidence_nodes.length} sources · {council.positions.length} perspectives</span></summary>
        {supportingNodes.length > 0 && <div className="decision-evidence-grid supporting">{supportingNodes.map((node) => <EvidenceCard node={node} key={node.node_id} />)}</div>}
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
