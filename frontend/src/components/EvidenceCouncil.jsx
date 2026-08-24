import { BarChart3, CalendarClock, Headphones, Image, MessageSquareQuote, ShieldQuestion } from "lucide-react";

const evidenceIcons = {
  customer: MessageSquareQuote,
  support: Headphones,
  image: Image,
  metric: BarChart3,
  commitment: CalendarClock,
};

const titleCase = (value) => String(value || "").replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());

export default function EvidenceCouncil({ decisionCase }) {
  const council = decisionCase.council;
  return (
    <section className="decision-room-section evidence-council" aria-labelledby="evidence-council-title">
      <header className="decision-room-section-header">
        <div><span className="decision-room-kicker">What the evidence says</span><h3 id="evidence-council-title">Five perspectives, one disagreement</h3></div>
        <span className={`council-mode ${council.mode === "google_adk" ? "live" : "fixture"}`}>{council.mode === "google_adk" ? "Live ADK" : "Pinned demo"}</span>
      </header>
      <div className="decision-evidence-grid">
        {decisionCase.evidence_nodes.map((node) => {
          const Icon = evidenceIcons[node.kind] || ShieldQuestion;
          return (
            <article className="decision-evidence-item" key={node.node_id}>
              <span className={`decision-evidence-icon ${node.kind}`}><Icon size={17} /></span>
              <div><span className="decision-evidence-source">{titleCase(node.kind)} · {node.source_label}</span><strong>{node.title}</strong><p>{node.excerpt}</p></div>
            </article>
          );
        })}
      </div>
      <div className="council-conflict"><ShieldQuestion size={20} /><div><strong>Where they disagree</strong><p>{council.decisive_conflict}</p></div></div>
      <div className="council-position-list" aria-label="Decision perspectives">
        {council.positions.map((position) => (
          <details className={`council-position ${position.role === "challenger" ? "challenger" : ""}`} key={position.role}>
            <summary><span className="council-role">{titleCase(position.role)}</span><span className={`council-vote ${position.recommendation}`}>{titleCase(position.recommendation)}</span><span>{position.thesis}</span></summary>
            <div><strong>Risk</strong><p>{position.risks.join(" · ")}</p><strong>Would change this position</strong><p>{position.would_change_mind_if}</p></div>
          </details>
        ))}
      </div>
    </section>
  );
}
