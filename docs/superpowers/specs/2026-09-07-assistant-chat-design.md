# Asistente conversacional — diseño

**Fecha:** 2026-09-07 · **Estado:** aprobado en brainstorming, pendiente de plan
**Despliegue:** sólo local (misma regla que la Biblioteca: el corpus y su índice no salen de la máquina)

## 1. Objetivo

Un chat multi-turno para «España en escenarios» que (a) responde con citas sobre el corpus, (b) lee el escenario que hay en pantalla y explica sus números, y (c) ejecuta acciones sobre la interfaz cuando el usuario las pide: mover palancas, aplicar presets, cambiar el horizonte, volver a base y navegar entre pestañas. Vive en dos sitios que comparten la misma conversación: un cajón lateral disponible en toda la app y la pestaña Biblioteca, que pasa a ser el chat a pantalla completa.

**Fuera de alcance (YAGNI):** historial entre sesiones, multiusuario, voz, edición de gráficos, ejecución de código por el modelo, despliegue público del asistente.

## 2. Decisiones tomadas

| Decisión | Elección | Motivo |
|---|---|---|
| Alcance | corpus + escenario + acciones | pedido explícito |
| Ubicación | cajón global + Biblioteca a pantalla completa, una sola conversación | las acciones deben verse junto al dashboard; la Biblioteca conserva las citas |
| Modelo | `gemini-3.8-flash` fijado (env `EVO_ASSISTANT_MODEL`) | sondeo 2026-09-07: 1,1 s, llamadas paralelas a herramientas correctas, streaming con tools OK; `gemini-2.5-flash` perdía la segunda herramienta; `3.1-pro-preview` 3× más lento |
| Protocolo LLM | endpoint OpenAI-compatible con `requests`, como `rag/chat.py` | cero dependencias nuevas; todos los proveedores hablan lo mismo |
| Fallback | misma cascada **con herramientas**: `gemini-3.8-flash → gemini-2.5-flash → glm-4-plus → gpt-4o-mini` | un solo camino de código; Kimi (8k) se descarta por contexto |
| Arquitectura | bucle de agente en servidor; herramientas de UI las ejecuta el navegador | la clave no sale del servidor; el estado del escenario sigue en el navegador (store + URL), como hoy |
| Estado | servidor sin estado; la conversación viaja en cada petición | coherente con `/rag/chat/stream`; nada que persistir |

## 3. Arquitectura

```
navegador                                   servidor (FastAPI)
─────────────────────────────────           ─────────────────────────────────────────────
useAssistantStore                            POST /assistant/chat/stream  (SSE)
  messages[] · status · open · undo            │
  ↓ assistantStream()  ──── request ────────►  assistant/agent.py  (bucle tool-use)
AssistantChat  ◄──── text/passages/status ───   ├─ herramientas servidor
  ├ AssistantDrawer (shell)                     │    search_corpus → rag.retrieve.search
  └ Biblioteca (ruta)                           │    get_scenario_facts → explain.facts.build_facts
        ◄──── action + await_tools ─────────   │    run_scenario → engine.spain.run_scenario
  aplica al scenarioStore / navigate            │    find_analogs → engine.analog.find_analogs
  recalcula KPIs con el motor TS                │    list_levers → LeverValues + PRESETS
        ──── continuation(tool_results) ───►    └─ herramientas cliente → evento `action`,
        ◄──── text … done ────────────────          el turno se pausa hasta la continuación
                                               assistant/providers.py  (cascada OpenAI-compat)
                                               GET /assistant/status
```

## 4. Backend

### 4.1 Paquete `assistant/`

| Fichero | Responsabilidad |
|---|---|
| `assistant/prompt.py` | `SYSTEM` (bibliotecario + operador), plantillas de texto fijo (aviso de fallback, límite de acciones) |
| `assistant/tools.py` | definiciones JSON de las 10 herramientas; `execute_server_tool(name, args, ctx) -> dict`; validación y recorte de argumentos de las herramientas cliente; `is_client_tool(name)` |
| `assistant/providers.py` | `PROVIDERS` de la cascada del asistente; `call_stream(provider, messages, tools, ...)` que devuelve deltas de texto y `tool_calls` reconstruidas |
| `assistant/agent.py` | `stream(req) -> Iterator[tuple[event, payload]]`: el bucle; reconstrucción de mensajes; límites; fallback |
| `api/schemas.py` | `AssistantMessage`, `AssistantRequest`, `AssistantStatus` |
| `api/main.py` | `POST /assistant/chat/stream`, `GET /assistant/status` |

