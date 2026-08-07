export function NarrativeBlock({
  text,
  cite,
  header = "✦ Escenario condicional",
}: {
  text: string;
  cite: string;
  header?: string;
}) {
  return (
    <div className="narr">
      <div className="h">{header}</div>
      <div className="x">{text}</div>
      <div className="cite"><code>{cite}</code></div>
    </div>
  );
}
