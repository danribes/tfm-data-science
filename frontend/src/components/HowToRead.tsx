/** «Cómo leerlo»: the plain-language explanation that goes before a
 *  technical chart. Written for someone who does not know what a percentile
 *  or a derivative is, and placed first so they do not have to get through the
 *  jargon to find out what they are looking at. */
export function HowToRead({ children }: { children: React.ReactNode }) {
  return (
    <div className="howto">
      <span className="howto-lab">Cómo leerlo</span>
      {children}
    </div>
  );
}

/** The technical notes, kept rather than cut — a reviewer still needs them —
 *  but folded away so they no longer stand between the reader and the chart. */
export function TechDetails({ children }: { children: React.ReactNode }) {
  return (
    <details className="tech-details">
      <summary>Detalle técnico ▸</summary>
      {children}
    </details>
  );
}
