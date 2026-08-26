import { ArrowUpRight, LogOut, ShieldCheck } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import {
  clearOperatorSession,
  getAuthConfig,
  getAvailableTenants,
  getOperatorSession,
  setOperatorSession,
  subscribeOperatorSession,
} from "../api";

function gisReady() {
  return typeof window !== "undefined" && window.google?.accounts?.id;
}

let gisLoadPromise;

function loadGoogleIdentityServices() {
  if (gisReady()) return Promise.resolve();
  if (gisLoadPromise) return gisLoadPromise;

  gisLoadPromise = new Promise((resolve, reject) => {
    const existing = document.querySelector('script[data-driftline-google-identity]');
    const script = existing || document.createElement("script");
    const onLoad = () => resolve();
    const onError = () => reject(new Error("Google sign-in could not load"));
    script.addEventListener("load", onLoad, { once: true });
    script.addEventListener("error", onError, { once: true });
    if (!existing) {
      script.src = "https://accounts.google.com/gsi/client";
      script.async = true;
      script.defer = true;
      script.dataset.driftlineGoogleIdentity = "true";
      document.head.appendChild(script);
    }
  }).catch((error) => {
    gisLoadPromise = undefined;
    throw error;
  });

  return gisLoadPromise;
}

export default function OperatorAccess() {
  const buttonRef = useRef(null);
  const [session, setSession] = useState(getOperatorSession());
  const [config, setConfig] = useState(null);
  const [authStarted, setAuthStarted] = useState(false);
  const [authLoading, setAuthLoading] = useState(false);
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");

  useEffect(() => subscribeOperatorSession(setSession), []);

  useEffect(() => {
    const handleSessionExpired = () => {
      setAuthStarted(false);
      setStatus("Google session expired · sign in again");
      setError("");
    };
    window.addEventListener("driftline:operator-session-expired", handleSessionExpired);
    return () => window.removeEventListener("driftline:operator-session-expired", handleSessionExpired);
  }, []);

  useEffect(() => {
    let active = true;
    getAuthConfig()
      .then((payload) => active && setConfig(payload))
      .catch(() => active && setConfig({ enabled: false }));
    return () => { active = false; };
  }, []);

  useEffect(() => {
    if (!config?.enabled || session.identityToken || !authStarted || !buttonRef.current) return undefined;
    let cancelled = false;
    const render = () => {
      if (cancelled || !gisReady() || !buttonRef.current) return;
      window.google.accounts.id.initialize({
        client_id: config.client_id,
        callback: async ({ credential }) => {
          setError("");
          setStatus("Checking tenant access…");
          try {
            const payload = await getAvailableTenants(credential);
            const tenants = payload.tenants || [];
            const first = tenants[0];
            if (!first) throw new Error("Your Google account has no active Driftline tenant membership.");
            setOperatorSession({
              identityToken: credential,
              email: payload.email,
              tenants,
              tenantId: first.tenant_id,
              role: first.role,
            });
            setStatus(tenants.length > 1 ? "Choose a tenant" : "Authenticated operator");
          } catch (requestError) {
            clearOperatorSession();
            setError(requestError.message || "Tenant access could not be verified.");
            setStatus("");
          }
        },
        auto_select: false,
        cancel_on_tap_outside: true,
      });
      window.google.accounts.id.renderButton(buttonRef.current, {
        type: "standard",
        theme: "outline",
        size: "medium",
        text: "signin_with",
        shape: "rectangular",
        logo_alignment: "left",
      });
    };
    if (gisReady()) render();
    else {
      const timer = window.setInterval(() => {
        if (gisReady()) {
          window.clearInterval(timer);
          render();
        }
      }, 100);
      return () => {
        cancelled = true;
        window.clearInterval(timer);
      };
    }
    return () => { cancelled = true; };
  }, [authStarted, config, session.identityToken]);

  const startSignIn = async () => {
    setError("");
    const secureOrigin = config?.sign_in_origin;
    if (secureOrigin && window.location.origin !== secureOrigin) {
      const destination = `${secureOrigin}${window.location.pathname}${window.location.search}${window.location.hash}`;
      window.location.assign(destination);
      return;
    }
    setAuthLoading(true);
    setStatus("Loading Google sign-in…");
    try {
      setAuthStarted(true);
      await loadGoogleIdentityServices();
      setStatus("Choose your Google account…");
    } catch (loadError) {
      setAuthStarted(false);
      setStatus("");
      setError(loadError.message || "Google sign-in could not load; try again.");
    } finally {
      setAuthLoading(false);
    }
  };

  const changeTenant = (event) => {
    const tenant = session.tenants.find((item) => item.tenant_id === event.target.value);
    if (!tenant) return;
    // A tenant switch changes only the selected tenant context. Preserve the
    // short-lived Google token and the full membership list so the next
    // request remains authenticated and the operator can switch back without
    // silently falling into the anonymous packet-safe lane.
    setOperatorSession({
      ...session,
      tenantId: tenant.tenant_id,
      role: tenant.role,
    });
    setStatus("Tenant selected");
  };

  if (config === null) {
    return <span className="operator-access unavailable"><ShieldCheck size={14} />Loading operator sign-in…</span>;
  }

  if (!config.enabled) {
    return <span className="operator-access unavailable"><ShieldCheck size={14} />Operator sign-in unavailable</span>;
  }

  if (!session.identityToken) {
    return (
      <div className={`operator-access${authStarted ? " google-auth-ready" : ""}`}>
        <span className="operator-access-label"><ShieldCheck size={14} />Operator lane</span>
        {authStarted
          ? <div ref={buttonRef} aria-label="Sign in with Google for the Driftline operator lane" />
          : <button className="operator-google-trigger" type="button" onClick={startSignIn} disabled={authLoading}><ShieldCheck size={14} />{authLoading ? "Loading…" : "Sign in with Google"}{config?.sign_in_origin && window.location.origin !== config.sign_in_origin ? <ArrowUpRight size={13} /> : null}</button>}
        {status && <small className="operator-access-status">{status}</small>}
        {error && <small className="operator-access-error" role="alert">{error}</small>}
      </div>
    );
  }

  return (
    <div className="operator-access authenticated">
      <span className="operator-access-label"><ShieldCheck size={14} />{session.email}</span>
      {session.tenants.length > 1 && (
        <label className="operator-tenant-select">
          <span className="sr-only">Tenant</span>
          <select value={session.tenantId || ""} onChange={changeTenant} aria-label="Select Driftline tenant">
            {session.tenants.map((tenant) => <option key={tenant.tenant_id} value={tenant.tenant_id}>{tenant.tenant_id} · {tenant.role}</option>)}
          </select>
        </label>
      )}
      <span className="operator-access-status">{session.tenantId} · {session.role}</span>
      <button className="icon-button operator-signout" type="button" aria-label="Sign out of Driftline operator lane" onClick={() => { window.google?.accounts?.id?.disableAutoSelect?.(); clearOperatorSession(); setStatus(""); }}><LogOut size={15} /></button>
    </div>
  );
}
