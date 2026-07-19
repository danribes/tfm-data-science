# Asistente RAG — "el LLM narra; el sistema calcula"

*2026-07-19. La extensión de la Entrega 2 ("asistente con IA"), construida DESPUÉS de cerrar el núcleo — exactamente como exigía la regla MVP-primero del tutor. Script: [`app/rag_assistant.py`](../app/rag_assistant.py); tests: [`tests/test_rag.py`](../tests/test_rag.py); manifiesto: `storage/gold/gold_corpus_manifest.csv` (cierra el contrato de la Entrega 3 §4.1 con alcance declarado).*

---

## Diseño

El papel correcto de un LLM en este proyecto quedó fijado en la [memoria §4.6](MEMORIA.md): **interfaz de lenguaje natural SOBRE los artefactos calculados** — nunca fuente de números. El asistente lo implementa con tres decisiones:

1. **Corpus = la documentación del propio proyecto** (248 pasajes de 24 documentos: memoria, cadena de backtesting, atlas, entregas, análisis), troceada por encabezados y indexada por TF-IDF (sklearn: determinista, sin red, sin dependencias nuevas). Excluidos `_old/` (planes sustituidos) y `defensa/` (duplica la memoria). El corpus EXTERNO (informes BdE/INE en PDF) sigue siendo la pata futura declarada.
2. **Dos modos**:
   - **Por defecto (sin red, sin clave)**: devuelve los pasajes citados tal cual — la respuesta con su fuente, sin redactar.
   - **`--llm`**: Claude (Opus 4.8, thinking adaptativo, prompt del sistema cacheado) redacta SOLO a partir de los pasajes recuperados, con cita [n] por afirmación y la regla dura: *"solo puedes escribir una cifra si aparece textualmente en un pasaje"*. Las preguntas normativas se reencuadran (Bloque D). Sin credenciales/saldo/red degrada limpiamente al modo pasajes.
3. **Testeado offline** (6 tests): corpus sin trivialidades ni duplicados, manifiesto con contrato, y dos consultas doradas ("por qué ganó el drift" → docs del protocolo; "elasticidad pensiones" → pasaje con el 0,91).

## Uso

```
python3 app/rag_assistant.py "¿por qué el modelo de producción es el drift?"
python3 app/rag_assistant.py --llm "¿qué dice el test final?"      # requiere API con saldo
python3 app/rag_assistant.py --build                                # regenerar manifiesto
```

## Límites declarados

- TF-IDF léxico: preguntas parafraseadas lejos del vocabulario del corpus pueden no recuperar (mitigable con embeddings locales como siguiente iteración).
- El modo `--llm` depende de credenciales y saldo de la API de Anthropic; el modo por defecto no depende de nada externo.
- El asistente NO accede a la capa gold numérica directamente: si un número no está en la documentación, la respuesta correcta es "el corpus no lo cubre" — por diseño.
