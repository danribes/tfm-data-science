import type { ReactNode } from "react";

/** A one- or two-sentence note under a chart, gauge or table saying what it
 *  shows and how to read it.
 *
 *  Deliberately static text, not generated: what a chart *is* does not change
 *  when a lever moves, and paying an LLM call to re-explain the axes on every
 *  interaction would be both slow and wasteful. The Explainer handles what
 *  changed; captions handle what you are looking at. */
export function Caption({ children }: { children: ReactNode }) {
  return <p className="caption">{children}</p>;
}