`rag/chat.py` no se toca salvo el cambio de modelo (§9). El asistente reutiliza `rag.chat.refusal_for`, `rag.retrieve.search`, `explain.facts.build_facts`, `engine.spain.run_scenario/baseline`, `engine.redlines.evaluate_redlines`, `engine.analog.find_analogs`.

### 4.2 Esquemas

```python
class AssistantMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=8000)      # texto final del turno; el intercambio de
                                               # herramientas de turnos pasados NO se reenvía
class ToolResultIn(BaseModel):
    tool_call_id: str
    content: str                                # JSON serializado por el cliente

class AssistantRequest(BaseModel):
    messages: list[AssistantMessage] = Field(min_length=1, max_length=60)
    levers: LeverValues = Field(default_factory=LeverValues)
    horizon: int = Field(2026, ge=2026, le=2050)
    route: str = Field("/", max_length=80)      # ruta actual, para que el modelo sepa dónde está el usuario
    collection_hint: str | None = None          # chip activo en Biblioteca; sugerencia, no filtro duro
    # Continuación tras herramientas cliente (ver §4.6). Opacos para el cliente.
    pending_assistant: dict | None = None       # mensaje assistant con tool_calls, devuelto tal cual
    pending_server_results: list[ToolResultIn] = []  # resultados de herramientas servidor ya ejecutadas
    tool_results: list[ToolResultIn] = []       # resultados de herramientas cliente

class AssistantStatus(ApiMeta):
    available: bool
    model: str | None
    reason: str | None                          # texto del 503 cuando no está disponible
```

Reglas: `messages[-1]` debe ser `user` salvo en continuación, donde `pending_assistant` no es nulo y `tool_results` no está vacío. Cualquier otra combinación → 422.

### 4.3 Eventos SSE

Mismo framing que `/rag/chat/stream` (`event: name\ndata: json\n\n`, productor en hilo + cola async).

| evento | payload | cuándo |
|---|---|---|
| `status` | `{tool, args_summary}` | al empezar cada herramienta servidor (p. ej. «buscando en libros…») |
| `passages` | `{passages: [Passage.to_dict()]}` | tras cada `search_corpus`; el cliente acumula y numera `[n]` en orden de llegada |
| `text` | `{text}` | delta de prosa |
| `action` | `{tool_call_id, tool, args, clamped: bool, note}` | por cada herramienta cliente validada |
| `await_tools` | `{pending_assistant, pending_server_results, tool_call_ids}` | cierre del turno parcial: el cliente debe aplicar las acciones y continuar |
| `done` | `{provider, model, grounded, actions_applied, error, computed_not_advice: true}` | fin del turno |
| `error` | `{detail}` | fallo no recuperable; siempre seguido de `done` |

Un turno emite o bien `… await_tools` (y termina) o bien `… done`. Nunca ambos.

### 4.4 Herramientas

**Servidor** (se ejecutan en Python dentro del bucle):

| nombre | argumentos | devuelve |
|---|---|---|
| `search_corpus` | `query: str`, `collection: enum(libros, metodo, crack23, defensa_tfm) = collection_hint or "libros"`, `top_k: int 1–12 = 6` | `{passages:[{n, cita, authority, text}]}`; `n` es el índice global del turno |
| `get_scenario_facts` | — | `explain.facts.build_facts(levers, horizon).to_dict()` recortado como `_scenario_facts` de `api/main.py` + `kpis` (b, saldo, u, pi, bono, esf en el horizonte) + `redlines` (`evaluate_redlines`) |
| `run_scenario` | `levers: dict[lever_id, float]` (parcial, se funde con el actual), `horizon: int` | KPIs y líneas rojas del escenario hipotético — **no toca la UI** |
| `find_analogs` | — | `engine.analog.find_analogs(levers, max(1, min(horizon-2026, 24)))` resumido: país, año, distancia, veredicto, 3 diffs divergentes |
| `list_levers` | — | ids, símbolo, nombre, unidad, base, min, max, paso; ids y nombres de los presets S0–S7; rutas navegables |

