import { useHealth } from "../api/hooks";
import { nf } from "../lib/fmt";
import { STALE_LIMIT_DAYS, staleDays, useAppHealth } from "../state/appHealth";
import { useScenario } from "../state/scenarioStore";

export function Warnings({ now }: { now?: Date }) {
  const engineMismatch = useAppHealth((s) => s.engineMismatch);
  const extraWarnings = useAppHealth((s) => s.extraWarnings);
  const { data: health } = useHealth();
  const scenario = useScenario();
  const days = health ? staleDays(health.vintage, now) : 0;
  return (
    <div>
      {scenario.b.some((value) => value < 0) && (
        <div className="banner" role="status">
          La trayectoria alcanza deuda negativa: queda fuera del dominio de deuda bruta
          de este modelo. No se modelan la acumulación de activos ni la respuesta de
          política al agotar la deuda.
        </div>
      )}
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
