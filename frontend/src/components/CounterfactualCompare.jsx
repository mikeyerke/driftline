import { useRef } from "react";
import { CheckCircle2, ChevronRight, RotateCcw } from "lucide-react";

export default function CounterfactualCompare({ options, recommendedId, selectedId, onSelect }) {
  const selected = options.find((option) => option.option_id === selectedId) || options[0];
  const optionRefs = useRef([]);
  const activeId = selectedId || selected?.option_id;

  const moveSelection = (event, currentIndex) => {
    const navigation = {
      ArrowRight: (currentIndex + 1) % options.length,
      ArrowDown: (currentIndex + 1) % options.length,
      ArrowLeft: (currentIndex - 1 + options.length) % options.length,
      ArrowUp: (currentIndex - 1 + options.length) % options.length,
      Home: 0,
      End: options.length - 1,
    };
    const nextIndex = navigation[event.key];
    if (nextIndex === undefined) return;
    event.preventDefault();
    onSelect(options[nextIndex].option_id);
    optionRefs.current[nextIndex]?.focus();
  };

  return (
    <section className="decision-room-section counterfactual-section" aria-labelledby="counterfactual-title">
      <header className="decision-room-section-header"><div><span className="decision-room-kicker">Choose safely</span><h3 id="counterfactual-title">Choose the smallest safe response</h3><p className="section-dek">Every option is tied to evidence, a guardrail, and a rollback path.</p></div><span className="bounded-label">No writes until approval</span></header>
      <div className="counterfactual-tabs" role="radiogroup" aria-label="Decision options">
        {options.map((option, index) => (
          <button className={`counterfactual-tab${activeId === option.option_id ? " selected" : ""}`} type="button" role="radio" aria-checked={activeId === option.option_id} tabIndex={activeId === option.option_id ? 0 : -1} ref={(element) => { optionRefs.current[index] = element; }} key={option.option_id} onClick={() => onSelect(option.option_id)} onKeyDown={(event) => moveSelection(event, index)}>
            <span>{option.title}</span>{recommendedId === option.option_id && <small><CheckCircle2 size={12} />Recommended</small>}
          </button>
        ))}
      </div>
      {selected && <div className="counterfactual-detail">
        <div className="counterfactual-main"><span className="decision-room-kicker">Selected response</span><h4>{selected.summary}</h4><p>{selected.expected_outcome}</p><div className="affected-segments">{selected.affected_segments.map((segment) => <span key={segment}>{segment.replaceAll("_", " ")}</span>)}</div></div>
        <dl>
          <div><dt>Guardrail</dt><dd>{selected.guardrails.join(" · ")}</dd></div>
          <div><dt>What would change our mind</dt><dd>{selected.would_change_mind_if}</dd></div>
          <div><dt><RotateCcw size={14} />Rollback</dt><dd>{selected.rollback}</dd></div>
        </dl>
        <div className="counterfactual-risks"><strong>Risks</strong>{selected.risks.map((risk) => <span key={risk}><ChevronRight size={13} />{risk}</span>)}</div>
      </div>}
    </section>
  );
}
