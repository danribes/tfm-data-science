import type { RagCollectionsResponse } from "../api/types";

export const PUBLIC_RAG_EXAMPLES = [
  "¿Qué parámetros de vivienda están estimados con datos?",
  "¿Por qué el modelo produce escenarios y no predicciones?",
  "¿Qué límites tiene la simulación Monte Carlo del proyecto?",
  "¿Cómo se puede reproducir el proyecto?",
];

/** Describe the connected corpus before readers assign weight to its answers. */
export function RagCorpusNotice({ data }: { data?: RagCollectionsResponse }) {
  if (!data) return null;
  const isPublic = data.corpus_scope === "public_project_docs";
  if (!isPublic && data.retrieval_mode !== "lexical") return null;
  return (
    <p className="layer-note">
      {isPublic && <>
        Biblioteca pública de documentación propia del proyecto. Explica el modelo y sus límites;
        no sustituye fuentes académicas independientes. Los libros privados no forman parte de este corpus.{" "}
      </>}
      {data.retrieval_mode === "lexical" && <>
        La búsqueda usa coincidencias de palabras; prueba con los términos del modelo.
      </>}
    </p>
  );
}
