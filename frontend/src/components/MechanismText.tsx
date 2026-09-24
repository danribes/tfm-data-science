import { TechDetails } from "./HowToRead";

/** The engine's «mecanismo» text, laid out rather than dumped.
 *
 *  It arrives as lines: headings, «  · » bullets and, last, one line that
 *  starts «Detalle técnico:» with the model's constants. Printed as one
 *  paragraph it was a wall of text; the constants in the middle of every
 *  sentence were most of why. Here the bullets are a list and the constants —
 *  kept, a reviewer needs them — fold away with any extra technical note. */
export function MechanismText({ text, technical }: { text: string; technical?: string }) {
  const lines = text.split("\n").map((l) => l.trimEnd()).filter(Boolean);
  const tech = lines.filter((l) => l.startsWith("Detalle técnico:"));
  const body = lines.filter((l) => !l.startsWith("Detalle técnico:"));

  const blocks: React.ReactNode[] = [];
  let items: string[] = [];
  const flush = () => {
    if (items.length) {
      blocks.push(<ul className="layer-list" key={`ul${blocks.length}`}>{items.map((t, i) => <li key={i}>{t}</li>)}</ul>);
      items = [];
    }
  };
  for (const l of body) {
    const bullet = l.match(/^\s*·\s*(.*)$/);
    if (bullet) items.push(bullet[1]);
    else { flush(); blocks.push(<p key={`p${blocks.length}`}>{l}</p>); }
  }
  flush();

  return (
    <div className="mech-text">
      {blocks}
      {(tech.length > 0 || technical) && (
        <TechDetails>
          {technical && <p className="layer-note">{technical}</p>}
          {tech.map((t, i) => <p className="layer-note" key={i}>{t.replace(/^Detalle técnico:\s*/, "Constantes del modelo: ")}</p>)}
        </TechDetails>
      )}
    </div>
  );
}
