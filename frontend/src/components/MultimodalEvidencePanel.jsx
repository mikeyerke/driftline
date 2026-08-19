import { useEffect, useState } from "react";
import { Eye, FileImage, Hash, LoaderCircle, Sparkles } from "lucide-react";
import { analyzeMultimodalEvidence, getMultimodalEvidence, multimodalAssetUrl } from "../api";

export default function MultimodalEvidencePanel({ assetId = "promise-card", mode = "live" }) {
  const [evidence, setEvidence] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError("");
    getMultimodalEvidence(assetId, mode)
      .then((payload) => active && setEvidence(payload))
      .catch((requestError) => active && setError(requestError.message || "Visual evidence unavailable"))
      .finally(() => active && setLoading(false));
    return () => { active = false; };
  }, [assetId, mode]);

  const analyze = async () => {
    setAnalyzing(true);
    setError("");
    try {
      const payload = await analyzeMultimodalEvidence(assetId, mode);
      setEvidence(payload.evidence || evidence);
      setAnalysis(payload.analysis || null);
    } catch (requestError) {
      setError(requestError.message || "Gemini visual analysis unavailable");
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <section className="panel multimodal-panel" aria-labelledby="multimodal-title">
      <header className="panel-header">
        <div><h2 id="multimodal-title"><FileImage size={17} />Visual evidence</h2><span className={`live-label ${evidence?.data_mode === "public_source" ? "public" : "synthetic"}`}>{evidence?.data_mode === "public_source" ? "Public bytes" : "Demo fallback"}</span></div>
        <span className="muted">Before → after</span>
      </header>
      {loading && <p className="multimodal-empty"><LoaderCircle size={15} className="spin" />Loading allowlisted visual bytes…</p>}
      {error && <p className="trace-error" role="alert">{error}</p>}
      {evidence && (
        <>
          <div className="multimodal-grid">
            {["before", "after"].map((side) => {
              const item = evidence[side];
              return <figure className="multimodal-card" key={side}><figcaption><strong>{side === "before" ? "Before" : "After"}</strong><small>{item.mime_type} · {(item.size_bytes / 1024 / 1024).toFixed(2)} MB</small></figcaption><img src={multimodalAssetUrl(assetId, side, mode)} alt={`${item.label}, ${side} visual evidence`} loading="lazy" /><code>{item.snapshot_hash.slice(0, 16)}…</code></figure>;
            })}
          </div>
          <div className="multimodal-proof"><span><Hash size={13} />Pair evidence hash</span><code>{evidence.evidence_hash}</code></div>
          <button className="secondary full" type="button" onClick={analyze} disabled={analyzing}><Sparkles size={15} />{analyzing ? "Gemini is comparing the visuals…" : "Analyze with Gemini vision"}</button>
          {analysis && <div className="multimodal-analysis"><span><Eye size={14} />{analysis.material_change ? "Material visual change" : "No material visual change"} · {Math.round(analysis.confidence * 100)}% confidence</span><strong>{analysis.summary}</strong><small>{analysis.before_observation} Then: {analysis.after_observation}</small></div>}
        </>
      )}
    </section>
  );
}
