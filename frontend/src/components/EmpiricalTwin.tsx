import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import { nf, sg } from "../lib/fmt";
import { Caption } from "../components/Caption";
import { HowToRead } from "./HowToRead";

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
        Comprobación con la historia · ¿frena más una subida de tipos cuando hay mucha deuda?
        <small>{nf(d.n, 0)} país-año · {nf(d.n_countries, 0)} países · {d.years[0]}–{d.years[1]}</small>
      </h4>

      <HowToRead>
        <p>
          El modelo supone que una subida de tipos de interés frena la economía lo
          mismo con poca que con mucha deuda. Para comprobarlo miramos lo que pasó
          en {nf(d.n_countries, 0)} países entre {d.years[0]} y {d.years[1]}, con un
          modelo de aprendizaje automático.
        </p>
        <p>
          La tabla dice cuánto cambió el crecimiento de los {nf(d.horizon_years, 0)} años siguientes
          por cada punto que subieron los tipos, según la deuda del país.{" "}
          {d.state_dependent
            ? "Los números son distintos según la deuda: el supuesto del modelo no se sostiene."
            : "Los números no se distinguen entre sí: no hay pruebas de que la deuda cambie el efecto, y el supuesto del modelo aguanta."}
        </p>
        <p>
          Las barras de la derecha dicen qué pesó más en el crecimiento del
          pasado: cuanto más larga, más pesó. Es historia de otros países, no una
          previsión para España.
        </p>
      </HowToRead>

      <details style={{ marginBottom: 10 }}>
        <summary style={{ fontSize: 13, color: "var(--muted)", cursor: "pointer", userSelect: "none" }}>
          Metodología ▸
        </summary>
        <p style={{ fontSize: 13.5, margin: "6px 0 0" }}>
          El motor supone que no importa: <code>E_R = {nf(d.engine_e_r, 2)}</code>{" "}
          puntos de PIB por punto de tipo, constante por diseño.{" "}
          <a href="/evidencia">Evidencia</a> declara esa constante no identificable
          con el vintage congelado. Aquí se le hace la pregunta <em>dinámica</em>{" "}
          con paneles externos: proyección local potenciada con árboles + SHAP,
          pendiente del efecto del tipo dentro de cada régimen de deuda.
        </p>
      </details>

      <div className="row2">
        <div>
          <table className="guide-t wrap-th" style={{ width: "100%" }}>
            <thead>
              <tr>
                <th>Deuda del país</th>
                <th className="num">efecto de 1 punto más de tipo</th>
                <th className="num">casos</th>
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
          <details>
            <summary style={{ fontSize: 12, color: "var(--muted)", cursor: "pointer", userSelect: "none" }}>
              IC bootstrap ▸
            </summary>
            <Caption>
              Diferencia alta−baja deuda: [{sg(d.diff_ci[0] ?? 0, 3)},{" "}
              {sg(d.diff_ci[1] ?? 0, 3)}] al 90 %, bootstrap por país
              ({nf(d.n_boot, 0)} réplicas). El intervalo incluye el cero: con
              estos datos no se puede afirmar que el efecto del tipo cambie con
              la deuda. El supuesto del motor no queda validado — queda{" "}
              <em>no contradicho</em>, que es menos y se dice tal cual.
            </Caption>
          </details>
        </div>

        <div>
          <p style={{ fontSize: 13.5, fontWeight: 700, margin: "0 0 6px" }}>
            Qué pesó más en el crecimiento a {nf(d.horizon_years, 0)} años,
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
          <details>
            <summary style={{ fontSize: 12, color: "var(--muted)", cursor: "pointer", userSelect: "none" }}>
              Nota ▸
            </summary>
            <Caption>
              La inercia del propio crecimiento y el nivel de renta dominan; el
              tipo de interés y la deuda quedan detrás. Es atribución histórica,
              no palancas de un escenario: por eso vive junto a la matriz de
              sensibilidad y no dentro de «Qué está pasando».
            </Caption>
          </details>
        </div>
      </div>

      <details>
        <summary style={{ fontSize: 12, color: "var(--muted)", cursor: "pointer", userSelect: "none" }}>
          R² y caveats ▸
        </summary>
        <p className="src" style={{ whiteSpace: "normal" }}>
          R² fuera de país {nf(d.r2_grouped, 3)} ± {nf(d.r2_std, 3)}: el modelo no
          predice el crecimiento a tres años de un país que no ha visto, así que
          estas pendientes describen la superficie ajustada, no una regla
          validada. España no puntúa aquí: {d.spain_excluded_reason}. No es
          causalidad — los bancos centrales suben tipos en expansión — y el
          contraste entre regímenes es lo único que se defiende, no los niveles.
        </p>
      </details>
    </div>
  );
}
