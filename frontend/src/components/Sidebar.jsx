import { ShieldCheck } from "lucide-react";
import { navItems } from "./Icons";

export default function Sidebar({ selected, onSelect, operatorSession }) {
  const signed = Boolean(operatorSession?.identityToken);
  return (
    <aside className="sidebar">
      <div className="brand"><span className="brand-mark">D</span><span>Driftline</span></div>
      <nav aria-label="Primary navigation">
        {navItems.map(([label, Icon]) => (
          <button
            className={selected === label ? "nav-item active" : "nav-item"}
            key={label}
            aria-label={label}
            aria-current={selected === label ? "page" : undefined}
            type="button"
            onClick={() => onSelect(label)}
          >
            <Icon size={20} strokeWidth={1.8} />
            <span>{label}</span>
          </button>
        ))}
      </nav>
      <div className="profile workspace-status" role="status">
        <ShieldCheck size={18} />
        <span><strong>{signed ? "Signed PM workspace" : "Interactive example"}</strong><small>{signed ? "Human approval required" : "No external writes"}</small></span>
      </div>
    </aside>
  );
}