**Cliente** (el servidor valida, emite `action`, y pausa):

| nombre | argumentos | validación servidor |
|---|---|---|
| `set_lever` | `id: enum(10 ids)`, `value: number` | recorte a `[min,max]` de `LeverValues`; `clamped=true` y `note` si se recortó |
| `apply_preset` | `id: enum(S0…S7)` | desconocido → error al modelo |
| `set_horizon` | `year: int` | recorte a `[2026, 2050]` |
| `reset_scenario` | — | — |
| `navigate` | `route: enum(/, /persona/01…/persona/12, /laboratorio, /biblioteca, /evidencia, /prediccion, /como-funciona, /metodologia)` | fuera del enum → error al modelo |

Límite: **3 acciones por turno**. La cuarta y siguientes se descartan y el modelo recibe `tool_result{is_error: "límite de 3 acciones por turno"}`.

### 4.5 Prompt del sistema (`assistant/prompt.py`)

Hereda las cuatro reglas duras del bibliotecario (`rag/chat.py::SYSTEM`) y añade las del operador:

1. Todo número sobre el escenario sale de `get_scenario_facts`, `run_scenario` o de los `tool_results`; nunca de memoria. Si no has llamado a la herramienta, no des la cifra.
2. Toda afirmación de teoría económica lleva cita `[n]` de `search_corpus`; sin pasaje, di que el corpus no lo cubre.
3. Sólo ejecutas acciones que el usuario ha pedido explícitamente en este turno. No mueves palancas para «ilustrar» por tu cuenta; para hipótesis usa `run_scenario`.
4. Tras una acción, describe el cambio con los números nuevos que llegan en el `tool_result` (antes → después) y qué líneas rojas cambian de estado.
5. Distingue siempre: el escenario es proyección condicional, no previsión; no das consejo de inversión, vivienda ni voto.
6. Español de España, prosa con verbo, sin «es importante señalar». Respuestas cortas cuando la acción es el contenido.

Contexto inyectado en cada turno como primer mensaje `user` sintético (no como system, para que el fallback a modelos sin system fuerte funcione igual): vintage, ruta actual, palancas movidas frente a base, horizonte, `collection_hint`.

### 4.6 Bucle del agente (`assistant/agent.py`)

```
stream(req):
  if not continuation:
      if refusal := rag.chat.refusal_for(last_user_text): yield text(refusal); yield done(grounded=False); return
      messages = [system] + [context_user] + history_as_text(req.messages)
  else:
      messages = [system] + [context_user] + history_as_text(req.messages[:-1 turno])
                 + [req.pending_assistant]                      # tal cual, con extra_content/thought_signature
                 + [tool msgs de pending_server_results + tool_results]
  rounds = 0; actions = 0; passages_seen = 0
  for provider in PROVIDERS:                                     # cascada
      try:
          while rounds < 6:
              text_deltas, tool_calls, raw_assistant = providers.call_stream(provider, messages, TOOLS)
              # el texto se reenvía en vivo; si luego hay tool_calls, el texto previo queda como prosa del turno
              if not tool_calls: yield done(...); return
              rounds += 1
              server_results, client_calls = [], []
              for call in tool_calls:                            # las paralelas se respetan en orden
                  if is_client_tool(call.name):
                      ok, args, note = validate_client_call(call)
                      if actions >= 3: server_results.append(error("límite de 3 acciones")); continue
                      actions += 1; yield action(call.id, call.name, args, clamped, note); client_calls.append(call)
                  else:
                      yield status(call.name, summary(args))
                      result = execute_server_tool(call.name, args, ctx)  # excepciones → is_error
                      if call.name == "search_corpus": yield passages(result)
                      server_results.append(tool_msg(call.id, result))
              if client_calls:
                  yield await_tools(raw_assistant, server_results, [c.id for c in client_calls]); return
              messages += [raw_assistant] + server_results
          yield text(LIMITE_RONDAS); yield done(...); return
      except ProviderError: continue                              # siguiente proveedor, mismo bucle
  yield error("ningún proveedor disponible"); yield done(error=...)
```

Detalles que el sondeo obliga a fijar:

