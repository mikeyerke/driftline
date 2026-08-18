import { Circle, Clock3, MoreVertical } from "lucide-react";
import { artifactIcons } from "./Icons";

export default function ArtifactTable({ items, onSelect, selected }) {
  const statusFor = (index, fallback) => {
    return fallback || ["Draft ready", "Needs approval", "Draft ready", "Scheduled"][index];
  };

  return (
    <section className="panel worklist">
      <header className="panel-header simple"><h2>Downstream artifact worklist</h2></header>
      <div className="table-scroll">
        <table>
          <thead><tr><th>Artifact</th><th>Owner</th><th>Action</th><th>Risk</th><th>Status</th><th /></tr></thead>
          <tbody>
            {items.map((item, index) => {
              const Icon = artifactIcons[index];
              const status = statusFor(index, item.status);
              return (
                <tr className={selected === item.name ? "selected-row" : ""} key={item.name} onClick={() => onSelect(item.name)}>
                  <td><Icon size={16} />{item.name}</td><td>{item.owner}</td><td>{item.action}</td>
                  <td><span className={`tag ${item.risk.toLowerCase()}`}>{item.risk.charAt(0).toUpperCase() + item.risk.slice(1)}</span></td>
                  <td className={`status status-${status.toLowerCase().replace(" ", "-")}`}>
                    {status === "Scheduled" || status === "Needs approval" ? <Clock3 size={14} /> : <Circle size={10} fill="currentColor" />}{status}
                  </td>
                  <td><button className="icon-button" aria-label={`More actions for ${item.name}`}><MoreVertical size={16} /></button></td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <footer className="table-footer"><span>Showing 4 of 4 artifacts</span><span>Risk: <i className="risk-dot high-dot" /> High <i className="risk-dot medium-dot" /> Medium <i className="risk-dot low-dot" /> Low</span></footer>
    </section>
  );
}
