import { LockKeyhole, Scale, Server, ShieldCheck } from "lucide-react";

export default function TrustPanel() {
  return (
    <section className="panel trust-panel" id="settings-section">
      <header className="panel-header"><div><h2>Trust and deployment posture</h2><span className="live-label">Evaluation sandbox</span></div><span className="muted">Production boundary is explicit</span></header>
      <div className="trust-grid">
        <div><Server size={18} /><strong>Google Cloud</strong><small>Cloud Run · Firestore · Cloud Tasks</small></div>
        <div><ShieldCheck size={18} /><strong>Deterministic gate</strong><small>Agent cannot approve or publish</small></div>
        <div><LockKeyhole size={18} /><strong>Evidence binding</strong><small>Every packet carries its source hash</small></div>
        <div><Scale size={18} /><strong>Bounded actions</strong><small>Sandbox packets; no external systems changed</small></div>
      </div>
      <p className="source-note">This public console is intentionally identity-free for judging. It is not an enterprise authentication claim, and it fails closed when the live backend is unavailable.</p>
    </section>
  );
}