- **`thought_signature`**: Gemini 3.x devuelve `extra_content.google.thought_signature` en cada `tool_call`. `raw_assistant` es el mensaje reconstruido **con** ese campo y se reenvía íntegro en `messages`; el cliente lo guarda opaco en `pending_assistant` y lo devuelve sin tocar. Omitirlo rompe el razonamiento entre rondas de forma silenciosa.
- **Historial como texto**: los turnos anteriores viajan sólo como `{role, content}`; los `tool_calls` antiguos no se reenvían (evita firmas caducas y contiene el contexto). Las acciones ejecutadas en turnos anteriores se resumen dentro del `content` del asistente como línea final «Acciones: r → 4,80 %».
- **Numeración de pasajes**: `n` es global al turno (la segunda búsqueda continúa en `[7]`), así las citas del texto y los cards del cliente coinciden aunque haya varias búsquedas.
- **Texto antes de herramientas**: si el modelo emite prosa y después llama a una herramienta cliente, la prosa ya se ha enviado; la continuación sigue en el mismo mensaje del asistente en la UI.

### 4.7 Proveedores (`assistant/providers.py`)

```python
PROVIDERS = [
  {"name":"gemini",     "key_env":"GEMINI_API_KEY", "model": os.environ.get("EVO_ASSISTANT_MODEL","gemini-3.8-flash"),
   "base":"https://generativelanguage.googleapis.com/v1beta/openai"},
  {"name":"gemini-2.5", "key_env":"GEMINI_API_KEY", "model":"gemini-2.5-flash", "base": same},
  {"name":"glm",        "key_env":"GLM_API_KEY",    "model":"glm-4-plus",  "base":"https://open.bigmodel.cn/api/paas/v4"},
  {"name":"openai",     "key_env":"OPENAI_API_KEY", "model":"gpt-4o-mini", "base":"https://api.openai.com/v1"},
]
```

`call_stream` hace `POST /chat/completions` con `stream=true, tools, tool_choice="auto", max_tokens=2600, temperature=0.2`, reensambla los fragmentos de `tool_calls` por `index` (argumentos llegan troceados) y conserva `extra_content`. Un proveedor sin clave o con HTTP ≥ 400 / timeout (60 s) lanza `ProviderError` y la cascada pasa al siguiente **desde el principio del turno** (los `tool_results` ya obtenidos se reutilizan porque siguen en `messages`). El evento `done` declara `provider` y `model` reales, como hoy hace la Biblioteca.

### 4.8 Disponibilidad y despliegue público

`GET /assistant/status` devuelve `available=false` con `reason` si no hay ninguna clave de la cascada o si `rag` no importa (despliegue HF). `POST /assistant/chat/stream` responde 503 con el mismo `detail` que `_rag_unavailable` en ese caso. El frontend oculta el botón del cajón y muestra en Biblioteca el aviso «sólo despliegue local» ya existente.

## 5. Frontend

### 5.1 Store `src/state/assistantStore.ts`

```ts
type ChatAction = { tool: string; args: Record<string, unknown>; clamped: boolean; note?: string; undone?: boolean };
type ChatMessage = {
  id: string; role: "user" | "assistant"; text: string;
  passages: Passage[]; actions: ChatAction[]; provider?: string; model?: string;
  pending?: { pending_assistant: unknown; pending_server_results: ToolResultIn[]; tool_call_ids: string[] };
  error?: string; streaming: boolean;
};
state: { messages: ChatMessage[]; open: boolean; busy: boolean; undo: { levers: Levers; horizon: number } | null }
actions: send(text), applyAndContinue(msgId), undoLast(), toggle(open?), clear()
```

Persistencia en `sessionStorage` (clave `evo.assistant.v1`) con `messages` sin `streaming` ni `pending`; un refresco a mitad de demo no pierde el hilo, pero un turno interrumpido no se reanuda.

### 5.2 Cliente `src/api/client.ts`

`assistantStream(req: AssistantRequest, handlers, signal)` generaliza `ragChatStream` (mismo parser de frames) con handlers `onStatus, onPassages, onText, onAction, onAwaitTools, onDone, onError`. `api.assistantStatus()` para `GET /assistant/status`.

### 5.3 Componentes

