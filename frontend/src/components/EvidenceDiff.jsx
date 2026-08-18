import { ArrowRight, ChevronUp } from "lucide-react";

export default function EvidenceDiff({ collapsed, onToggle, evidence }) {
  const before = (evidence?.before || "Enterprise includes unlimited audit-log retention.").replace(/\.$/, "");
  const after = (evidence?.after || "Enterprise includes 365-day audit-log retention.").replace(/\.$/, "");
  return (
    <section className="panel evidence-panel">
      <header className="panel-header">
        <h2>Evidence diff</h2>
        <button className="secondary compact" onClick={onToggle}>
          {collapsed ? "Expand" : "Collapse"}<ChevronUp className={collapsed ? "rotated" : ""} size={16} />
        </button>
      </header>
      {!collapsed && (
        <div className="evidence-body">
          <div className="diff-label removed-label">Removed</div>
          <div />
          <div className="diff-label added-label">Added</div>
          <div className="diff-box removed"><del>{before}</del></div>
          <ArrowRight className="diff-arrow" size={24} />
          <div className="diff-box added">{after}</div>
          <div className="snapshot">
            <strong>Source snapshot</strong><span>{evidence?.source_id || "public/pricing"}</span>
            <i /> <span>{evidence?.snapshot_label || "Synthetic demo fixture"}</span>
          </div>
        </div>
      )}
    </section>
  );
}
