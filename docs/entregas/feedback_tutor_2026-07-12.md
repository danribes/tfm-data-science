# Feedback del tutor — Julio Valero (12 de julio de 2026)

Comentarios privados recibidos en Google Classroom (Máster en Data Science, Enero 2026), recuperados de las notificaciones de Gmail. Ambas entregas fueron devueltas ("Returned") la misma mañana, sin calificación numérica visible.

---

## 1. Sobre la entrega "Trabajo de Fin de Máster. Análisis de datos necesarios" (`02_datos_necesarios.md`)

*Comentario privado — 8:54 CEST, 12 jul 2026*

> Daniel, la propuesta está mucho mejor acotada que las ideas iniciales y trabaja con fuentes públicas, reales y bien identificadas. El principal punto a revisar es cómo defines la asequibilidad: dividir un índice de precios entre un índice salarial permite comparar evoluciones, pero no refleja por completo el esfuerzo real de comprar una vivienda, porque no incorpora aspectos como el precio por metro cuadrado, la renta disponible, la entrada necesaria o la cuota hipotecaria. Te recomiendo presentar el resultado como un indicador aproximado y, si es posible, complementarlo con alguna medida adicional de esfuerzo de compra. También conviene priorizar bien el alcance: en un MVP es buena práctica asegurar primero una entrega sólida del núcleo —pipeline, índice, análisis y una predicción bien validada— y dejar los modelos adicionales, los escenarios avanzados o el asistente con IA como mejoras deseables solo si da tiempo, sin poner en riesgo la entrega del core. Por último, solo has entregado los dos archivos Markdown y no el repositorio solicitado, por lo que no puedo comprobar la estructura, la trazabilidad ni el trabajo desarrollado. En un equipo, el formato de entrega funciona como un contrato: el siguiente miembro o proceso necesita recibir exactamente la estructura acordada para poder continuar. Espero que en las próximas entregas presentes el repositorio completo y respetes este formato.

## 2. Sobre la entrega "Trabajo de fin de máster: almacenamiento de datos" (`03_modelo_datos.md`)

*Comentario privado — 9:01 CEST, 12 jul 2026*

> Daniel, la entrega desarrolla bastante bien la parte conceptual del modelo de datos: la capa gold está mejor definida, hay granularidad, claves, campos, usos posteriores y riesgos concretos, y se nota que has pensado en problemas reales como el desfase temporal de salarios, la normalización de CCAA o la separación entre datos tabulares y corpus RAG. Aun así, se mantienen dos advertencias importantes del feedback anterior. La primera es que el índice de asequibilidad sigue siendo un indicador aproximado: dividir IPV entre salario indexado permite comparar evolución relativa, pero no representa por completo el esfuerzo real de compra si no incorporas precio por metro cuadrado, renta disponible, entrada, financiación o cuota hipotecaria; por tanto, tendrás que presentarlo con cuidado y, si puedes, complementarlo con alguna medida adicional. La segunda es más crítica a nivel de entrega: de nuevo no has entregado el repositorio completo, sino solo los markdown, y eso impide comprobar si la estructura, los datos, scripts y contratos que describes existen realmente. Para la próxima entrega espero ver el repositorio completo, con la estructura real alineada con lo que documentas, y un MVP claramente priorizado antes de extender el proyecto con modelos adicionales o RAG.

---

## Resumen de acciones pendientes

1. **Entregar el repositorio completo** (no solo los markdown), con la estructura real alineada con lo documentado. Señalado en ambos comentarios; en el segundo, calificado como el punto "más crítico". *"El formato de entrega funciona como un contrato."*
2. **Matizar el índice de asequibilidad**: IPV ÷ salario indexado = indicador aproximado de evolución relativa. Presentarlo con cuidado y, si es posible, complementarlo con una medida adicional de esfuerzo real de compra (precio por m², renta disponible, entrada, financiación, cuota hipotecaria).
3. **Priorizar el MVP**: asegurar primero el núcleo (pipeline + índice + análisis + una predicción bien validada) antes de extender con modelos adicionales, escenarios avanzados o asistente RAG/IA.