| componente | dónde | qué |
|---|---|---|
| `AssistantChat` | compartido | lista de mensajes, entrada, ejemplos, chips de acción, cards de pasajes; prop `layout: "drawer" \| "page"` |
| `AssistantDrawer` | `App.tsx`, dentro de `.shell` tras `.body` | panel derecho 380 px, botón «Asistente» en la topbar, `Esc` cierra; oculto si `status.available=false` |
| `Biblioteca` | ruta existente | pasa a renderizar `AssistantChat layout="page"`; conserva chips de colección (→ `collection_hint`) y contador de documentos/pasajes; si `available=false`, aviso 503 actual |
| `ActionChip` | dentro del mensaje | `↳ Euríbor 2,80 → 4,80 %` · `↳ preset S1` · `↳ → Laboratorio`; botón **Deshacer** en el último mensaje con acciones |
| `PassageCards` | reutiliza el card actual de Biblioteca | `[n]` en el texto hace scroll al card |

### 5.4 Aplicación de acciones y continuación

Al recibir `await_tools`, `applyAndContinue`:

1. Guarda `undo = {levers, horizon}` actuales.
2. Para cada `action` recibida en el turno: `set_lever → setLever`, `apply_preset → applyPreset`, `set_horizon → setHorizon`, `reset_scenario → resetAll`, `navigate → navigate(route)` (react-router `useNavigate`, inyectado al store desde `App`).
3. Calcula con el motor TS: `runScenario(levers)`, `baseline()`, `evaluateRedlines(defs, scn, kIndex(horizon))` — `defs` sale de la query `["redlines"]` que Inicio ya carga (react-query la cachea); si aún no está, el `tool_result` omite `redlines` y lo dice → `tool_result` por acción: `{ok: true, levers, horizon, kpis:{b,saldo,u,pi,bono,esf}, deltas_vs_base, redlines:[{id,status}]}`; para `navigate`: `{ok: true, route}`.
4. Envía la continuación (`pending_assistant`, `pending_server_results`, `tool_results`, mismo `messages`) y sigue anexando `text` al **mismo** mensaje del asistente.

**Deshacer** restaura `undo` en el store y marca las acciones `undone`; no envía nada al servidor (la siguiente petición lleva el estado real en `levers/horizon`).

### 5.5 Entrada

Textarea de una línea que crece, `Enter` envía, `Shift+Enter` salto. Ejemplos bajo la entrada, dependientes de la ruta: en Inicio «Sube los tipos 200 pb y dime qué pasa con la deuda»; en un perfil «¿Qué le pasa a este perfil si aplico S7?»; en Laboratorio «Busca análogos de mi escenario». Desactivada mientras `busy`.

## 6. Flujos

**A · acción + explicación.** «Sube los tipos 200 pb y explícame qué pasa con la deuda» → `refusal_for` pasa → modelo llama `list_levers` y `set_lever(r, 4.80)` → `status`, `action`, `await_tools` → cliente aplica, KPIs 2050: b 306,9 → continuación → modelo llama `get_scenario_facts` y `search_corpus("tipo de interés coste de la deuda refinanciación")` → `passages` → `text` con «de 223,8 a 306,9 %PIB [1][2]» → `done`.

**B · hipótesis sin tocar la UI.** «¿Y si además consolidara 1 pp?» → `run_scenario({sp: 1.0}, 2050)` → texto con la comparación; ninguna `action`.

**C · rechazo.** «¿Debería vender mis acciones?» → `refusal_for` → texto fijo `REFUSAL`, `done(grounded=false)`, sin llamada al modelo.

**D · fallback.** Gemini 3.8 devuelve 503 → `ProviderError` → misma petición a `gemini-2.5-flash`; `done.model` lo declara; la UI muestra el modelo bajo la respuesta como hoy.

## 7. Errores

| caso | comportamiento |
|---|---|
| excepción en herramienta servidor | `tool_result{is_error: str(exc)}` al modelo; el flujo sigue |
| argumento fuera de rango | recorte + `clamped=true`; el chip lo muestra («recortado a 6,00 %») |
| ruta o preset desconocido | `is_error` al modelo; no se emite `action` |
| > 6 rondas | texto fijo «he alcanzado el límite de pasos de este turno» + `done` |
| todos los proveedores fallan | `error{detail}` + `done{error}`; la UI muestra banner con el detalle y conserva el mensaje del usuario para reintentar |
| cliente aborta (`AbortSignal`) | el generador termina al fallar el `yield`; nada queda a medias en el servidor porque no hay estado |
| continuación con `pending_assistant` inválido | 422 |

