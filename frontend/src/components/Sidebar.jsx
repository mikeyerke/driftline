import { ChevronDown } from "lucide-react";
import { navItems } from "./Icons";

export default function Sidebar({ selected, onSelect }) {
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
      <button className="profile" type="button">
        <span className="avatar">DO</span>
        <span><strong>Demo operator</strong><small>Synthetic workspace</small></span>
        <ChevronDown size={16} />
      </button>
    </aside>
  );
}
