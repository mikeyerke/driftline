import { Circle, Clock3, ExternalLink } from "lucide-react";
import { artifactIcons } from "./Icons";

const artifactRowId = (name) => `artifact-row-${String(name || "artifact").replace(/[^a-z0-9]+/gi, "-").toLowerCase()}`;

export default function ArtifactTable({ items, onSelect, selected }) {
  const statusFor = (index, fallback) => {
    return fallback || ["Draft ready", "Draft ready", "Draft ready", "Draft ready"][index];
  };

  return (
    <section className="panel worklist">
      <header className="panel-header simple"><h2>Downstream artifact worklist</h2></header>
      <div className="table-scroll">
        <table>
          <thead><tr><th scope="col">Artifact</th><th scope="col">Owner</th><th scope="col">Action</th><th scope="col">Risk</th><th scope="col">Status</th><th scope="col"><span className="sr-only">Details</span></th></tr></thead>
          <tbody>
            {items.map((item, index) => {
              const Icon = artifactIcons[index];
              const status = statusFor(index, item.status);
              const selectRow = (event) => {
                if (event.key === "Enter" || event.key === " ") {
                  event.preventDefault();
                  onSelect(item.name);
                }
              };
              return (
                <tr id={artifactRowId(item.name)} className={selected === item.name ? "selected-row" : ""} key={item.name} tabIndex={0} aria-selected={selected === item.name} onClick={() => onSelect(item.name)} onKeyDown={selectRow}>
                  <td><Icon size={16} />{item.name}</td><td>{item.owner}</td><td>{item.action}</td>
                  <td><span className={`tag ${item.risk.toLowerCase()}`}>{item.risk.charAt(0).toUpperCase() + item.risk.slice(1)}</span></td>
                  <td className={`status status-${status.toLowerCase().replaceAll(" ", "-")}`}>
                    {status === "Queued" || status === "Owner review" ? <Clock3 size={14} /> : <Circle size={10} fill="currentColor" />}{status}
                  </td>
                  <td><button className="icon-button" aria-label={`Open details for ${item.name}`} onClick={(event) => { event.stopPropagation(); onSelect(item.name); }}><ExternalLink size={15} /></button></td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <footer className="table-footer"><span>Showing {items.length} of {items.length} mapped surfaces</span><span>Risk: <i className="risk-dot high-dot" /> High <i className="risk-dot medium-dot" /> Medium <i className="risk-dot low-dot" /> Low</span></footer>
    </section>
  );
}
