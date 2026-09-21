import { useVintage } from "../api/hooks";
import { nf } from "../lib/fmt";

/** La portada del panel: qué es esto, antes de que el lector toque nada.
 *
 *  La aplicación abría directamente en el escenario. Para quien llega desde un
 *  enlace eso está bien —quiere la herramienta— pero para quien la ve por
 *  primera vez, incluido un tribunal, no había ninguna frase que dijera qué
 *  hace ni qué se acredita de cada parte. Esa información existía sólo en la
 *  cubierta de la memoria, que está en el repositorio y no en la pantalla.
 *
 *  No es una pantalla aparte y no hay que pasar por ella: el panel sigue a
 *  continuación, a un desplazamiento de distancia. Meter un clic entre un
 *  revisor y lo que viene a revisar es la forma más rápida de que no lo mire.
 */
const CAPAS: { nombre: string; que: string; acredita: string }[] = [
  {
    nombre: "Motor determinista",
    que: "Identidad contable de la deuda y reglas calibradas, escritas dos veces: en Python y en TypeScript.",
    acredita: "Las dos implementaciones coinciden cifra a cifra en 40 series y 25 años.",
  },
  {
    nombre: "Capa empírica",
    que: "Estimación en panel, clasificación y vecinos históricos, cada uno con su protocolo.",
    acredita: "Cada resultado publica su muestra, su banda y la regla con la que se juzgó.",
  },
  {
    nombre: "Capa de explicación",
    que: "Primero se calculan los hechos y después se redactan: nunca al revés.",
    acredita: "Las cifras del texto salen del motor, no del modelo de lenguaje.",
  },
  {
    nombre: "Capa documental",
    que: "Búsqueda híbrida —densa y por palabras— sobre 58 obras académicas.",
    acredita: "Cada cita lleva documento y página comprobables.",
  },
];

const VEREDICTOS: { titulo: string; estado: string; tono: "ok" | "no" }[] = [
  { titulo: "Coherencia computacional", estado: "verificada", tono: "ok" },
  { titulo: "Descripción histórica", estado: "publicada con su muestra", tono: "ok" },
  { titulo: "Capacidad predictiva", estado: "medida y no alcanzada", tono: "no" },
  { titulo: "Identificación causal", estado: "no reclamada", tono: "no" },
];

export function Portada() {
  const vintage = useVintage();
  return (
    <section className="portada" aria-labelledby="portada-h">
      <h1 id="portada-h">España en escenarios</h1>
      <p className="portada-lead">
        Una herramienta para preguntar <b>qué implica un supuesto</b> sobre
        tipos, crecimiento, saldo público o pensiones para la deuda, la vivienda
        y el bolsillo de doce perfiles distintos. No predice: calcula las
        consecuencias aritméticas de lo que tú fijas, y enseña de dónde sale
        cada número.
      </p>

      <div className="portada-capas">
        {CAPAS.map((c) => (
          <div className="portada-capa" key={c.nombre}>
            <h3>{c.nombre}</h3>
            <p>{c.que}</p>
            <p className="portada-acredita">{c.acredita}</p>
          </div>
        ))}
      </div>

      <h2 className="portada-h2">Qué se acredita y qué no</h2>
      <div className="portada-veredictos">
        {VEREDICTOS.map((v) => (
          <div className={`portada-veredicto ${v.tono}`} key={v.titulo}>
            <b>{v.titulo}</b>
            <span>{v.estado}</span>
          </div>
        ))}
      </div>

      <p className="portada-pie">
        {vintage.isSuccess ? (
          <>
            Corte de datos <b>{vintage.data.vintage}</b> ·{" "}
            {nf(vintage.data.n_files, 0)} fuentes congeladas
          </>
        ) : (
          <>Corte de datos congelado</>
        )}
        {" · "}proyección condicional, no previsión
      </p>
    </section>
  );
}
