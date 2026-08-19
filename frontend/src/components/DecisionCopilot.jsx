import { CheckCircle2, ChevronDown, CircleAlert, ShieldAlert } from "lucide-react";

const label = (value) => (value || "").replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());

function shortHash(value) {
  return value ? `${value.slice(0, 12)}…` : "unavailable";
}

export default function DecisionCopilot({ copilot, selectedId, onSelect }) {
  if (!copilot?.options?.length) return null;
  const policy = copilot.policy_review;
  const blocked = policy?.status === "blocked";
  return (
    <section className="decision-copilot" aria-labelledby="decision-copilot-title">
      <header className="decision-copilot-header">
        <div><span className="decision-copilot-kicker">Decision copilot</span><h3 id="decision-copilot-title">Choose a bounded response</h3></div>
        <span className={`live-label ${copilot.mode === "gemini_structured" ? "public" : "synthetic"}`}>{copilot.mode === "gemini_structured" ? "Gemini" : "Fallback"}</span>
      </header>
      {copilot.question && <p className="decision-copilot-question">{copilot.question}</p>}
      <div className="decision-option-list">
        {copilot.options.map((option) => {
          const selected = selectedId === option.option_id;
          return (
            <label className={`decision-option${selected ? " selected" : ""}`} key={option.option_id}>
              <input type="radio" name="decision-copilot-option" value={option.option_id} checked={selected} onChange={() => onSelect(option)} />
              <span className="decision-option-copy">
                <span className="decision-option-title"><strong>{option.title}</strong><span className={`tag ${option.risk}`}>{label(option.risk)}</span></span>
                <span className="decision-option-summary">{option.summary}</span>
                <details>
                  <summary>Tradeoffs, rollback, and evidence <ChevronDown size={13} /></summary>
                  <span className="decision-option-detail"><strong>Tradeoffs</strong><span>{option.tradeoffs.join(" · ")}</span><strong>Rollback</strong><span>{option.rollback}</span><strong>Cited source</strong><q>{option.citations?.[0]?.quote}</q><small>Evidence {shortHash(option.citations?.[0]?.evidence_hash)}</small></span>
                </details>
              </span>
            </label>
          );
        })}
      </div>
      <div className={`red-team-review ${blocked ? "blocked" : "passed"}`} aria-label="Red-team policy review">
        {blocked ? <ShieldAlert size={16} /> : <CheckCircle2 size={16} />}
        <div><strong>{blocked ? "Red-team blocked this brief" : "Red-team policy check passed"}</strong><small>{blocked ? "Resolve the blocking findings before approval." : "Evidence, rollback, artifact scope, and human approval were checked."}</small>
          {policy?.findings?.length > 0 && <ul>{policy.findings.map((finding, index) => <li key={`${finding.code}-${finding.option_id || index}`}><CircleAlert size={12} /><span>{finding.message} <em>{finding.mitigation}</em></span></li>)}</ul>}
        </div>
      </div>
    </section>
  );
}
