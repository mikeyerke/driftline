import { useEffect, useMemo, useState } from "react";
import { ArrowRight, Check, ChevronRight, CircleDot, FileCheck2, Globe2, Layers3, Link2, MousePointer2, Radio, RotateCcw, Target, UsersRound } from "lucide-react";

const kindMeta = {
  source: { label: "Observed change", icon: Globe2, tone: "source" },
  offering: { label: "Offering", icon: Target, tone: "offering" },
  domain: { label: "Business impact", icon: Layers3, tone: "domain" },
  artifact: { label: "Work surface", icon: FileCheck2, tone: "artifact" },
  system: { label: "Handoff", icon: Link2, tone: "system" },
};

function GraphNode({ node, focused, dimmed, onSelect }) {
  const meta = kindMeta[node.kind] || kindMeta.artifact;
  const Icon = meta.icon;
  const stateClass = [
    "impact-graph-node",
    meta.tone,
    focused ? "focused" : "",
    dimmed ? "dimmed" : "",
  ].filter(Boolean).join(" ");

  return (
    <button
      type="button"
      className={stateClass}
      aria-pressed={focused}
      aria-label={`${meta.label}: ${node.label}${node.meta ? `, ${node.meta}` : ""}`}
      onClick={() => onSelect(node)}
    >
      <span className="impact-graph-icon"><Icon size={15} aria-hidden="true" /></span>
      <span className="impact-graph-copy"><strong>{node.label}</strong><small>{node.meta}</small></span>
      {node.risk && <span className={`impact-graph-risk ${node.risk}`}>{node.risk}</span>}
    </button>
  );
}

function pathToSource(nodeId, nodesById, edges) {
  const path = [];
  const visited = new Set();
  let current = nodeId;
  while (current && nodesById.has(current) && !visited.has(current)) {
    visited.add(current);
    path.unshift(nodesById.get(current));
    const parent = edges.find((edge) => edge.to === current);
    current = parent?.from;
  }
  return path;
}

