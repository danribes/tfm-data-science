import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import { nf, sg } from "../lib/fmt";
import { Caption } from "../components/Caption";

/** The empirical twin of the structural attribution.
 *
 *  The engine's ContributionChart answers "what did *your levers* do to this
 *  scenario", by re-running the engine. This card answers the historical
 *  version — "what moved three-year growth across 140 countries, and does the
 *  rate effect depend on the debt level" — and puts the two side by side
 *  without pretending they are the same kind of number.
 */
export function EmpiricalTwin() {
  const q = useQuery({
    queryKey: ["state-dependence"],
    queryFn: api.stateDependence,
    staleTime: Infinity,
  });

  if (q.isError) return null;
  if (q.data && !q.data.available) return <div className="banner">{q.data.note}</div>;
  if (!q.data) return null;

  const d = q.data;
  const maxImp = Math.max(...d.importance.map((i) => i.mean_abs_shap), 1e-9);

  return (
    <div className="card" style={{ marginTop: 16 }}>
      <h4>
        El gemelo empírico · ¿pega igual un tipo al 60 % que al 120 % de deuda?
        <small>{nf(d.n, 0)} país-año · {nf(d.n_countries, 0)} países · {d.years[0]}–{d.years[1]}</small>
      </h4>

      <p style={{ fontSize: 14.5, margin: "4px 0 10px" }}>
        El motor supone que no importa: <code>E_R = {nf(d.engine_e_r, 2)}</code>{" "}
        puntos de PIB por punto de tipo, constante por diseño.{" "}
        <a href="/evidencia">Evidencia</a> declara esa constante no identificable
        con el vintage congelado. Aquí se le hace la pregunta <em>dinámica</em>{" "}
        con paneles externos: proyección local potenciada con árboles + SHAP,
        pendiente del efecto del tipo dentro de cada régimen de deuda.
      </p>

      <div className="row2">
        <div>
          <table className="guide-t" style={{ width: "100%" }}>
            <thead>
              <tr>
                <th>Régimen</th>
                <th className="num">pendiente SHAP</th>
                <th className="num">n</th>
              </tr>
            </thead>
            <tbody>
              {d.regimes.map((r) => (
                <tr key={r.label}>
                  <td>{r.label}</td>
                  <td className="num">{sg(r.slope, 3)}</td>
                  <td className="num dim">{nf(r.n, 0)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="verdict-line" style={{ marginTop: 8 }}>
            <span className={d.state_dependent ? "st cross" : "st safe"}>
              {d.state_dependent
                ? "dependiente del estado — contradice al motor"
                : "no distinguible — la constante del motor sobrevive"}
            </span>
          </p>
          <Caption>
            Diferencia alta−baja deuda: [{sg(d.diff_ci[0] ?? 0, 3)},{" "}
            {sg(d.diff_ci[1] ?? 0, 3)}] al 90 %, bootstrap por país
            ({nf(d.n_boot, 0)} réplicas). El intervalo incluye el cero: con
            estos datos no se puede afirmar que el efecto del tipo cambie con
            la deuda. El supuesto del motor no queda validado — queda{" "}
            <em>no contradicho</em>, que es menos y se dice tal cual.
          </Caption>
        </div>

        <div>
          <p style={{ fontSize: 13.5, fontWeight: 700, margin: "0 0 6px" }}>
            Qué movió el crecimiento a {nf(d.horizon_years, 0)} años,
            históricamente <span className="dim">(|SHAP| medio)</span>
          </p>
          {d.importance.map((i) => (
            <div key={i.feature} className="et-row">
              <span className="et-lab">{i.label}</span>
              <span className="et-track">
                <span className="et-fill"
                      style={{ width: `${(i.mean_abs_shap / maxImp) * 100}%` }} />
              </span>
              <span className="et-val">{nf(i.mean_abs_shap, 2)}</span>
            </div>
          ))}
          <Caption>
            La inercia del propio crecimiento y el nivel de renta dominan; el
            tipo de interés y la deuda quedan detrás. Es atribución histórica,
            no palancas de un escenario: por eso vive junto a la matriz de
            sensibilidad y no dentro de «Qué está pasando».
          </Caption>
        </div>
      </div>

      <p className="src" style={{ whiteSpace: "normal" }}>
        R² fuera de país {nf(d.r2_grouped, 3)} ± {nf(d.r2_std, 3)}: el modelo no
        predice el crecimiento a tres años de un país que no ha visto, así que
        estas pendientes describen la superficie ajustada, no una regla
        validada. España no puntúa aquí: {d.spain_excluded_reason}. No es
        causalidad — los bancos centrales suben tipos en expansión — y el
        contraste entre regímenes es lo único que se defiende, no los niveles.
      </p>
    </div>
  );
}