## 8. Pruebas

**Python (`tests/test_assistant.py`)**, con un proveedor falso inyectado en `PROVIDERS` que devuelve guiones de `tool_calls`:

- `test_tools_schema_has_ten_tools_with_enums`
- `test_set_lever_clamps_and_flags` · `test_navigate_rejects_unknown_route` · `test_apply_preset_unknown_is_error`
- `test_server_tool_search_corpus_numbers_passages_globally` (dos búsquedas → `[1..6]`, `[7..]`)
- `test_get_scenario_facts_matches_scenario_endpoint_kpis`
- `test_run_scenario_does_not_emit_action`
- `test_agent_emits_await_tools_and_keeps_thought_signature` (el `pending_assistant` devuelto contiene `extra_content`)
- `test_agent_continuation_resumes_with_tool_results`
- `test_action_cap_three_per_turn`
- `test_round_cap_six`
- `test_refusal_short_circuits_without_provider_call`
- `test_provider_failover_reruns_turn_on_next_provider`
- `test_endpoint_sse_framing_and_done_has_computed_not_advice`
- `test_status_unavailable_without_keys` · `test_stream_503_without_rag_stack`

**Frontend (Vitest + MSW, `src/routes/__tests__/assistant.test.tsx`, `biblioteca.test.tsx` adaptado):**

- drawer y Biblioteca renderizan la misma conversación del store
- `action` + `await_tools` aplica `setLever` en `scenarioStore` y envía la continuación con `tool_results` que incluyen `kpis`
- `navigate` cambia la ruta
- Deshacer restaura palancas y horizonte
- pasajes se numeran y `[n]` enlaza al card
- 503 en `/assistant/status` oculta el botón y Biblioteca muestra el aviso local-only
- rechazo se muestra sin llamada a `/assistant/chat/stream`
- las pruebas actuales de Biblioteca que dependen de `/rag/chat/stream` se reescriben contra `/assistant/chat/stream`; las de colecciones y contador se conservan

Objetivo: 382 + 251 pruebas actuales siguen verdes; ~14 Python y ~8 frontend nuevas.

## 9. Cambio de modelo en la Biblioteca (`rag/chat.py`)

Entrada Gemini de `PROVIDERS`: `gemini-2.5-flash → gemini-3.8-flash`. Verificar en `python -m rag.eval_chat` que el presupuesto `max_tokens=2600` sigue dejando respuesta completa (el comentario del código documenta el recorte medido en 2.5); ajustar sólo si la evaluación lo exige. Commit separado.

## 10. Ficheros

**Nuevos:** `assistant/__init__.py`, `assistant/prompt.py`, `assistant/tools.py`, `assistant/providers.py`, `assistant/agent.py`, `tests/test_assistant.py`, `frontend/src/state/assistantStore.ts`, `frontend/src/components/AssistantChat.tsx`, `frontend/src/components/AssistantDrawer.tsx`, `frontend/src/components/ActionChip.tsx`, `frontend/src/routes/__tests__/assistant.test.tsx`.

**Modificados:** `api/schemas.py`, `api/main.py`, `frontend/src/api/client.ts`, `frontend/src/api/types.ts`, `frontend/src/App.tsx`, `frontend/src/routes/Biblioteca.tsx`, `frontend/src/test/msw/handlers.ts`, `frontend/src/routes/__tests__/biblioteca.test.tsx`, hoja de estilos global (cajón, chips), `rag/chat.py` (§9).

## 11. Restricciones globales

- Sólo local: ninguna clave ni el corpus salen de la máquina; el despliegue HF responde 503.
- Todo número del escenario procede del motor (Python o TS), nunca del modelo.
- Vintage congelado `2026-07-31`; el asistente no consulta datos en caliente.
- Pie «proyección condicional, no recomendación» se mantiene; `refusal_for` corre antes del modelo.
- Español de España en UI y prompt.
- Sin dependencias nuevas en Python ni en el frontend.
