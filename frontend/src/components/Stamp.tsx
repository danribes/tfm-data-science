export function Stamp({ fresh, year }: { fresh: boolean; year: number }) {
  return fresh ? (
    <span className="badge-fwd">📅 dato observado · vintage</span>
  ) : (
    <span className="badge-fwd lab">🔮 condicional · {year}</span>
  );
}
