"""Asistente RAG del proyecto — "el LLM narra; el sistema calcula".

Extensión prevista en la Entrega 2 y aplazada por la regla MVP-primero (hoy el
núcleo está cerrado). Recupera pasajes de la documentación DEL PROPIO proyecto
(memoria, cadena de backtesting, atlas, entregas) por TF-IDF y responde:

- Modo por defecto (sin red, sin clave): devuelve los pasajes citados tal cual.
- Modo --llm: Claude redacta la respuesta SOLO a partir de los pasajes
  recuperados, citándolos; los números solo pueden aparecer si están textualmente
  en un pasaje. Las preguntas normativas se reencuadran (Bloque D).

El corpus externo (informes BdE/INE en PDF) queda como pata futura declarada;
este corpus interno genera el gold_corpus_manifest.csv comprometido en la E3.

    python3 app/rag_assistant.py "¿por qué gano el drift?"
    python3 app/rag_assistant.py --llm "¿qué dice el test final?"
    python3 app/rag_assistant.py --build   (solo reconstruir el índice/manifest)
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
GOLD = ROOT / "storage" / "gold"

EXCLUIR = {"MEMORIA.docx", "MEMORIA.pdf"}
TOP_K = 4
MIN_SIM = 0.05

SYSTEM = """Eres el asistente del proyecto "Dinero público → Resultados" (TFM de Daniel Ribes).
Reglas ESTRICTAS, en este orden de prioridad:
1. Responde SOLO con información presente en los pasajes proporcionados. Si los pasajes no
   contienen la respuesta, di "El corpus del proyecto no cubre esto" y sugiere dónde podría estar.
2. Cada afirmación factual lleva su cita [n] al pasaje que la respalda.
3. NÚMEROS: solo puedes escribir una cifra si aparece textualmente en un pasaje. Nunca
   calcules, extrapoles ni redondees cifras nuevas. El sistema calcula; tú narras.
4. Preguntas normativas ("¿qué habría que recortar/priorizar?"): reencuadra como hace el
   proyecto (Bloque D) — cuantifica lo que digan los pasajes y devuelve la elección a la política.
5. Responde en el idioma de la pregunta, conciso (máx ~200 palabras)."""


def chunk_docs() -> list[dict]:
    """Trocea docs/*.md por encabezados ## (y # como fallback)."""
    chunks = []
    for path in sorted(DOCS.rglob("*.md")):
        rel_parts = path.relative_to(DOCS).parts
        # _old = planes sustituidos; defensa = duplica la memoria en formato slide
        if path.name in EXCLUIR or rel_parts[0] in ("_old", "defensa"):
            continue
        rel = path.relative_to(ROOT)
        text = path.read_text(encoding="utf-8")
        partes = re.split(r"\n(?=#{1,3} )", text)
        for parte in partes:
            parte = parte.strip()
            if len(parte) < 200:  # descarta fragmentos triviales
                continue
            m = re.match(r"#{1,3} (.+)", parte)
            seccion = m.group(1).strip() if m else "(inicio)"
            chunks.append({
                "id": f"{rel}#{len(chunks)}",
                "fuente": str(rel), "seccion": seccion[:120],
                "texto": parte, "n_car": len(parte),
            })
    return chunks


def build_manifest(chunks: list[dict]) -> None:
    import pandas as pd
    df = pd.DataFrame([{k: c[k] for k in ("id", "fuente", "seccion", "n_car")} for c in chunks])
    df.to_csv(GOLD / "gold_corpus_manifest.csv", index=False)


def retrieve(chunks: list[dict], pregunta: str, k: int = TOP_K) -> list[tuple[float, dict]]:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    vec = TfidfVectorizer(lowercase=True, ngram_range=(1, 2), sublinear_tf=True)
    X = vec.fit_transform([c["texto"] for c in chunks])
    q = vec.transform([pregunta])
    sims = cosine_similarity(q, X)[0]
    orden = sims.argsort()[::-1][:k]
    return [(float(sims[i]), chunks[i]) for i in orden if sims[i] >= MIN_SIM]


def responder_llm(pregunta: str, pasajes: list[tuple[float, dict]]) -> str:
    import anthropic
    contexto = "\n\n".join(
        f"[{i + 1}] ({c['fuente']} § {c['seccion']})\n{c['texto'][:2500]}"
        for i, (_, c) in enumerate(pasajes)
    )
    client = anthropic.Anthropic()
    resp = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=1500,
        thinking={"type": "adaptive"},
        system=[{"type": "text", "text": SYSTEM, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": f"Pasajes del corpus:\n\n{contexto}\n\nPregunta: {pregunta}"}],
    )
    if resp.stop_reason == "refusal":
        return "[El modelo declinó responder a esta pregunta.]"
    return "".join(b.text for b in resp.content if b.type == "text")


def main() -> None:
    ap = argparse.ArgumentParser(description="Asistente RAG del proyecto")
    ap.add_argument("pregunta", nargs="*", help="La pregunta")
    ap.add_argument("--llm", action="store_true", help="Redactar respuesta con Claude (requiere credenciales)")
    ap.add_argument("--build", action="store_true", help="Solo regenerar gold_corpus_manifest.csv")
    ap.add_argument("-k", type=int, default=TOP_K)
    args = ap.parse_args()

    chunks = chunk_docs()
    build_manifest(chunks)
    if args.build:
        print(f"{len(chunks)} pasajes de {len({c['fuente'] for c in chunks})} documentos → gold_corpus_manifest.csv")
        return
    if not args.pregunta:
        ap.error("falta la pregunta (o usa --build)")
    pregunta = " ".join(args.pregunta)

    pasajes = retrieve(chunks, pregunta, args.k)
    if not pasajes:
        print("El corpus del proyecto no contiene pasajes relevantes para esa pregunta.")
        return

    if args.llm:
        try:
            print(responder_llm(pregunta, pasajes))
            print("\n— Fuentes —")
        except Exception as e:  # sin credenciales, sin saldo o sin red → degradar a pasajes
            detalle = str(e).split("message")[-1][:140]
            print(f"[modo LLM no disponible: {type(e).__name__} — {detalle}]\n"
                  "Pasajes recuperados (la respuesta está aquí, sin redactar):\n", file=sys.stderr)
    for i, (sim, c) in enumerate(pasajes, 1):
        print(f"[{i}] {c['fuente']} § {c['seccion']}  (similitud {sim:.2f})")
        if not args.llm:
            resumen = " ".join(c["texto"].split())[:400]
            print(f"    {resumen}…\n")


if __name__ == "__main__":
    main()
