import { ArrowRight, Check, CircleDot, FileCheck2, Globe2, Layers3, Link2, Radio, Target, UsersRound } from "lucide-react";

const kindMeta = {
  source: { label: "Observed change", icon: Globe2, tone: "source" },
  offering: { label: "Offering", icon: Target, tone: "offering" },
  domain: { label: "Business impact", icon: Layers3, tone: "domain" },
  artifact: { label: "Work surface", icon: FileCheck2, tone: "artifact" },
  system: { label: "Handoff", icon: Link2, tone: "system" },
};

function GraphNode({ node }) {
  const meta = kindMeta[node.kind] || kindMeta.artifact;
  const Icon = meta.icon;
  return (
    <div className={`impact-graph-node ${meta.tone}`}>
      <span className="impact-graph-icon"><Icon size={15} /></span>
      <span className="impact-graph-copy"><strong>{node.label}</strong><small>{node.meta}</small></span>
      {node.risk && <span className={`impact-graph-risk ${node.risk}`}>{node.risk}</span>}
    </div>
  );
}

export default function ImpactMap({ items, graph, approved, sourceName, sourceCategory }) {
  const nodes = graph?.nodes || [];
  const columns = ["source", "offering", "domain", "artifact", "system"].map((kind) => ({
    kind,
    nodes: nodes.filter((node) => node.kind === kind),
  })).filter((column) => column.nodes.length);
  const summary = graph?.summary || {};
  const previewOffering = sourceCategory === "Competitor pricing"
    ? "Competitor Pro plan"
    : sourceCategory === "Competitor offering"
      ? "Competitor Business plan"
      : sourceCategory === "Competitor narrative"
        ? "Competitor product narrative"
        : "Enterprise plan";
  const previewChangeType = sourceCategory === "Competitor pricing"
    ? "Competitive pricing move"
    : sourceCategory === "Competitor offering"
      ? "Product capability change"
      : sourceCategory === "Competitor narrative"
        ? "Market narrative change"
        : "Pricing and packaging";
  const fallbackNodes = [
    { id: "source", kind: "source", label: sourceName || "Public pricing page", meta: "Verified source change" },
    { id: "offering", kind: "offering", label: previewOffering, meta: previewChangeType },
    ...(items || []).map((item, index) => ({ id: `artifact-${index}`, kind: "artifact", label: item.name, meta: item.owner, risk: item.risk })),
  ];
  const displayColumns = columns.length ? columns : [
    { kind: "source", nodes: fallbackNodes.slice(0, 1) },
    { kind: "offering", nodes: fallbackNodes.slice(1, 2) },
    { kind: "artifact", nodes: fallbackNodes.slice(2) },
  ];

  return (
    <section className="panel impact-panel" aria-labelledby="impact-map-title">
      <header className="panel-header impact-map-header">
        <div><h2 id="impact-map-title">Offering impact map</h2><span className="live-label public"><Radio size={12} />{approved ? "Handoff plan" : "Decision scope"}</span></div>
        <span className="muted">Change → business consequence</span>
      </header>
      <div className="impact-map-summary">
        <div><span>Change type</span><strong>{summary.change_type || previewChangeType}</strong></div>
        <div><span>Affected offering</span><strong>{summary.offering || previewOffering}</strong></div>
        <div><span>Work surfaces</span><strong>{summary.artifact_count || items?.length || 0} mapped</strong></div>
      </div>
      <div className="impact-graph" role="img" aria-label="Source change mapped through offering, business impact, work surface, and handoff stages">
        {displayColumns.map((column, index) => {
          const meta = kindMeta[column.kind] || kindMeta.artifact;
          return (
            <div className="impact-graph-column" key={column.kind}>
              <div className="impact-graph-column-label"><CircleDot size={13} />{meta.label}</div>
              <div className="impact-graph-nodes">
                {column.nodes.map((node) => <GraphNode node={node} key={node.id} />)}
              </div>
              {index < displayColumns.length - 1 && <ArrowRight className="impact-graph-arrow" size={17} />}
            </div>
          );
        })}
      </div>
      <div className="impact-map-footer">
        <span><UsersRound size={14} /> Ownership follows the work, not the model</span>
        <span><Check size={14} /> Every node inherits the source evidence hash</span>
      </div>
    </section>
  );
}
