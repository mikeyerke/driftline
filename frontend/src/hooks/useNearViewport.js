import { useEffect, useRef, useState } from "react";

/** Defer below-the-fold reads until a panel is near the viewport. */
export default function useNearViewport(rootMargin = "700px") {
  const panelRef = useRef(null);
  const [nearViewport, setNearViewport] = useState(false);

  useEffect(() => {
    if (nearViewport) return undefined;
    if (typeof window === "undefined" || !("IntersectionObserver" in window)) {
      setNearViewport(true);
      return undefined;
    }
    const element = panelRef.current;
    if (!element) return undefined;
    const marginMatch = String(rootMargin).match(/-?\d+(?:\.\d+)?/);
    const margin = marginMatch ? Number(marginMatch[0]) : 0;
    let frame = null;
    let observer;
    const markNear = () => {
      setNearViewport(true);
      observer?.disconnect();
      window.removeEventListener("scroll", checkPassedPanel);
      if (frame !== null) window.cancelAnimationFrame(frame);
    };
    const checkPassedPanel = () => {
      if (frame !== null) return;
      frame = window.requestAnimationFrame(() => {
        frame = null;
        const rect = element.getBoundingClientRect();
        // IntersectionObserver only reports the final viewport after a large
        // jump. If a user jumps past this panel (End, sidebar navigation, or
        // a deep link), treat it as seen so deferred evidence cannot remain
        // permanently stuck behind an "in view" placeholder.
        const isNear = rect.bottom >= -margin && rect.top <= window.innerHeight + margin;
        const wasPassed = rect.bottom < 0;
        if (isNear || wasPassed) markNear();
      });
    };
    observer = new IntersectionObserver(
      (entries) => {
        if (entries.some((entry) => entry.isIntersecting)) {
          markNear();
        }
      },
      { rootMargin },
    );
    observer.observe(element);
    window.addEventListener("scroll", checkPassedPanel, { passive: true });
    checkPassedPanel();
    return () => {
      observer.disconnect();
      window.removeEventListener("scroll", checkPassedPanel);
      if (frame !== null) window.cancelAnimationFrame(frame);
    };
  }, [nearViewport, rootMargin]);

  return [panelRef, nearViewport];
}
