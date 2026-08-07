import { useEffect, useRef, useState, useSyncExternalStore } from "react";

function subscribe(cb: () => void): () => void {
  if (typeof window.matchMedia !== "function") return () => {};
  const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
  mq.addEventListener("change", cb);
  return () => mq.removeEventListener("change", cb);
}
function getSnapshot(): boolean {
  return (
    typeof window.matchMedia === "function" &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches
  );
}
/** True when the OS asks for reduced motion — gates ALL animation (spec §5). */
export function useReducedMotion(): boolean {
  return useSyncExternalStore(subscribe, getSnapshot, () => false);
}

/** Roll a displayed number to its new value over ~180 ms (spec §5). First render is exact;
 *  animation only happens on CHANGE, so tests reading the initial DOM see final values. */
export function useRollup(value: number, ms = 180): number {
  const [shown, setShown] = useState(value);
  const fromRef = useRef(value);
  const reduced = useReducedMotion();
  useEffect(() => {
    if (reduced || !Number.isFinite(value)) {
      fromRef.current = value;
      setShown(value);
      return;
    }
    const from = fromRef.current;
    if (from === value) return;
    let raf = 0;
    const t0 = performance.now();
    const step = (t: number) => {
      const p = Math.min(1, (t - t0) / ms);
      setShown(from + (value - from) * p);
      if (p < 1) raf = requestAnimationFrame(step);
      else fromRef.current = value;
    };
    raf = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf);
  }, [value, ms, reduced]);
  return shown;
}
