import { nf, sg } from "../lib/fmt";
import type { ContributionOut } from "../api/types";

/** How much each lever moved the headline series on its own, plus the residual.
 *
 *  Bars are scaled against the largest absolute magnitude in the set — including
 *  the interaction term, which is drawn as a bar like any other. The engine is
 *  non-linear, so the single-lever deltas genuinely do not sum to the joint
 *  movement; drawing the residual as a peer of the levers is the honest chart.
 *  Normalising it away would produce a tidier picture of a false additivity. */
export function ContributionChart({
  contributions,
  interaction,
  jointDelta,
  year,
  unit = "%PIB",
}: {
  contributions: ContributionOut[];
  interaction: number;
  jointDelta: number;
  year: number;
  unit?: string;
}) {
  if (contributions.length === 0) return null;

  const rows = [
    ...contributions.map((c) => ({ key: c.lever_id, label: c.lever_name, delta: c.delta })),
    ...(Math.abs(interaction) > 0.05
      ? [{ key: "__interaction", label: "Interacción entre palancas", delta: interaction }]
      : []),
  ];
  const max = Math.max(...rows.map((r) => Math.abs(r.delta)), 1e-9);

  return (
    <div className="contrib">
      <div className="contrib-head">
        Quién mueve la deuda en {year}
        <span className="contrib-total">{sg(jointDelta, 1)} {unit} en total</span>
      </div>
      <ul className="contrib-rows">
        {rows.map((r) => (
          <li key={r.key} className={r.key === "__interaction" ? "cr resid" : "cr"}>
            <span className="cr-label">{r.label}</span>
            <span className="cr-track">
              <span
                className={r.delta >= 0 ? "cr-bar up" : "cr-bar down"}
                style={{ width: `${(Math.abs(r.delta) / max) * 100}%` }}
              />
            </span>
            <span className="cr-val">{sg(r.delta, 1)}</span>
          </li>
        ))}
      </ul>
      <p className="contrib-note">
        Cada barra es el motor corrido otra vez con esa única palanca movida. Como
        el motor no es lineal, las palancas por separado no suman el efecto
        conjunto: esa diferencia es la barra de interacción
        {Math.abs(interaction) > 0.05 ? ` (${sg(interaction, 1)} ${unit})` : ""},
        y es una propiedad real del modelo, no un redondeo.
      </p>
      {contributions.length > 0 && (
        <p className="contrib-note dim">
          Reparto del movimiento bruto:{" "}
          {contributions
            .map((c) => `${c.lever_name.split(" · ")[0]} ${nf(c.share * 100, 0)} %`)
            .join(" · ")}
        </p>
      )}
    </div>
  );
}
