import { Check, Globe2, Info } from "lucide-react";
import { artifactIcons } from "./Icons";

export default function ImpactMap({ items, approved, sourceName }) {
  return (
    <section className="panel impact-panel">
      <header className="panel-header simple"><h2>Impact map</h2><Info size={16} /></header>
      <div className="source-node">
        <span className="check-circle"><Check size={15} /></span>
        <span><strong>Verified source change</strong><small><Globe2 size={14} />{sourceName || "Public pricing page"}</small></span>
      </div>
      <div className="impact-tree">
        {items.map((item, index) => {
          const Icon = artifactIcons[index];
          const status = item.status || "Draft ready";
          const statusLabel = status.replace(/_/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
          const riskLabel = item.risk.charAt(0).toUpperCase() + item.risk.slice(1);
          const resolvedStatus = approved ? status.toLowerCase().replace(/\s+/g, "-") : item.risk.toLowerCase();
          return (
            <div className="impact-row" key={item.name}>
              <span className="branch" />
              <span className="artifact-icon"><Icon size={18} /></span>
              <span className="impact-copy"><strong>{item.name}</strong><small>{item.detail}</small></span>
              <span className={`tag ${approved ? resolvedStatus : item.risk.toLowerCase()}`}>
                {approved ? statusLabel : riskLabel}
              </span>
            </div>
          );
        })}
      </div>
    </section>
  );
}
