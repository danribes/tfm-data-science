import { useAnalogs } from "../api/hooks";
import { nf } from "../lib/fmt";
import { Caption } from "./Caption";
import { anioDeConsulta } from "../lib/analogHorizon";
import { useScenarioStore } from "../state/scenarioStore";

/** España al lado de los demás países.
 *
 *  La portada ya mostraba la puntuación de tensión de España, pero sola: un
 *  número en una escala, sin los países contra los que se puntúa. Esto pone
 *  al lado los episodios históricos más parecidos al escenario actual.
 *
 *  Las dos salvedades van pegadas a la tabla y no en una nota al pie, porque
 *  son justo la lectura que se presta a sobreinterpretar:
 *
 *  · España está excluida del conjunto de referencia por construcción. Estos
 *    son otros países en momentos parecidos, no España en su propio pasado.
 *
 *  · el parecido es descriptivo. Que a un país le fuera bien o mal después no
 *    es un pronóstico para España: es lo que le pasó a ese país.
 */
const COLS: { k: string; lab: string; dec: number }[] = [
  { k: "debt_gdp", lab: "Deuda", dec: 0 },
  { k: "overall_balance_gdp", lab: "Saldo", dec: 1 },
  { k: "unemployment", lab: "Paro", dec: 1 },
];

export function SpainAmongOthers() {
  const levers = useScenarioStore((s) => s.levers);
  const horizon = useScenarioStore((s) => s.horizon);
  const anio = anioDeConsulta(horizon);
  const q = useAnalogs(levers, anio);

  if (q.isError) {
    return (
      <div className="card">
        <h4>España entre los demás</h4>
        <div className="banner err">
          Vecinos históricos no disponibles — el resto de la página sigue funcionando.
        </div>
      </div>
    );
  }

  const matches = (q.data?.matches ?? []).slice(0, 5);

  return (
    <div className="card">
      <h4>
        España entre los demás
        <small>
          {q.data?.query_year
            ? `parecidos al escenario en ${q.data.query_year}, y qué les pasó después`
            : "episodios históricos más parecidos"}
        </small>
      </h4>

      {q.isPending && !q.data && <p style={{ fontSize: 14 }}>Buscando episodios parecidos…</p>}

      {matches.length > 0 && (
        <div className="tscroll">
          <table className="projtable">
            <thead>
              <tr>
                <th>País</th>
                <th className="num">Año</th>
                {COLS.map((c) => <th key={c.k} className="num">{c.lab}</th>)}
                <th className="num">Deuda después</th>
              </tr>
            </thead>
            <tbody>
              {matches.map((m) => {
                // El último punto de la trayectoria suele venir truncado y con
                // la deuda a null: la serie del país se acaba antes que el
                // horizonte pedido. Tomar literalmente el último dejaba la
                // columna entera en «s/d». Se busca el último punto que sí
                // trae dato.
                const fin = [...(m.outcome ?? [])].reverse()
                  .find((p) => p.debt_gdp != null);
                return (
                  <tr key={`${m.iso3}-${m.match_year}`}>
                    <th scope="row">
                      {m.country_name}
                      {/* El código sólo si aporta algo. Cuando falta el nombre
                          la API devuelve el propio ISO, y la celda salía
                          «LBN LBN». */}
                      {m.country_name !== m.iso3 && (
                        <span className="muted"> {m.iso3}</span>
                      )}
                    </th>
                    <td className="num">{m.match_year}</td>
                    {COLS.map((c) => (
                      <td className="num" key={c.k}>
                        {m.match_snapshot?.[c.k] == null
                          ? "s/d"
                          : nf(m.match_snapshot[c.k] as number, c.dec)}
                      </td>
                    ))}
                    <td className="num">
                      {fin?.debt_gdp == null
                        ? "s/d"
                        : <>{nf(fin.debt_gdp, 0)} <span className="muted">
                            a {fin.year_offset} años</span></>}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {matches.length > 1 && new Set(matches.map((m) => m.iso3)).size === 1 && (
        <Caption>
          <strong>Todos los episodios parecidos son del mismo país.</strong> No es
          un fallo de la búsqueda: es el resultado. Para un escenario con esta
          deuda apenas hay precedentes históricos, y los que hay pertenecen a una
          sola economía. Una analogía que se apoya en un único país sostiene
          mucho menos que cinco países distintos coincidiendo.
        </Caption>
      )}

      <Caption>
        <strong>Son otros países, no España.</strong> El buscador excluye a España
        del conjunto de referencia por construcción, así que estos son episodios
        ajenos en situaciones parecidas —deuda, saldo y paro— medidas por
        distancia de Mahalanobis sobre variables normalizadas.
      </Caption>
      <Caption>
        <strong>Lo que les pasó después no es un pronóstico.</strong> La columna
        «deuda después» dice cómo evolucionó <em>ese</em> país, no cómo
        evolucionará España. El parecido es descriptivo y no incorpora
        instituciones, moneda ni régimen cambiario: dos países con la misma
        deuda y el mismo paro pueden tener márgenes de maniobra muy distintos.
      </Caption>
      {q.data?.limitations && <Caption>{q.data.limitations}</Caption>}
    </div>
  );
}
