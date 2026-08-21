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
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries.some((entry) => entry.isIntersecting)) {
          setNearViewport(true);
          observer.disconnect();
        }
      },
      { rootMargin },
    );
    observer.observe(element);
    return () => observer.disconnect();
  }, [nearViewport, rootMargin]);

  return [panelRef, nearViewport];
}
