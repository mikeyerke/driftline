import { CheckCircle2, ChevronRight, RotateCcw } from "lucide-react";

export default function CounterfactualCompare({ options, recommendedId, selectedId, onSelect }) {
  const selected = options.find((option) => option.option_id === selectedId) || options[0];
  return (
    <section className="decision-room-section counterfactual-section" aria-labelledby="counterfactual-title">
      <header className="decision-room-section-header"><div><span className="decision-room-kicker">Your options</span><h3 id="counterfactual-title">Choose what happens next</h3></div><span className="bounded-label">Preview only</span></header>
      <div className="counterfactual-tabs" role="radiogroup" aria-label="Decision options">
        {options.map((option) => (
          <button className={`counterfactual-tab${selectedId === option.option_id ? " selected" : ""}`} type="button" role="radio" aria-checked={selectedId === option.option_id} key={option.option_id} onClick={() => onSelect(option.option_id)}>
            <span>{option.title}</span>{recommendedId === option.option_id && <small><CheckCircle2 size={12} />Recommended</small>}
          </button>
        ))}
      </div>
      {selected && <div className="counterfactual-detail">
        <div className="counterfactual-main"><span className="decision-room-kicker">What this tests</span><h4>{selected.summary}</h4><p>{selected.expected_outcome}</p><div className="affected-segments">{selected.affected_segments.map((segment) => <span key={segment}>{segment.replaceAll("_", " ")}</span>)}</div></div>
        <dl>
          <div><dt>Stop if</dt><dd>{selected.guardrails.join(" · ")}</dd></div>
          <div><dt>What would change the plan</dt><dd>{selected.would_change_mind_if}</dd></div>
          <div><dt><RotateCcw size={14} />Undo</dt><dd>{selected.rollback}</dd></div>
        </dl>
        <div className="counterfactual-risks"><strong>Risks</strong>{selected.risks.map((risk) => <span key={risk}><ChevronRight size={13} />{risk}</span>)}</div>
      </div>}
    </section>
  );
}
