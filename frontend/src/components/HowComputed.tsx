/** De dónde sale cada cifra de la página.
 *
 *  La aplicación tiene seis capas y el lector no tiene forma de saber cuál
 *  produjo el número que está mirando. La respuesta incómoda es que casi todo
 *  sale de la primera —una identidad contable con reglas calibradas— y que la
 *  red neuronal, que es lo que suena a predicción, no se usa porque no superó
 *  a su referencia. Decirlo aquí vale más que esconderlo: un trabajo que
 *  publica su resultado negativo es más creíble, no menos.
 */
const LAYERS: { id: string; name: string; body: string }[] = [
  {
    id: "motor", name: "MOTOR",
    body: "Identidad contable de la deuda y reglas calibradas (Phillips, Okun, "
      + "regla fiscal). Produce la inmensa mayoría de las cifras de la tabla. "
      + "No aprende de los datos: proyecta las consecuencias aritméticas de los "
      + "supuestos que fijas con las palancas.",
  },
  {
    id: "panel", name: "PANEL",
    body: "Econometría de panel sobre 19 comunidades, 2007–2026. Aporta los dos "
      + "únicos parámetros estimados del motor, y los dos actúan sobre la "
      + "vivienda. Son los que llevan error típico, y por eso la vivienda es la "
      + "única serie con banda de incertidumbre paramétrica.",
  },
  {
    id: "dl", name: "APRENDIZAJE PROFUNDO",
    // Aquí había media respuesta: se presentaba la capa entera como «no se
    // usa», cuando lo que no se usa es UNA de las dos redes. La otra está
    // codificando cada consulta ahora mismo.
    body: "Dos redes neuronales, y conviene no confundirlas. La que SÍ está en "
      + "producción es el codificador multilingual-e5-large, un transformador "
      + "de 24 capas que convierte cada pregunta en un vector de 1.024 "
      + "dimensiones: es la mitad densa de la búsqueda documental, se ejecuta "
      + "en cada consulta y es con ella medido el hit@8 publicado. Apagarla "
      + "cambia los resultados —sólo 3 de 8 pasajes coinciden con la búsqueda "
      + "por palabras—, así que no es decorativa. La que NO se usa es un "
      + "perceptrón multicapa entrenado sobre series de vivienda extranjeras "
      + "para proyectar el precio: no superó su regla de desarrollo "
      + "prerregistrada —MASE 0,4000 frente a 0,3953 de una tendencia simple, "
      + "ganando en 5 de 17 comunidades cuando la regla exigía 12— y el "
      + "resultado negativo se conserva publicado en vez de retirarse. "
      + "Ninguna de las dos interviene en las cifras de la tabla de arriba.",
  },
  {
    id: "ml", name: "CLASIFICADOR",
    body: "Gradient boosting sobre impago soberano, 154 países. Vive aparte de "
      + "las proyecciones: produce una puntuación exploratoria, sin calibrar, y "
      + "España queda fuera del conjunto etiquetado. No alimenta ninguna cifra "
      + "de la tabla.",
  },
  {
    id: "knn", name: "ANÁLOGOS",
    body: "Vecinos históricos por distancia de Mahalanobis, 173 países. "
      + "Descriptivo: busca episodios parecidos al escenario, no predice el "
      + "suyo. España está excluida del conjunto de referencia por construcción.",
  },
  {
    id: "llm", name: "RAG Y LENGUAJE",
    body: "Recuperación documental sobre los manuales, y un modelo de lenguaje "
      + "que redacta. La recuperación combina búsqueda por palabras (BM25) con "
      + "búsqueda densa, y esta última es la red neuronal descrita arriba. El "
      + "modelo de lenguaje no calcula: redacta sobre hechos ya calculados por "
      + "el motor, y las cifras que cita se comprueban contra él antes de "
      + "mostrarse.",
  },
];

export function HowComputed() {
  return (
    <div className="card">
      <h4>Cómo se ha calculado cada cifra <small>las seis capas, y cuál interviene de verdad</small></h4>
      <table className="how-table">
        <tbody>
          {LAYERS.map((l) => (
            <tr key={l.id}>
              <th scope="row"><span className={`tag prov ${l.id}`}>{l.name}</span></th>
              <td>{l.body}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <div className="layer-note">
        <strong>La respuesta corta:</strong> las cifras de la tabla salen de una
        identidad contable con reglas calibradas, no de un modelo aprendido. De
        los parámetros del motor sólo dos vienen de los datos, y afectan a la
        cadena de vivienda. Hay aprendizaje profundo en la aplicación —el
        codificador de la búsqueda documental es un transformador y se ejecuta
        en cada consulta— pero no interviene en estos números: la red que se
        entrenó para proyectar el precio no superó a su referencia y no se usa.
        El clasificador vive aparte y el modelo de lenguaje no calcula: redacta
        sobre hechos ya calculados.
      </div>
    </div>
  );
}
