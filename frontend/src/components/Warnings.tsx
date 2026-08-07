import { useHealth } from "../api/hooks";
import { nf } from "../lib/fmt";
import { STALE_LIMIT_DAYS, staleDays, useAppHealth } from "../state/appHealth";

export function Warnings({ now }: { now?: Date }) {
  const engineMismatch = useAppHealth((s) => s.engineMismatch);
  const extraWarnings = useAppHealth((s) => s.extraWarnings);
  const { data: health } = useHealth();
  const days = health ? staleDays(health.vintage, now) : 0;
  return (
    <div>
      {engineMismatch && (
        <div className="banner err" role="alert">
          ⚠️ Desajuste del motor: el cálculo local no coincide con la API (tolerancia 10⁻⁶).
          Los números en pantalla podrían no ser los del motor verificado.
        </div>
      )}
      {health && days > STALE_LIMIT_DAYS && (
        <div className="banner" role="status">
          El vintage {health.vintage} tiene {nf(days, 0)} días — los datos observados pueden estar desactualizados.
        </div>
      )}
      {extraWarnings.map((w) => (
        <div className="banner" role="status" key={w}>{w}</div>
      ))}
    </div>
  );
}
