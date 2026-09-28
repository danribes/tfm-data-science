import type { ReactNode } from "react";

/** A corpus answer, laid out rather than printed raw.
 *
 *  The prompt asks for prose, but the model writes Markdown anyway —
 *  «**Relación inicial:**», «* » bullets, «*creciente*» — and printed as text
 *  every asterisk showed. This renders the small subset it actually uses:
 *  paragraphs, bullet and numbered lists, headings as bold lines, bold,
 *  italics and inline code. As React nodes, never as HTML: the text comes from a model. A
 *  marker still open mid-stream stays literal until its closing half arrives. */
export function AnswerText({ text }: { text: string }) {
  const blocks: ReactNode[] = [];
  let items: string[] = [];
  let ordered = false;
  const flush = () => {
    if (!items.length) return;
    const lis = items.map((t, i) => <li key={i}>{inline(t)}</li>);
    blocks.push(ordered ? <ol key={blocks.length}>{lis}</ol> : <ul key={blocks.length}>{lis}</ul>);
    items = [];
  };

  for (const raw of text.split("\n")) {
    const line = raw.trim();
    const bullet = line.match(/^[*•-]\s+(.*)$/);
    const numbered = line.match(/^\d{1,2}[.)]\s+(.*)$/);
    const item = bullet ?? numbered;
    if (item) {
      if (items.length && ordered !== !bullet) flush();
      ordered = !bullet;
      items.push(item[1]);
      continue;
    }
    flush();
    if (!line) continue;
    const heading = line.match(/^#{1,6}\s+(.*)$/);
    blocks.push(<p key={blocks.length}>{heading ? <strong>{inline(heading[1])}</strong> : inline(line)}</p>);
  }
  flush();
  return <>{blocks}</>;
}

// «`x`» first, so nothing inside code reads as emphasis; then «**x**» or
// «*x*», with no space just inside the markers: «2 * 3 * 4» is arithmetic.
const INLINE = /`([^`]+)`|\*\*(\S(?:.*?\S)?)\*\*|\*(\S(?:.*?\S)?)\*/g;

function inline(text: string): ReactNode[] {
  const out: ReactNode[] = [];
  let last = 0;
  for (const m of text.matchAll(INLINE)) {
    if (m.index > last) out.push(text.slice(last, m.index));
    out.push(m[1] !== undefined ? <code key={m.index}>{m[1]}</code>
      : m[2] !== undefined ? <strong key={m.index}>{inline(m[2])}</strong>
      : <em key={m.index}>{m[3]}</em>);
    last = m.index + m[0].length;
  }
  if (last < text.length) out.push(text.slice(last));
  return out;
}