export default function ImpactMap({ items, graph, approved, sourceName, sourceCategory, onSelectArtifact }) {
  const nodes = graph?.nodes || [];
  const edges = graph?.edges || [];
  const [focusedNodeId, setFocusedNodeId] = useState(null);

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
  // Keep the pre-scan state structurally honest: it is a deterministic map of
  // the configured impact profile, not a blank placeholder. The live graph
  // returned by the agent uses this same source -> offering -> impact area ->
  // work surface -> handoff shape, so the console does not change its mental
  // model halfway through a scan.
  const fallbackNodes = [
    { id: "source", kind: "source", label: sourceName || "Public pricing page", meta: "Verified source change" },
    { id: "offering", kind: "offering", label: previewOffering, meta: previewChangeType },
  ];
  const fallbackEdges = [{ from: "source", to: "offering" }];
  const fallbackAreas = new Map();
  const fallbackSystems = new Map();
  const areaForItem = (item) => ({
    "Competitive positioning": "Competitive intelligence",
    "Sales objection handling": "Positioning",
    "Commercial operations": "Revenue enablement",
    "Market narrative": "Planning",
  }[item.detail] || "Downstream work");
  const systemsForItem = (item) => item.name === "Deal desk guidance"
    ? ["Jira", "Slack"]
    : ["Confluence", "Slack"];
  (items || []).forEach((item, index) => {
    const area = areaForItem(item);
    const areaId = `fallback-area-${area.toLowerCase().replaceAll(" ", "-")}`;
    if (!fallbackAreas.has(areaId)) {
      fallbackAreas.set(areaId, area);
      fallbackNodes.push({ id: areaId, kind: "domain", label: area, meta: "Impact area" });
      fallbackEdges.push({ from: "offering", to: areaId });
    }
    const artifactId = `artifact-${index}`;
    fallbackNodes.push({ id: artifactId, kind: "artifact", label: item.name, meta: item.owner, risk: item.risk });
    fallbackEdges.push({ from: areaId, to: artifactId });
    systemsForItem(item).forEach((system) => {
      const systemId = `fallback-system-${system.toLowerCase()}`;
      if (!fallbackSystems.has(systemId)) {
        fallbackSystems.set(systemId, system);
        fallbackNodes.push({ id: systemId, kind: "system", label: system, meta: "Prepared handoff" });
      }
      fallbackEdges.push({ from: artifactId, to: systemId });
    });
  });
  const displayColumns = columns.length ? columns : ["source", "offering", "domain", "artifact", "system"]
    .map((kind) => ({ kind, nodes: fallbackNodes.filter((node) => node.kind === kind) }))
    .filter((column) => column.nodes.length);
  const displayNodes = displayColumns.flatMap((column) => column.nodes);
  const displayNodesById = useMemo(() => new Map(displayNodes.map((node) => [node.id, node])), [displayNodes]);
  const displayEdges = edges.length ? edges : fallbackEdges;

  useEffect(() => {
    if (focusedNodeId && !displayNodesById.has(focusedNodeId)) setFocusedNodeId(null);
  }, [displayNodesById, focusedNodeId]);

  const focusedNode = focusedNodeId ? displayNodesById.get(focusedNodeId) : null;
  const focusedIds = useMemo(() => {
    if (!focusedNodeId) return new Set();
    // Focus the complete directed evidence chain, not only adjacent cards.
    // Walk ancestors toward the source and descendants toward handoffs; do
    // not traverse sideways through a shared offering and light up sibling
    // work surfaces that the operator did not select.
    const forward = new Map();
    const reverse = new Map();
    displayEdges.forEach((edge) => {
      if (!forward.has(edge.from)) forward.set(edge.from, []);
      if (!reverse.has(edge.to)) reverse.set(edge.to, []);
      forward.get(edge.from).push(edge.to);
      reverse.get(edge.to).push(edge.from);
    });
    const ids = new Set();
    const visit = (start, adjacency) => {
      const seen = new Set();
      const queue = [start];
      while (queue.length) {
        const current = queue.shift();
        if (seen.has(current)) continue;
        seen.add(current);
        ids.add(current);
        (adjacency.get(current) || []).forEach((neighbor) => {
          if (!seen.has(neighbor)) queue.push(neighbor);
        });
      }
    };
    visit(focusedNodeId, reverse);
    visit(focusedNodeId, forward);
    return ids;
  }, [displayEdges, focusedNodeId]);
  const focusedPath = focusedNode ? pathToSource(focusedNode.id, displayNodesById, displayEdges) : [];
  const focusedChildren = focusedNode
    ? displayEdges
      .filter((edge) => edge.from === focusedNode.id)
      .map((edge) => displayNodesById.get(edge.to))
      .filter(Boolean)
    : [];
  const meta = focusedNode ? (kindMeta[focusedNode.kind] || kindMeta.artifact) : null;

  const selectNode = (node) => {
    setFocusedNodeId(node.id);
    if (node.kind === "artifact" && onSelectArtifact) onSelectArtifact(node.label);
  };

  return (
    <section className="panel impact-panel" aria-labelledby="impact-map-title">
      <header className="panel-header impact-map-header">
        <div className="impact-map-title-group"><h2 id="impact-map-title">Offering impact map</h2><span className="live-label public"><Radio size={12} />{approved ? "Handoff plan" : "Decision scope"}</span></div>
        <div className="impact-map-header-tools"><span className="impact-map-instruction"><MousePointer2 size={13} /> Select a node to trace the work</span><span className="muted">Change → business consequence</span></div>
      </header>
      <div className="impact-map-summary">
        <div><span>Change type</span><strong>{summary.change_type || previewChangeType}</strong></div>
        <div><span>Affected offering</span><strong>{summary.offering || previewOffering}</strong></div>
        <div><span>Work surfaces</span><strong>{summary.artifact_count || items?.length || 0} mapped</strong></div>
      </div>
      <div className="impact-graph" role="group" aria-label="Source change mapped through offering, business impact, work surface, and handoff stages">
        {displayColumns.map((column, index) => {
          const columnMeta = kindMeta[column.kind] || kindMeta.artifact;
          return (
            <div className="impact-graph-column" key={column.kind}>
              <div className="impact-graph-column-label"><CircleDot size={13} />{columnMeta.label}</div>
              <div className="impact-graph-nodes">
                {column.nodes.map((node) => <GraphNode node={node} key={node.id} focused={focusedNodeId === node.id} dimmed={Boolean(focusedNodeId) && !focusedIds.has(node.id)} onSelect={selectNode} />)}
              </div>
              {index < displayColumns.length - 1 && <ArrowRight className="impact-graph-arrow" size={17} aria-hidden="true" />}
            </div>
          );
        })}
      </div>
      <div className={`impact-map-inspector${focusedNode ? " active" : ""}`} aria-live="polite">
        {focusedNode ? (
          <>
            <div className="impact-map-inspector-heading">
              <div><span>{meta.label}</span><strong>{focusedNode.label}</strong></div>
              <button type="button" className="impact-map-reset" onClick={() => setFocusedNodeId(null)}><RotateCcw size={13} /> Clear focus</button>
            </div>
            <div className="impact-map-path" aria-label="Evidence path">
              {focusedPath.map((node, index) => (
                <span className="impact-map-path-step" key={node.id}>
                  {index > 0 && <ChevronRight size={13} aria-hidden="true" />}
                  <button type="button" onClick={() => selectNode(node)} aria-label={`Focus ${node.label}`}>{node.label}</button>
                </span>
              ))}
            </div>
            <p className="impact-map-inspector-note">
              <Check size={14} /> {focusedNode.meta || "Evidence-linked node"}
              {focusedNode.risk && <><span className="impact-map-separator">·</span><strong className={`impact-map-risk ${focusedNode.risk}`}>{focusedNode.risk} risk</strong></>}
              {focusedChildren.length > 0 && <><span className="impact-map-separator">·</span>Next: {focusedChildren.map((node) => node.label).join(", ")}</>}
              {focusedNode.kind === "artifact" && onSelectArtifact && <button type="button" className="impact-map-worklist-link" onClick={() => onSelectArtifact(focusedNode.label)}>Open worklist row <ChevronRight size={13} /></button>}
            </p>
          </>
        ) : (
          <p className="impact-map-inspector-empty"><MousePointer2 size={14} /> Select a source, offering, impact area, or work surface to see what it touches and where the evidence flows.</p>
        )}
      </div>
      <div className="impact-map-footer">
        <span><UsersRound size={14} /> Ownership follows the work, not the model</span>
        <span><Check size={14} /> Every node inherits the source evidence hash</span>
      </div>
    </section>
  );
}
