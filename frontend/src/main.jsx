import React from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import "./styles.css";

class AppErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error) {
    // Keep the recovery surface useful without sending the exception or page
    // state to a third party. Cloud Run request and browser logs remain the
    // only diagnostic source for this deployment.
    console.error("Driftline console render failure", error?.message || "unknown error");
  }

  render() {
    if (!this.state.hasError) return this.props.children;
    return (
      <main className="app-error" role="alert" aria-live="assertive">
        <section className="app-error-card">
          <span className="app-error-kicker">Driftline · recovery</span>
          <h1>The console hit an unexpected state.</h1>
          <p>Your workflow data is persisted separately. Reload the console to reconnect without losing the audit trail.</p>
          <div className="app-error-actions">
            <button type="button" onClick={() => window.location.reload()}>Reload console</button>
            <a href="/privacy.html">Privacy</a>
          </div>
        </section>
      </main>
    );
  }
}

createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <AppErrorBoundary>
      <App />
    </AppErrorBoundary>
  </React.StrictMode>,
);
