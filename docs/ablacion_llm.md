# Ablación LLM: ¿marca la diferencia la capa ML/DL + RAG?

## Resumen en lenguaje llano (para leer antes que las tablas)

La pregunta: el valor del proyecto debe estar en las **matemáticas** (los
modelos que procesan los datos); el asistente de IA solo debe poner esos
resultados en palabras, nunca inventar los números. Para comprobarlo hicimos
un experimento sencillo: cogimos **un mismo asistente de IA** (Gemini de Google)
y le hicimos las mismas 12 preguntas dos veces. **Primera vuelta:** el asistente
solo, de memoria, sin acceso al proyecto. **Segunda vuelta:** el mismo
asistente, pero entregándole antes los resultados que ha calculado el proyecto,
y pidiéndole que responda únicamente a partir de ellos. Las 12 preguntas tienen
respuestas que *solo el proyecto puede saber* (por ejemplo, la deuda que
proyecta el simulador para 2050). Resultado: **el asistente solo acertó 3 de 12;
con los resultados del proyecto, 11 de 12.** Y sus fallos "a solas" son del tipo
peligroso — sonar convincente y equivocarse: estimó la deuda de 2050 en 135 %
del tamaño de la economía cuando el proyecto calcula 224 % (no "ve" el efecto
del envejecimiento que las matemáticas del proyecto sí miden), e inventó una
relación entre suelo y precios donde los datos muestran que apenas existe. En
resumen: **sin la capa de matemáticas y datos el asistente se equivoca; con ella
acierta — luego esa capa es la que produce el conocimiento, y el asistente solo
lo narra.** ("RAG", que aparece más abajo, significa simplemente: antes de
responder, buscar primero los documentos reales y contestar solo con ellos —
ese "buscar primero" es toda la diferencia entre las dos vueltas.)

Detalle completo pregunta a pregunta: `docs/comparativa_llm_vs_modelo.md`.

---

Requisito del tutor, convertido en experimento medible: **las matemáticas
(la capa ML/DL) producen los resultados; el LLM se limita a explicarlos.** Si
eso se cumple, un LLM a pelo — sin el sistema — NO debería reproducir los
números del modelo, y con el sistema SÍ. Aquí se comprueba, en vivo.

Reproducible: `python3 analysis/ablacion_llm.py` → `gold/gold_ablacion_llm.csv`.
Aserción permanente en `tests/test_ablacion.py` (falla si la capa deja de
diferenciar). Ejecutado con **gemini-2.5-pro** (2026-07-19); el diseño es
agnóstico al motor — el registro `ENGINES` admite kimi/glm/mimo/gemini.

## Diseño

Mismo LLM en los dos brazos; la ÚNICA variable es la capa de conocimiento.

- **Brazo A — LLM solo**: el modelo sin contexto, "da tu mejor estimación".
- **Brazo B — LLM + sistema (RAG)**: el mismo modelo con los pasajes
  recuperados del corpus del proyecto — es decir, con los resultados que
  calcula la capa ML/DL.
- **Verdad**: el valor que produce el sistema (gold / motores).

12 preguntas cuya respuesta es una SALIDA del sistema (backtests, Monte Carlo,
paneles, fronteras): imposibles de acertar sin las matemáticas, triviales de
citar con ellas.

## Resultado

| Pregunta | Verdad (sistema) | LLM solo | LLM + sistema |
|---|---|---|---|
| Ratio asequibilidad nacional 2024 | 1,26 | 1,32 ✅ | 1,26 ✅ |
| Ratio proyectado 2027Q4 (+2 % sal.) | 1,64 | **40,7** ❌ | 1,64 ✅ |
| MASE drift h≤4 (validación) | 0,395 | 0,87 ❌ | — ❌ (declina) |
| Deuda 2050 central (% PIB) | 224 | **135** ❌ | 224 ✅ |
| Deuda 2050 sin demografía | 127 | **6,5** ❌ | 127 ✅ |
| Deuda 2070 mediana MC | 409 | 181 ❌ | 409 ✅ |
| Esfuerzo hipotecario nacional 2024 | 41,6 % | 37,0 ❌ | 41,6 ✅ |
| Gasto público España 1900 | 11,0 | 8,7 ❌ | 11,0 ✅ |
| Residual sanitario España (A1) | 2,72 | 3,2 ✅ | 2,7 ✅ |
| Bienestar 2050, crec. 1 % | −12,3 % | −8,2 ❌ | −12,3 ✅ |
| Elasticidad β65 pensiones | 0,912 | 1,0 ✅ | 0,91 ✅ |
| Spearman precio/renta vs suelo | 0,01 | **0,35** ❌ | 0,01 ✅ |

**LLM solo: 3/12. LLM + sistema: 11/12. Error relativo mediano: 27 % → 0 %.**

### Lectura

- **Los dos resultados difieren de forma efectiva y masiva.** El requisito del
  tutor se cumple: sin la capa ML/DL el LLM no reproduce los números; con ella,
  sí. La diferencia no es de matiz — es 3/12 vs 11/12.
- **Los errores del LLM solo son los del "plausible pero falso"**: proyecta la
  deuda 2050 en 135 % (ignora la presión demográfica que el motor cuantifica en
  +97 pp); inventa una correlación suelo-precio de 0,35 cuando el panel mide
  0,01; da un ratio 2027 de 40,7 (confunde escalas). Exactamente el fallo que la
  capa de datos + validación evita.
- **Honestidad del propio experimento**: 11/12, no 12/12. En `mase_drift` el
  RAG recuperó el pasaje correcto pero el LLM declinó entre 0,40 (titular) y
  0,395 (h≤4) y no emitió número. Se reporta el fallo, no se esconde — es la
  misma disciplina del resto del proyecto.

## Segunda parte: ¿dónde vive el ML/DL en el modelo?

La percepción de "poco ML/DL" viene de que el modelo PUBLICADO es simple (drift,
OLS). Pero esa simplicidad es una CONCLUSIÓN de la capa matemática, no su
ausencia. El ML/DL está en toda la tubería:

| Dónde | Técnica | Rol |
|---|---|---|
| Selección T1 | 5 contests: SARIMAX, LightGBM, LightGBM+demanda, Chronos (fundacional), MLP global (PyTorch, 1.760 series) | La maquinaria que JUZGA; el drift gana porque la superó |
| Producción D1 | Regresión panel UE con efectos fijos + errores CR1 (cluster) | Elasticidades β65 0,91±0,19 — ENTRENADAS, alimentan la deuda a 2070 |
| Fronteras A1 (×3) | OLS vs GBM vs MLP bajo LOOCV + conformal | El OLS gana 5/5 — resultado medido, no supuesto |
| Horizonte 50 | Panel within (FE país+año, CR1) + Monte Carlo 4.000 trayectorias | Efecto ingreso→bienestar a retardo 8; propagación de incertidumbre |
| Tipologías A2 | PCA + KMeans | Composición del gasto (clusters débiles, silueta 0,20) |
| DL profundo | MLP entrenado sobre 208.640 observaciones (PyTorch) | Empate técnico 0,401 vs 0,395 — la única vía con evidencia de anticipar giros |
| Asistente | TF-IDF + coseno (RAG) | Recuperación; la capa de este experimento |

La matemática defendible del TFM no es "usé una red neuronal", sino: **construí
la capa de evaluación ML que dejó ganar al modelo simple en público cinco veces,
entrené las elasticidades que están en producción, y demostré que sin todo eso
el LLM se equivoca.** Esa capa ES el contenido; el LLM solo la narra.
