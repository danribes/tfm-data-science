---
marp: true
theme: default
paginate: true
size: 16:9
header: 'España en escenarios · guía de uso del modelo'
footer: 'Daniel Ribes · TFM Data Science · vintage 2026-07-31 · proyección condicional, no previsión'
style: |
  section { font-family: 'Segoe UI', 'Inter', system-ui, sans-serif; color: #1B2430; background: #F4F7FA !important; background-image: none !important; font-size: 19px; padding: 34px 50px 46px 50px; line-height: 1.3; }
  h1 { color: #0B2545; font-size: 1.62em; font-weight: 800; letter-spacing: -0.01em; border-bottom: 3px solid #13A89E; padding-bottom: 4px; margin: 0 0 0.35em 0; }
  h1 .sub { color: #4A5568; font-weight: 500; font-size: 0.55em; margin-left: 10px; }
  h2 { color: #0B2545; font-size: 1.15em; margin: 0.2em 0 0.1em 0; }
  h3 { color: #0E877F; font-size: 0.95em; margin: 0.25em 0 0.1em 0; text-transform: uppercase; letter-spacing: 0.04em; }
  p { margin: 0.25em 0; }
  strong { color: #0B2545; }
  em { color: #4A5568; }
  code { background: #E3EAF3; color: #0B2545; padding: 1px 6px; border-radius: 4px; font-size: 0.85em; }
  table { border-collapse: collapse; width: 100%; font-size: 0.72em; }
  th { background: #0B2545; color: white; padding: 5px 8px; text-align: left; font-weight: 600; }
  td { padding: 4px 8px; border-bottom: 1px solid #e2e8f0; vertical-align: top; }
  tr:nth-child(even) td { background: #ffffff; }
  td.n, th.n { text-align: right; font-variant-numeric: tabular-nums; }
  ul, ol { line-height: 1.32; margin: 0.2em 0; padding-left: 1.15em; }
  li { margin: 0.12em 0; }
  ul li::marker, ol li::marker { color: #13A89E; }
  img { border-radius: 8px; box-shadow: 0 2px 10px rgba(11,37,69,0.10); }
  img.ico { display: inline-block; vertical-align: middle; flex: none; box-shadow: none; border-radius: 0; background: transparent; }
  header, footer, section::after { color: #7b8794; font-size: 0.62em; font-weight: 500; }
  .pill { display: inline-block; padding: 2px 10px; border-radius: 100px; font-size: 0.68em; font-weight: 700; margin: 0 2px; background: #E3EAF3; color: #0B2545; }
  .pill.teal { background: #DDF3F1; color: #0E877F; }
  .pill.coral { background: #FDE3E0; color: #c0392b; }
  .pill.gold { background: #FCEFD2; color: #9a6b00; }
  .g2 { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; align-items: start; }
  .g3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 14px; align-items: start; }
  .g4 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; align-items: start; }
  .g6 { display: grid; grid-template-columns: repeat(6, 1fr); gap: 10px; }
  .card { background: #fff; border-radius: 10px; padding: 12px 14px; box-shadow: 0 1px 6px rgba(11,37,69,0.07); border-top: 4px solid #13A89E; }
  .card.navy { border-top-color: #0B2545; } .card.coral { border-top-color: #F4645A; } .card.gold { border-top-color: #F2B134; }
  .card h2 { margin-top: 0; font-size: 1.0em; display: flex; align-items: center; gap: 8px; }
  .card p, .card li { font-size: 0.82em; color: #4A5568; }
  .kpi { background: #fff; border-radius: 10px; padding: 10px 12px; border-left: 5px solid #13A89E; box-shadow: 0 1px 6px rgba(11,37,69,0.07); }
  .kpi .num { font-size: 1.5em; font-weight: 800; color: #0B2545; line-height: 1.05; font-variant-numeric: tabular-nums; }
  .kpi .num small { font-size: 0.5em; color: #4A5568; font-weight: 600; margin-left: 3px; }
  .kpi .lbl { font-size: 0.68em; color: #4A5568; margin-top: 3px; }
  .kpi .d { font-size: 0.7em; font-weight: 700; margin-top: 2px; }
  .kpi.coral { border-left-color: #F4645A; } .kpi.gold { border-left-color: #F2B134; } .kpi.navy { border-left-color: #0B2545; }
  .up { color: #c0392b; } .dn { color: #0E877F; }
  .flow { display: flex; align-items: stretch; gap: 0; margin: 10px 0; }
  .flow .node { flex: 1; background: #fff; border-radius: 10px; padding: 10px 10px; box-shadow: 0 1px 6px rgba(11,37,69,0.07); border-top: 4px solid #13A89E; font-size: 0.78em; }
  .flow .node b { display: block; color: #0B2545; font-size: 1.05em; margin-bottom: 2px; }
  .flow .node .k { display: inline-block; background: #E3EAF3; color: #0B2545; border-radius: 4px; padding: 0 6px; font-family: ui-monospace, Consolas, monospace; font-size: 0.85em; margin: 2px 2px 0 0; }
  .flow .arr { display: flex; align-items: center; padding: 0 6px; color: #13A89E; font-size: 1.6em; font-weight: 800; }
  .eq { font-family: 'Cambria Math', 'Times New Roman', serif; font-size: 2.0em; color: #0B2545; text-align: center; background: #fff; border-radius: 12px; padding: 14px; box-shadow: 0 1px 8px rgba(11,37,69,0.08); margin: 8px 0 12px; }
  .eq .r { color: #F4645A; } .eq .g { color: #0E877F; } .eq .sp { color: #F2B134; }
  .bar { display: grid; grid-template-columns: 240px 1fr 70px; align-items: center; gap: 8px; font-size: 0.78em; margin: 3px 0; }
  .bar .t { height: 16px; border-radius: 4px; background: #F4645A; } .bar .t.dn { background: #13A89E; }
  .bar .v { text-align: right; font-weight: 700; color: #0B2545; font-variant-numeric: tabular-nums; }
  .num-c { display: inline-flex; width: 24px; height: 24px; border-radius: 50%; background: #F4645A; color: #fff; font-weight: 800; font-size: 0.75em; align-items: center; justify-content: center; margin-right: 6px; flex: none; }
  .legend { display: flex; gap: 14px; font-size: 0.72em; color: #4A5568; margin-top: 6px; }
  .legend span::before { content: ''; display: inline-block; width: 10px; height: 10px; border-radius: 3px; margin-right: 5px; vertical-align: middle; }
  .legend .safe::before { background: #13A89E; } .legend .near::before { background: #F2B134; } .legend .cross::before { background: #F4645A; }
  .st { display: inline-block; padding: 1px 8px; border-radius: 4px; font-size: 0.85em; font-weight: 700; }
  .st.safe { background: #DDF3F1; color: #0E877F; } .st.near { background: #FCEFD2; color: #9a6b00; } .st.cross { background: #FDE3E0; color: #c0392b; }
  .cap { font-size: 0.72em; color: #4A5568; margin-top: 4px; }
  .persona { background: #fff; border-radius: 10px; padding: 10px 10px; box-shadow: 0 1px 6px rgba(11,37,69,0.07); display: flex; gap: 8px; align-items: flex-start; font-size: 0.72em; }
  .persona b { display: block; color: #0B2545; font-size: 1.05em; }
  .persona span { color: #4A5568; }
  .shot { width: 100%; }
  .note { background: #FCEFD2; border-left: 4px solid #F2B134; padding: 6px 10px; border-radius: 6px; font-size: 0.78em; color: #5c4400; margin-top: 8px; }
  section.cover { background: #0B2545 !important; background-image: none !important; color: #fff; padding: 70px 80px; }
  section.cover h1 { color: #fff; border: none; font-size: 2.9em; margin-top: 30px; }
  section.cover h2 { color: #9fd9d3; font-weight: 400; font-size: 1.35em; }
  section.cover p { color: #b7c4d6; }
  section.cover .tag { display: inline-block; background: #13A89E; color: #fff; padding: 4px 14px; border-radius: 100px; font-weight: 700; font-size: 0.75em; letter-spacing: 0.06em; }
  section.cover header, section.cover footer, section.cover::after { display: none; }
  section.divider { background: #13A89E !important; background-image: none !important; color: #fff; padding: 90px 80px; }
  section.divider h1 { color: #fff; border: none; font-size: 2.6em; }
  section.divider h2 { color: #e6f7f5; font-weight: 400; font-size: 1.3em; }
  section.divider p { color: #d6f0ed; }
  section.divider header, section.divider footer { display: none; }
  section.divider::after { color: #e6f7f5; }
  section.dense { font-size: 17px; }

---
<!-- _class: cover -->

<span class="tag">GUÍA DE USO · DEFENSA TFM</span>

# España en escenarios

## Cómo funciona el modelo, cómo se opera y qué resultados produce

<p style="margin-top:34px"><img class="ico" src="icons/_c/globe_9fd9d3.svg" width="22" height="22" alt=""> <b>danribes.github.io/tfm-data-science</b> &nbsp;·&nbsp; <img class="ico" src="icons/_c/db_9fd9d3.svg" width="22" height="22" alt=""> API en Hugging Face Spaces &nbsp;·&nbsp; <img class="ico" src="icons/_c/calendar_9fd9d3.svg" width="22" height="22" alt=""> vintage congelado 2026-07-31</p>
<p style="font-size:0.8em;margin-top:18px">Simulador macro-fiscal condicional para España, 2026–2050 · motor de identidad de deuda con 10 palancas · 12 perfiles ciudadanos · Monte Carlo · análogos históricos</p>

---

# Qué vamos a ver <span class="sub">cuatro bloques</span>

<div class="g4">
<div class="card navy"><h2><img class="ico" src="icons/_c/bulb_0B2545.svg" width="26" height="26" alt=""> 1 · El modelo</h2><p>Una pregunta, una identidad contable y una cadena de transmisión con coeficientes con nombre. Arquitectura de datos y despliegue.</p></div>
<div class="card "><h2><img class="ico" src="icons/_c/slider_13A89E.svg" width="26" height="26" alt=""> 2 · Cómo se opera</h2><p>Punto de partida (vintage), las 10 palancas y sus rangos, los 8 presets, el horizonte y cómo leer cada tipo de resultado.</p></div>
<div class="card gold"><h2><img class="ico" src="icons/_c/layer_F2B134.svg" width="26" height="26" alt=""> 3 · Recorrido por las pestañas</h2><p>Inicio, 12 perfiles, Laboratorio (abanico, Sankey, sensibilidad, gemelo empírico, análogos), Biblioteca, Evidencia, Predicción, método.</p></div>
<div class="card coral"><h2><img class="ico" src="icons/_c/target_F4645A.svg" width="26" height="26" alt=""> 4 · Escenarios ilustrativos</h2><p>Cuatro escenarios de extremo a extremo con sus números, líneas rojas y lectura. Comparativa de los 8 presets y límites del modelo.</p></div>
</div>

<p class="cap" style="margin-top:14px">Todas las cifras del deck provienen de la API en producción (motor v1.0.0) el 6-sep-2026. Las capturas son de la web publicada.</p>

---

<!-- _class: divider -->

<span style="font-size:0.9em;opacity:.8">01</span>

# El modelo

## una pregunta, una identidad, una cadena de transmisión

---

# Qué pregunta responde <span class="sub">y qué no</span>

<div class="card navy" style="font-size:1.05em;padding:16px 20px">
<b>¿Qué le pasaría a la deuda, al paro, a los precios y al esfuerzo de comprar vivienda si algunas condiciones cambiaran y se mantuvieran así?</b>
</div>

<div class="g3" style="margin-top:14px">
<div class="card "><h2><img class="ico" src="icons/_c/settings_13A89E.svg" width="26" height="26" alt=""> Es una proyección condicional</h2><p>No dice qué va a pasar; dice qué implica el modelo si mueves una palanca y la dejas quieta. Nadie sabe dónde estará el Euríbor en 2040 — sí se puede ser explícito sobre la aritmética que lo conecta con la deuda.</p></div>
<div class="card gold"><h2><img class="ico" src="icons/_c/gauge_F2B134.svg" width="26" height="26" alt=""> Enseña el margen de error</h2><p>Cada escenario lleva un abanico de 4.000 trayectorias Monte Carlo (semilla 42). Lo informativo es la anchura de la banda, no la mediana.</p></div>
<div class="card coral"><h2><img class="ico" src="icons/_c/people_F4645A.svg" width="26" height="26" alt=""> Baja al bolsillo</h2><p>El mismo número agregado se traduce a 12 perfiles: bonista, banca, comprador de vivienda, jubilado, joven, autónomo… con datos observados del vintage y proyección 2026–2050.</p></div>
</div>

<div class="note"><img class="ico" src="icons/_c/warning_F2B134.svg" width="18" height="18" alt=""> No es una previsión ni una recomendación de compra, venta o voto. Es lo que el modelo implica si esas palancas se mantuvieran en esos valores.</div>

---

# La identidad que gobierna todo <span class="sub">casi todo el motor existe para alimentar tres términos</span>

<div class="eq">b(t+1) = b(t) · (1 + <span class="r">r</span> − <span class="g">g</span>) − <span class="sp">sp</span></div>

<div class="g3">
<div class="card coral"><h2><img class="ico" src="icons/_c/money_F4645A.svg" width="26" height="26" alt=""> <span style="color:#F4645A">r</span> · tipo efectivo de la deuda</h2><p>Lo que cuesta la deuda viva. Sólo se refinancia el <b>14 %</b> cada año (<code>REFI</code>), así que un tipo nuevo entra en el coste poco a poco. El bono a 10 años = <code>r + TERM + prima/100</code>.</p></div>
<div class="card "><h2><img class="ico" src="icons/_c/trend_up_13A89E.svg" width="26" height="26" alt=""> <span style="color:#0E877F">g</span> · crecimiento nominal</h2><p>Lo que crece la economía. Recoge productividad (λ), demanda externa (Y*), y el freno del propio tipo (<code>E_R</code>). Por Okun mueve el paro; por Phillips la inflación.</p></div>
<div class="card gold"><h2><img class="ico" src="icons/_c/scale_F2B134.svg" width="26" height="26" alt=""> <span style="color:#F2B134">sp</span> · saldo primario</h2><p>Ingresos menos gastos sin intereses. La única palanca que reduce deuda directamente. El vintage arranca con déficit primario; la consolidación (S3) lo mueve +1 pp PIB.</p></div>
</div>

<div class="g2" style="margin-top:12px">
<div class="card"><h2><img class="ico" src="icons/_c/trend_down_13A89E.svg" width="24" height="24" alt=""> r &lt; g → la deuda se diluye sola</h2><p>Aunque no haya superávit, la ratio baja: la economía crece más deprisa que el coste de la deuda. Base 2026: r − g = <b>−0,62 pp</b>.</p></div>
<div class="card coral"><h2><img class="ico" src="icons/_c/warning_F4645A.svg" width="24" height="24" alt=""> r &gt; g → bola de nieve</h2><p>Hace falta superávit primario sólo para que la deuda no crezca. La zona que el crecimiento no absorbe se ensancha cada año sin ninguna decisión nueva de gasto.</p></div>
</div>

---

# Cómo viaja un cambio <span class="sub">subir el tipo no toca la deuda directamente — recorre un camino con coeficientes con nombre</span>

<div class="flow">
<div class="node"><b>1 · Palanca</b>Euríbor 12m sube +2 pp (preset S1).<span class="k">r</span></div><div class="arr">→</div>
<div class="node"><b>2 · Coste de la deuda</b>Sólo el 14 % de la deuda viva se refinancia cada año; el bono 10A se forma como r + TERM + prima.<span class="k">REFI 0,14</span><span class="k">TERM 0,17</span></div><div class="arr">→</div>
<div class="node"><b>3 · Demanda</b>El tipo frena inversión y consumo; el multiplicador amplifica, la persistencia amortigua.<span class="k">E_R 0,45</span><span class="k">MULT 1,4</span><span class="k">RHO 0,62</span></div><div class="arr">→</div>
<div class="node"><b>4 · Empleo y precios</b>Menos PIB es menos g. El paro sube por Okun y arrastra la inflación por Phillips.<span class="k">OKUN 0,48</span><span class="k">KAPPA 0,22</span></div><div class="arr">→</div>
<div class="node"><b>5 · Deuda</b>Menos g y más r vuelven a la identidad: la ratio deuda/PIB se capitaliza más deprisa.<span class="k">b(t+1)</span></div>
</div>

<div class="g2" style="margin-top:10px">
<div class="card"><h2><img class="ico" src="icons/_c/flow_13A89E.svg" width="24" height="24" alt=""> Otros canales</h2><ul>
<li><b>Energía (pᵐ)</b> → inflación importada con decaimiento <code>PM_DECAY 0,45</code>; efecto real <code>E_PM 0,012</code>.</li>
<li><b>Oferta (λ, τ, z)</b> → desplazan la curva de precios (PS) y de salarios (WS): <code>A_LAM 0,45 · A_TAU 0,3 · A_Z 1,1</code>.</li>
<li><b>Vivienda</b> → precio responde al tipo (<code>E_IPV_R 2,6</code>) y al crecimiento (<code>E_IPV_G 1,1</code>); esfuerzo = cuota francesa / salario.</li>
<li><b>Demografía (β₆₅) e indexación (ι)</b> → gasto en pensiones comprometido antes de decidir.</li></ul></div>
<div class="card navy"><h2><img class="ico" src="icons/_c/layer_0B2545.svg" width="24" height="24" alt=""> Por qué las palancas no suman</h2><p>El panel de Inicio descompone el movimiento palanca a palanca: vuelve a correr el motor con una sola palanca movida y compara. Como los canales se refuerzan entre sí, la suma de efectos individuales <b>no iguala</b> el efecto conjunto — la diferencia se dibuja como una barra más, en lugar de repartirla disimuladamente.</p><p><em>Las constantes son calibraciones (v16), no estimaciones sobre estos datos. La pestaña Evidencia declara cuáles son identificables.</em></p></div>
</div>

---

# Arquitectura <span class="sub">de 141 fuentes congeladas a 19 pestañas</span>

<div class="flow">
<div class="node"><b>Fuentes · vintage 2026-07-31</b>141 series congeladas: BCE, Eurostat, INE, AMECO, WEO, PWT, OCDE, Banco Mundial, Polity5. Nada se actualiza en caliente.<span class="k">csv gold/</span></div><div class="arr">→</div>
<div class="node"><b>Capa gold</b>CSVs auditados con manifest: proyecciones, escenarios de deuda, fiscal 1850–2023, panel impagos 1960–2023, panel análogos 1980–2023.<span class="k">pandas</span></div><div class="arr">→</div>
<div class="node"><b>Motor Python</b>Identidad de deuda + 40 series derivadas, Monte Carlo (4.000 × AR(1)), líneas rojas, clasificador de impago, HMM de regímenes, KNN análogos.<span class="k">FastAPI</span><span class="k">numpy</span></div><div class="arr">→</div>
<div class="node"><b>Motor TypeScript</b>Réplica del motor en el navegador con paridad verificada (fixtures compartidos). El escenario te sigue entre páginas sin latencia.<span class="k">React</span><span class="k">Vite</span><span class="k">Zustand</span></div><div class="arr">→</div>
<div class="node"><b>Interfaz</b>Inicio · 12 perfiles · Laboratorio · Biblioteca · Evidencia · Predicción · Cómo funciona · Datos y método.<span class="k">19 pestañas</span></div>
</div>

<div class="g3" style="margin-top:10px">
<div class="card "><h2><img class="ico" src="icons/_c/globe_13A89E.svg" width="26" height="26" alt=""> Frontend · GitHub Pages</h2><p><code>danribes.github.io/tfm-data-science</code><br>Build Vite en cada push a <code>main</code>. 248 tests (Vitest + MSW).</p></div>
<div class="card navy"><h2><img class="ico" src="icons/_c/db_0B2545.svg" width="26" height="26" alt=""> API · Hugging Face Spaces</h2><p><code>danribes-evo-espana-api.hf.space</code><br>Docker · FastAPI. Duerme sin uso (≈1 min de arranque). 382 tests pytest.</p></div>
<div class="card gold"><h2><img class="ico" src="icons/_c/shield_F2B134.svg" width="26" height="26" alt=""> Reproducibilidad</h2><p>Semilla fija (42), vintage inmutable, constantes en un solo fichero, paridad Python ↔ TS por fixtures. El corpus de la Biblioteca nunca sale de la máquina local.</p></div>
</div>

---

<!-- _class: divider -->

<span style="font-size:0.9em;opacity:.8">02</span>

# Cómo se opera

## punto de partida · palancas · presets · horizonte · lectura de resultados

---

# Punto de partida <span class="sub">la línea base del vintage, con todas las palancas en su valor observado</span>

<div class="g2">
<div>
<img class="shot" src="media/crop_levers_panel.png" style="max-height:470px;width:auto">
<p class="cap">Panel izquierdo: presets, 10 deslizadores, horizonte y «volver a base». El escenario te sigue entre páginas.</p>
</div>
<div>
<h3>España 2026 · observado</h3>
<div class="g2" style="gap:10px">
<div class="kpi coral"><div class="num">106,3<small>%PIB</small></div><div class="lbl">Deuda pública</div></div>
<div class="kpi coral"><div class="num">−4,2<small>%PIB</small></div><div class="lbl">Saldo público</div></div>
<div class="kpi "><div class="num">10,1<small>%</small></div><div class="lbl">Paro</div></div>
<div class="kpi "><div class="num">3,0<small>%</small></div><div class="lbl">IPCA</div></div>
<div class="kpi navy"><div class="num">3,42<small>%</small></div><div class="lbl">Bono 10A</div></div>
<div class="kpi navy"><div class="num">−0,62<small>pp</small></div><div class="lbl">r − g (el crecimiento diluye)</div></div>
</div>
<h3 style="margin-top:10px">Senda central sin tocar nada</h3>
<p style="font-size:0.85em">Deuda 2050: <b>223,8 %PIB</b> · saldo −15,0 · la economía ×2,2 y la deuda ×4,6. No es un pronóstico: es lo que implica mantener el déficit primario del vintage 24 años.</p>
</div>
</div>

---

<!-- _class: dense -->
# Las 10 palancas <span class="sub">los rangos son la envolvente de lo que cada variable ha hecho históricamente</span>

<table>
<tr><th></th><th>Palanca</th><th>Canal</th><th class="n">Base</th><th class="n">Rango</th><th>Fuente del vintage</th></tr>
<tr><td><b>r</b></td><td>Tipo de interés · Euríbor 12m</td><td><span class="pill coral">financiero</span></td><td class="n">2,80 %</td><td class="n">0 … 6</td><td>ecb_euribor12m · 2026-06</td></tr>
<tr><td><b>σ</b></td><td>Prima de riesgo · spread ES–DE</td><td><span class="pill coral">financiero</span></td><td class="n">45 pb</td><td class="n">0 … 400</td><td>ecb_bono10y es/de · 2026-06</td></tr>
<tr><td><b>sp</b></td><td>Saldo primario · Δ vs central</td><td><span class="pill gold">fiscal</span></td><td class="n">0,0 pp PIB</td><td class="n">−4 … +4</td><td>gold_escenarios_deuda (central)</td></tr>
<tr><td><b>τ</b></td><td>Presión fiscal · cuña laboral</td><td><span class="pill gold">fiscal</span></td><td class="n">0,00 pp</td><td class="n">−5 … +5</td><td>Eurostat GFS · desplaza la WS</td></tr>
<tr><td><b>λ</b></td><td>Productividad</td><td><span class="pill teal">oferta</span></td><td class="n">0,9 %/año</td><td class="n">−0,5 … 2,5</td><td>PWT + INE · desplaza la PS</td></tr>
<tr><td><b>z</b></td><td>Instituciones laborales</td><td><span class="pill teal">oferta</span></td><td class="n">0,0 índice</td><td class="n">−2 … +2</td><td>OECD/Eurostat · desplaza la WS</td></tr>
<tr><td><b>pᵐ</b></td><td>Precio importaciones / energía</td><td><span class="pill">exterior</span></td><td class="n">0 % a/a</td><td class="n">−50 … +100</td><td>WEO commodity prices</td></tr>
<tr><td><b>Y*</b></td><td>Demanda externa</td><td><span class="pill">exterior</span></td><td class="n">1,8 % a/a</td><td class="n">−4 … +6</td><td>WEO · canal exterior</td></tr>
<tr><td><b>β₆₅</b></td><td>Presión demográfica</td><td><span class="pill navy">estructural</span></td><td class="n">0,00 ×</td><td class="n">−1 … +1</td><td>gold_projections · 6 variantes INE</td></tr>
<tr><td><b>ι</b></td><td>Indexación pensiones / nóminas</td><td><span class="pill navy">estructural</span></td><td class="n">0,0 IPC+pp</td><td class="n">−1,5 … +1</td><td>regla de revalorización</td></tr>
</table>

<p class="cap">Cada deslizador muestra su fuente y fecha de corte debajo. No puedes poner el Euríbor al 40 % porque el modelo no está calibrado ahí. β₆₅ ofrece las variantes demográficas del INE (migración alta/baja, fecundidad baja, mortalidad baja, sin migración).</p>

---

# Los 8 presets <span class="sub">escenarios de un clic — cada uno mueve una o tres palancas y deja el resto en base</span>

<div class="g4">
<div class="card navy"><h2><img class="ico" src="icons/_c/home_0B2545.svg" width="26" height="26" alt=""> S0 · base</h2><p>Todas las palancas en su valor observado. Senda central del vintage.</p><p><code>—</code></p></div>
<div class="card coral"><h2><img class="ico" src="icons/_c/trend_up_F4645A.svg" width="26" height="26" alt=""> S1 · tipos +200 pb</h2><p>Euríbor de 2,80 % a 4,80 %. Prueba el canal financiero puro.</p><p><code>r = 4,80</code></p></div>
<div class="card gold"><h2><img class="ico" src="icons/_c/warning_F2B134.svg" width="26" height="26" alt=""> S2 · petróleo +50 %</h2><p>Choque de precios importados con decaimiento. Prueba el canal de inflación.</p><p><code>pᵐ = +50</code></p></div>
<div class="card "><h2><img class="ico" src="icons/_c/scale_13A89E.svg" width="26" height="26" alt=""> S3 · consolidación</h2><p>Saldo primario +1 pp PIB sostenido. La única palanca que ataca la deuda directamente.</p><p><code>sp = +1,0</code></p></div>
<div class="card "><h2><img class="ico" src="icons/_c/rocket_13A89E.svg" width="26" height="26" alt=""> S4 · productividad</h2><p>De 0,9 a 1,4 %/año. Prueba el canal de crecimiento (g).</p><p><code>λ = 1,4</code></p></div>
<div class="card "><h2><img class="ico" src="icons/_c/briefcase_13A89E.svg" width="26" height="26" alt=""> S5 · desregulación laboral</h2><p>Instituciones −1 y cuña fiscal −1,5. Desplaza la curva de salarios.</p><p><code>z = −1,0 · τ = −1,5</code></p></div>
<div class="card gold"><h2><img class="ico" src="icons/_c/sun_F2B134.svg" width="26" height="26" alt=""> S6 · envejecimiento</h2><p>Presión demográfica +0,6. Pensiones comprometidas antes de decidir.</p><p><code>β₆₅ = +0,6</code></p></div>
<div class="card coral"><h2><img class="ico" src="icons/_c/dismiss_F4645A.svg" width="26" height="26" alt=""> S7 · adverso</h2><p>Tipos +200 pb, petróleo +50 % y prima a 150 pb a la vez. Choque combinado.</p><p><code>r = 4,80 · pᵐ = 50 · σ = 150</code></p></div>
</div>

<p class="cap" style="margin-top:12px">Los presets son un punto de partida: después puedes mover cualquier otro deslizador. El pill del preset activo cambia a «condicional» y cada KPI muestra su Δ vs base.</p>

---

# El panel de control <span class="sub">cinco gestos bastan para operar el modelo</span>

<div class="g2" style="grid-template-columns: 0.9fr 1.1fr">
<img class="shot" src="media/scen_S7_top.png" style="max-height:400px;width:auto">
<div>
<div class="card" style="margin-bottom:8px"><h2><span class="num-c">1</span>Elige un preset o parte de base</h2><p>S0…S7 arriba del panel. El pill «condicional · 2026» indica que el escenario ya no es la base.</p></div>
<div class="card" style="margin-bottom:8px"><h2><span class="num-c">2</span>Mueve deslizadores</h2><p>Cada uno con símbolo, nombre, unidad, valor y fuente. Los movidos se resaltan en morado.</p></div>
<div class="card" style="margin-bottom:8px"><h2><span class="num-c">3</span>Fija el horizonte</h2><p>2026 · 2030 · 2035 · 2040 · 2050. Las líneas rojas y los KPIs se evalúan en ese año.</p></div>
<div class="card" style="margin-bottom:8px"><h2><span class="num-c">4</span>Lee la Δ vs base</h2><p>Cada KPI muestra el nivel y cuánto se debe a ti. Todo lo demás ya estaba en los datos.</p></div>
<div class="card"><h2><span class="num-c">5</span>Cambia de pestaña</h2><p>El escenario te sigue: los 12 perfiles y el Laboratorio recalculan con tus palancas. «↺ volver a base» lo deshace.</p></div>
</div>
</div>

---

# Cómo leer los resultados <span class="sub">cuatro tipos de salida, cuatro lecturas distintas</span>

<div class="g4">
<div class="card navy"><h2><img class="ico" src="icons/_c/gauge_0B2545.svg" width="26" height="26" alt=""> KPIs con Δ vs base</h2><p><b>Nivel</b> en el año del horizonte y <b>diferencia</b> respecto a la base congelada. La Δ es lo único que has causado tú. Badge «dato observado» cuando el año es 2026.</p></div>
<div class="card "><h2><img class="ico" src="icons/_c/chart_13A89E.svg" width="26" height="26" alt=""> Abanico Monte Carlo</h2><p>4.000 trayectorias con choques AR(1) sobre tipo, crecimiento y saldo. Mira la <b>anchura</b> p5–p95, no la mediana. Semilla 42: dos personas ven lo mismo.</p></div>
<div class="card coral"><h2><img class="ico" src="icons/_c/warning_F4645A.svg" width="26" height="26" alt=""> Líneas rojas</h2><p>9 umbrales anclados a episodios reales. Estado <b>calculado</b> cada año: <span class="st safe">segura</span> <span class="st near">cerca</span> <span class="st cross">cruzada</span>. «Cerca» = 10 % del umbral. Una línea cruzada en base ya lo estaba hoy.</p></div>
<div class="card gold"><h2><img class="ico" src="icons/_c/shield_F2B134.svg" width="26" height="26" alt=""> Probabilidad de impago</h2><p>Clasificador sobre 377 impagos reales 1960–2023. AUC 0,674: ordena razonablemente pero no calibra un nivel. Lee la <b>posición relativa</b> frente a la tasa base 9,7 %.</p></div>
</div>

<div class="g2" style="margin-top:12px">
<div class="card"><h2><img class="ico" src="icons/_c/search_13A89E.svg" width="24" height="24" alt=""> Descomposición palanca a palanca</h2><p>El bloque «Qué está pasando» de Inicio vuelve a correr el motor con una sola palanca movida y compara. La barra de interacción es la parte que no se reparte.</p></div>
<div class="card"><h2><img class="ico" src="icons/_c/history_13A89E.svg" width="24" height="24" alt=""> Análogos históricos</h2><p>Los 3 país-año más parecidos a tu escenario (Mahalanobis sobre 6 rasgos), cómo evolucionaron después, y en qué se diferencia España estructuralmente.</p></div>
</div>

---

<!-- _class: dense -->
# Las 9 líneas rojas <span class="sub">umbrales con fuente, evaluados en 2026 sobre la base</span>

<table>
<tr><th>Línea roja</th><th class="n">Umbral</th><th class="n">Base 2026</th><th>Estado</th><th>Ancla histórica / regla</th></tr>
<tr><td>Bono 10A</td><td class="n">&gt; 7 %</td><td class="n">3,42</td><td><span class="st safe">segura</span></td><td>Zona rescate: GRC/PRT/IRL pidieron rescate con bonos ≈7 %; ES tocó 7,6 % en jul-2012</td></tr>
<tr><td>Paro</td><td class="n">&gt; 26,9 %</td><td class="n">10,1</td><td><span class="st safe">segura</span></td><td>Máximo histórico ES (T1-2013)</td></tr>
<tr><td>Déficit</td><td class="n">&gt; 3 % PIB</td><td class="n">−4,2</td><td><span class="st cross">cruzada</span></td><td>Umbral de Maastricht (regla UE)</td></tr>
<tr><td>Déficit</td><td class="n">&gt; 11,3 % PIB</td><td class="n">−4,2</td><td><span class="st safe">segura</span></td><td>Suelo 2009: ES −11,3 % PIB</td></tr>
<tr><td>Deuda</td><td class="n">&gt; 105 % PIB</td><td class="n">106,3</td><td><span class="st cross">cruzada</span></td><td>crack23: «deuda brutal que ya está por encima del 105 %»</td></tr>
<tr><td>Deuda</td><td class="n">&gt; 120 % PIB</td><td class="n">106,3</td><td><span class="st safe">segura</span></td><td>≈ pico COVID ES 2020: 119,3</td></tr>
<tr><td>Inflación</td><td class="n">&gt; 10 %</td><td class="n">3,0</td><td><span class="st safe">segura</span></td><td>Ola inflacionaria 2022: ES pico 10,8 % jul-2022</td></tr>
<tr><td>Esfuerzo vivienda</td><td class="n">&gt; 40 %</td><td class="n">42,6</td><td><span class="st cross">cruzada</span></td><td>Definición Eurostat de sobrecarga (housing cost overburden)</td></tr>
<tr><td>Pobreza infantil</td><td class="n">&gt; 30 %</td><td class="n">28,5</td><td><span class="st near">cerca</span></td><td>ES 27–28 % crónico, 30 % en picos post-2013; media UE ≈19 %</td></tr>
</table>

<div class="note"><img class="ico" src="icons/_c/bulb_F2B134.svg" width="18" height="18" alt=""> Tres líneas ya están cruzadas en la base y una en banda de aviso. Que un escenario las muestre cruzadas no significa que las haya roto — significa que España ya está por encima hoy. El estado se recalcula en el año del horizonte.</div>

---

<!-- _class: divider -->

<span style="font-size:0.9em;opacity:.8">03</span>

# Recorrido por las pestañas

## Inicio · 12 perfiles · Laboratorio · Biblioteca · Evidencia · Predicción · método

---

# Inicio <span class="sub">el problema de la deuda en una pantalla</span>

<div class="g2" style="grid-template-columns: 1.15fr 0.85fr">
<img class="shot" src="media/01_inicio_top.png">
<div>
<div class="card" style="margin-bottom:8px"><h2><img class="ico" src="icons/_c/chart_13A89E.svg" width="22" height="22" alt=""> El problema de la deuda</h2><p>60 de las 4.000 trayectorias como hebras finas; la mediana gruesa. Donde se abren en abanico el modelo no distingue futuros. Casi ninguna vuelve a bajar.</p></div>
<div class="card" style="margin-bottom:8px"><h2><img class="ico" src="icons/_c/gauge_13A89E.svg" width="22" height="22" alt=""> Cuatro KPIs</h2><p>Deuda 2050, saldo, paro e IPCA con Δ vs base y badge de dato observado / proyectado.</p></div>
<div class="card" style="margin-bottom:8px"><h2><img class="ico" src="icons/_c/trend_up_13A89E.svg" width="22" height="22" alt=""> Por qué cuesta devolverla</h2><p>Deuda y PIB en índice 2026 = 100 y el término r − g. La zona sombreada es la deuda que el crecimiento no absorbe.</p></div>
<div class="card"><h2><img class="ico" src="icons/_c/history_13A89E.svg" width="22" height="22" alt=""> Siglo y medio de calma y crisis</h2><p>Saldo español 1850–2023 con regímenes detectados por un HMM de 2 estados — no anotados a mano.</p></div>
</div>
</div>

---

# Inicio · segunda mitad <span class="sub">de la macro al bolsillo, líneas rojas, impago, perfiles y narrativa</span>

<div class="g3">
<div><img class="shot" src="media/crop_c_hmm.png"><p class="cap"><b>Regímenes 1850–2023.</b> HMM gaussiano de 2 estados ajustado sólo al saldo separa el Sexenio, la Gran Guerra, la posguerra y 2008–2023. El saldo español alterna entre dos mundos; las líneas rojas están ancladas en el malo.</p></div>
<div><img class="shot" src="media/crop_c_redlines.png"><p class="cap"><b>Líneas rojas.</b> Umbral, valor, estado y fuente. Se recalculan en el año del horizonte.</p></div>
<div><img class="shot" src="media/crop_c_pd.png"><p class="cap"><b>Probabilidad de impago.</b> 1,74 % frente a 9,7 % de tasa base (6× por debajo). España no está en la base de impagos: el modelo la puntúa sin haberla visto.</p>
<div class="card navy" style="margin-top:6px"><h2><img class="ico" src="icons/_c/people_0B2545.svg" width="20" height="20" alt=""> 12 perfiles + «Qué está pasando»</h2><p>Rejilla de perfiles con su pregunta, y un texto determinista que explica qué líneas rojas cruza el escenario y por qué. Sin IA en producción pública.</p></div></div>
</div>

---

# Los 12 perfiles <span class="sub">el mismo número, visto desde abajo — cada uno hace una pregunta concreta</span>

<div class="g4" style="gap:10px">
<div class="persona"><img class="ico" src="icons/_c/money_13A89E.svg" width="30" height="30" alt=""><div><b>💼 Bonista</b><span>Inversor en bonos: ¿me pagarán los 10 años?</span></div></div>
<div class="persona"><img class="ico" src="icons/_c/bank_13A89E.svg" width="30" height="30" alt=""><div><b>🏦 Banca</b><span>Banco hipotecario: ¿a quién presto, a qué tipo y con qué mora esperada?</span></div></div>
<div class="persona"><img class="ico" src="icons/_c/key_13A89E.svg" width="30" height="30" alt=""><div><b>🔑 Comprador</b><span>Comprador de vivienda: ¿qué esfuerzo me exige el techo?</span></div></div>
<div class="persona"><img class="ico" src="icons/_c/rocket_13A89E.svg" width="30" height="30" alt=""><div><b>🚀 Emprendedor</b><span>¿Aguanta el ciclo lo que tarda mi empresa en nacer?</span></div></div>
<div class="persona"><img class="ico" src="icons/_c/building_13A89E.svg" width="30" height="30" alt=""><div><b>🏛️ Funcionario</b><span>¿Mi nómina real sobrevive al ajuste que viene?</span></div></div>
<div class="persona"><img class="ico" src="icons/_c/vote_13A89E.svg" width="30" height="30" alt=""><div><b>🗳️ Político</b><span>¿Qué palanca puedo mover sin cruzar una línea roja?</span></div></div>
<div class="persona"><img class="ico" src="icons/_c/eyeoff_F4645A.svg" width="30" height="30" alt=""><div><b>🕳️ Corrupto</b><span>¿Dónde no mira nadie? — partidas con más discrecionalidad, señaladas para quien SÍ mira</span></div></div>
<div class="persona"><img class="ico" src="icons/_c/child_F2B134.svg" width="30" height="30" alt=""><div><b>🧒 Infancia</b><span>¿Qué país hereda quien hoy tiene 8 años?</span></div></div>
<div class="persona"><img class="ico" src="icons/_c/sun_F2B134.svg" width="30" height="30" alt=""><div><b>🌅 Jubilado</b><span>¿Mi pensión sigue al IPC — y quién la paga en 2035?</span></div></div>
<div class="persona"><img class="ico" src="icons/_c/grad_13A89E.svg" width="30" height="30" alt=""><div><b>🎓 Joven</b><span>¿Primer contrato o cola del paro — y podré irme de casa?</span></div></div>
<div class="persona"><img class="ico" src="icons/_c/doc_13A89E.svg" width="30" height="30" alt=""><div><b>📋 Indefinido</b><span>¿Crece mi salario por encima del IPC?</span></div></div>
<div class="persona"><img class="ico" src="icons/_c/receipt_13A89E.svg" width="30" height="30" alt=""><div><b>🧾 Autónomo</b><span>¿Caja, cuota y ciclo — en qué orden me golpean?</span></div></div>
</div>

<div class="g2" style="margin-top:10px">
<div class="card"><h2><img class="ico" src="icons/_c/layer_13A89E.svg" width="22" height="22" alt=""> Anatomía de un perfil</h2><p>Pregunta · 5–6 KPIs con badge «dato observado · vintage» o «proyectado» y Δ vs base · histórico observado (sparkline) · proyección 2026–2050 escenario vs base · fuentes al pie.</p></div>
<div class="card navy"><h2><img class="ico" src="icons/_c/flow_0B2545.svg" width="22" height="22" alt=""> Cómo llega la macro a cada uno</h2><p>Bono 10A → cuota hipotecaria (fórmula francesa) · intereses → gasto que nadie elige · g → paro (Okun) y salario real (Phillips) · prima → crédito y mora · β₆₅ e ι → pensiones.</p></div>
</div>

---

# Dos perfiles en detalle <span class="sub">Comprador de vivienda · Jubilado</span>

<div class="g2">
<div><img class="shot" src="media/p03_top.png"><p class="cap"><b>🔑 Comprador.</b> Precio de la vivienda (€/m²), cuota mensual, esfuerzo (%), salario, sobrecarga. La cuota sale del bono 10A vía Euríbor; el precio responde al tipo (E_IPV_R 2,6) y al crecimiento. Esfuerzo 42,6 % en 2026: línea roja cruzada ya en base.</p></div>
<div><img class="shot" src="media/p09_top.png"><p class="cap"><b>🌅 Jubilado.</b> Gasto en pensiones (%PIB), poder de compra, IPC, dependencia 65+, esperanza de vida. La regla de revalorización (ι) y la tasa de dependencia (β₆₅) deciden cuánto del gasto futuro está comprometido antes de empezar a decidir.</p></div>
</div>

<div class="note"><img class="ico" src="icons/_c/bulb_F2B134.svg" width="18" height="18" alt=""> Mueve S6 (envejecimiento) y salta al Jubilado; mueve S1 (tipos) y salta al Comprador. La Δ vs base de cada KPI es la única parte causada por ti.</div>

---

# Laboratorio · explorar y cuantificar la incertidumbre <span class="sub">40 series, abanico Monte Carlo, palancas en crudo</span>

<div class="g2" style="grid-template-columns: 1.4fr 0.6fr">
<div><img class="shot" src="media/crop_l_series.png" style="height:340px;width:auto;max-width:100%"><p class="cap"><b>Explorador de series.</b> Cualquiera de las 40 series del motor (b, u, pi, g, bono, esf, pensiones, salario real…): línea continua = tu escenario; punteada = base congelada; líneas rojas dibujadas donde aplican.</p></div>
<div><img class="shot" src="media/crop_l_mc.png" style="height:340px;width:auto;max-width:100%"><p class="cap"><b>Abanico Monte Carlo hasta 2070.</b> 4.000 trayectorias, bandas p5–p95 y p25–p75, mediana p50. Se calcula en el servidor (Python) y se valida contra la envolvente dorada con tolerancia ±2 pp en 2030/2050/2070.</p></div>
</div>

<div class="card" style="margin-top:6px"><h2><img class="ico" src="icons/_c/doc_13A89E.svg" width="22" height="22" alt=""> Informe de política pública · versión imprimible</h2><p>Botón en cabecera: genera un informe determinista con las cifras del escenario activo, listo para imprimir o adjuntar.</p></div>

---

# Laboratorio · a dónde va cada euro <span class="sub">Sankey fiscal y acumulación de deuda, por año de proyección</span>

<div class="g2">
<div><img class="shot" src="media/crop_l_sankey.png"><p class="cap"><b>Flujo de ingresos y gastos del Estado.</b> Impuestos directos, indirectos, cotizaciones y financiación del déficit → pensiones, sanidad, educación, intereses, inversión. Selector de año 2026–2050. Recaudación total y gasto total en %PIB.</p></div>
<div><img class="shot" src="media/crop_l_debtflow.png"><p class="cap"><b>Flujo presupuestario y acumulación de deuda.</b> Deuda al inicio → ingresos, gastos y la fracción del déficit que se convierte en NEW DEBT → deuda al final del año. Ratio deuda/PIB frente al límite del 100 % del PIB anual.</p></div>
</div>

---

# Laboratorio · qué mueve la deuda <span class="sub">matriz de sensibilidad (∂Y/∂L) y gemelo empírico</span>

<div class="g2" style="grid-template-columns: 1.1fr 0.9fr">
<div>
<h3>Deuda 2050 si cada palanca se mueve de tope a tope</h3>
<div class="bar"><span>r · Euríbor 12m</span><div><div class="t " style="width:100%"></div></div><span class="v">+205 pp</span></div>
<div class="bar"><span>β₆₅ · Presión demográfica</span><div><div class="t " style="width:94%"></div></div><span class="v">+194 pp</span></div>
<div class="bar"><span>σ · Prima de riesgo</span><div><div class="t " style="width:56%"></div></div><span class="v">+115 pp</span></div>
<div class="bar"><span>λ · Productividad</span><div><div class="t dn" style="width:52%"></div></div><span class="v">−107 pp</span></div>
<div class="bar"><span>sp · Saldo primario</span><div><div class="t dn" style="width:51%"></div></div><span class="v">−104 pp</span></div>
<div class="bar"><span>Y* · Demanda externa</span><div><div class="t dn" style="width:15%"></div></div><span class="v">−30 pp</span></div>
<div class="bar"><span>pᵐ · Energía</span><div><div class="t dn" style="width:3%"></div></div><span class="v">−6 pp</span></div>
<div class="bar"><span>τ · z · ι</span><div><div class="t " style="width:0%"></div></div><span class="v">−0 pp</span></div>
<p class="cap">Única columna que se puede leer hacia abajo: hace la misma pregunta a todas las palancas. Las derivadas por unidad (en gris en la app) no son comparables entre filas — β₆₅ marca +96,9 frente a +34,2 del tipo, y sin embargo, de tope a tope, el tipo pesa más.</p>
</div>
<div><img class="shot" src="media/crop_l_twin.png" style="max-height:300px;width:auto"><p class="cap"><b>El gemelo empírico.</b> ¿Pega igual un tipo al 60 % que al 120 % de deuda? Panel externo de 2.816 país-año (140 países, 1981–2021), árboles + SHAP por régimen de deuda. Resultado: <b>no distinguible</b> — el IC bootstrap incluye el cero; la constante del motor sobrevive, «no contradicha», que es menos que validada y se dice tal cual.</p></div>
</div>

---

# Laboratorio · análogos históricos <span class="sub">¿a qué país-año se parece tu escenario y qué pasó después?</span>

<div class="g2" style="grid-template-columns: 1.05fr 0.95fr">
<img class="shot" src="media/analog_results.png">
<div>
<div class="flow" style="margin-top:0">
<div class="node"><b>Consulta</b>6 rasgos del escenario en el horizonte: deuda, saldo, bono 10A, crecimiento, paro, inflación.<span class="k">z-score</span></div><div class="arr">→</div>
<div class="node"><b>Búsqueda</b>KNN con distancia de Mahalanobis sobre 6.370 país-año (120+ países, 1980–2023). Bonus 20 % si el país-año destaca en la palanca dominante.<span class="k">k = 3</span></div><div class="arr">→</div>
<div class="node"><b>Lectura</b>Trayectoria posterior hasta el horizonte, veredicto r − g y 8 diferencias estructurales con España.<span class="k">✓ ✗ ≈</span></div>
</div>
<div class="card" style="margin-top:8px"><h2><img class="ico" src="icons/_c/scale_13A89E.svg" width="22" height="22" alt=""> Veredicto de Blanchard</h2><p><span class="st safe">AUTO-LIQUIDABLE</span> r &lt; g − 0,5 &nbsp; <span class="st near">LÍMITE</span> |r − g| &lt; 0,5 pp &nbsp; <span class="st cross">REQUIERE SUPERÁVIT</span> r &gt; g + 0,5</p></div>
<div class="card gold" style="margin-top:8px"><h2><img class="ico" src="icons/_c/layer_F2B134.svg" width="22" height="22" alt=""> 8 diferencias estructurales</h2><p>Zona euro · régimen cambiario · deuda externa / total · calidad institucional (Polity5) · apertura comercial · vencimiento de la deuda · tendencia TFP · productividad laboral. Cada una con ✓ converge, ✗ diverge, ≈ neutral, y «sin datos» cuando el panel no cubre.</p></div>
<p class="cap">Narrativa por IA sobre el corpus sólo en despliegue local; en público, plantilla determinista.</p>
</div>
</div>

---

# Biblioteca y Evidencia <span class="sub">preguntar al corpus · declarar qué está calibrado y qué estimado</span>

<div class="g2">
<div><img class="shot" src="media/biblioteca_top.png"><p class="cap"><b>Biblioteca.</b> Preguntas sobre el escenario y la deuda respondidas <b>sólo desde pasajes</b> del corpus (RAG). Si el corpus no cubre la pregunta, se dice. Evaluación publicada sobre preguntas dorada (aciertos, cobertura, fidelidad). El corpus nunca sale de la máquina local.</p></div>
<div><img class="shot" src="media/evidencia_top.png"><p class="cap"><b>Evidencia.</b> Tabla de constantes del motor: valor calibrado, valor estimado sobre el vintage cuando es posible, banda, y veredicto de identificabilidad. Declara explícitamente qué coeficientes no se pueden estimar con los datos congelados — un revisor puede discutirlos, y debería.</p></div>
</div>

---

# Predicción · Cómo funciona · Datos y método <span class="sub">contraste fuera de muestra, guía del motor y trazabilidad de datos</span>

<div class="g3">
<div><img class="shot" src="media/prediccion_top.png"><p class="cap"><b>Predicción.</b> Contraste del motor fuera de muestra: acierto direccional por comunidad y error por horizonte. Publica lo que acierta y lo que no, con el drift entre vintages.</p></div>
<div><img class="shot" src="media/como-funciona_top.png"><p class="cap"><b>Cómo funciona.</b> Siete secciones: la pregunta, la identidad, las 10 palancas, cómo viaja un cambio, cómo leer el abanico, qué significan las líneas rojas, qué no puede decirte.</p></div>
<div><img class="shot" src="media/metodologia_top.png"><p class="cap"><b>Datos y método.</b> Vintage 2026-07-31 con 141 fuentes congeladas y sus fechas de corte, paridad Python ↔ TypeScript por fixtures, constantes del motor con origen, huecos de datos conocidos.</p></div>
</div>

---

<!-- _class: divider -->

<span style="font-size:0.9em;opacity:.8">04</span>

# Escenarios ilustrativos

## cuatro casos de extremo a extremo, con números de la API en producción

---

# Escenario S1 · tipos +200 pb <span class="sub">Euríbor 2,80 → 4,80 %, todo lo demás en base</span>

<div class="g2" style="grid-template-columns: 1.05fr 0.95fr">
<div><img class="shot" src="media/scen_S1_top.png"><p class="cap">Inicio con el preset aplicado: los deslizadores movidos en morado, pill «condicional», KPIs con Δ vs base.</p></div>
<div>
<h3>Horizonte 2050 · Δ vs base</h3>
<div class="g3" style="gap:8px"><div class="kpi coral"><div class="num">306,9<small>%PIB</small></div><div class="lbl">Deuda 2050</div><div class="d"><span class="up">+83,1 vs base</span></div></div><div class="kpi coral"><div class="num">−23,3<small>%PIB</small></div><div class="lbl">Saldo 2050</div><div class="d"><span class="up">−8,3</span></div></div><div class="kpi coral"><div class="num">5,4<small>%</small></div><div class="lbl">Bono 10A</div><div class="d"><span class="up">+2,0</span></div></div><div class="kpi "><div class="num">10,7<small>%</small></div><div class="lbl">Paro 2050</div><div class="d"><span class="up">+0,6</span></div></div><div class="kpi "><div class="num">2,7<small>%</small></div><div class="lbl">IPCA 2050</div><div class="d"><span class="dn">−0,3</span></div></div><div class="kpi gold"><div class="num">15,5<small>%</small></div><div class="lbl">Esfuerzo vivienda</div><div class="d"><span class="dn">−24,3</span></div></div></div>
<h3 style="margin-top:8px">Líneas rojas en 2050</h3>
<p style="font-size:0.82em"><span class="st cross">cruzada</span> déficit &gt; 3 · deuda &gt; 105 · deuda &gt; 120 &nbsp; <span class="st near">cerca</span> pobreza infantil &nbsp; <span class="st safe">segura</span> bono, paro, inflación, esfuerzo</p>
<h3 style="margin-top:8px">Lectura</h3>
<ul style="font-size:0.85em"><li>El canal financiero puro: +2 pp de tipo son <b>+83 pp de deuda</b> en 2050 — la palanca más pesada de tope a tope.</li><li>Entra despacio (REFI 14 %/año) pero, una vez dentro, tarda años en salir.</li><li>El esfuerzo de vivienda <b>baja</b>: el precio cae (E_IPV_R 2,6) más de lo que sube la cuota. Un resultado que hay que leer con cuidado, no celebrar.</li></ul>
</div>
</div>

---

# Escenario S3 · consolidación fiscal <span class="sub">saldo primario +1 pp PIB sostenido 24 años</span>

<div class="g2" style="grid-template-columns: 1.05fr 0.95fr">
<div><img class="shot" src="media/scen_S3_top.png"><p class="cap">Inicio con el preset aplicado: los deslizadores movidos en morado, pill «condicional», KPIs con Δ vs base.</p></div>
<div>
<h3>Horizonte 2050 · Δ vs base</h3>
<div class="g3" style="gap:8px"><div class="kpi "><div class="num">210,3<small>%PIB</small></div><div class="lbl">Deuda 2050</div><div class="d"><span class="dn">−13,5 vs base</span></div></div><div class="kpi "><div class="num">−13,5<small>%PIB</small></div><div class="lbl">Saldo 2050</div><div class="d"><span class="dn">+1,5</span></div></div><div class="kpi navy"><div class="num">3,4<small>%</small></div><div class="lbl">Bono 10A</div><div class="d">=</div></div><div class="kpi coral"><div class="num">10,8<small>%</small></div><div class="lbl">Paro 2050</div><div class="d"><span class="up">+0,7</span></div></div><div class="kpi "><div class="num">2,7<small>%</small></div><div class="lbl">IPCA 2050</div><div class="d"><span class="dn">−0,3</span></div></div><div class="kpi coral"><div class="num">44,2<small>%</small></div><div class="lbl">Esfuerzo vivienda</div><div class="d"><span class="up">+4,4</span></div></div></div>
<h3 style="margin-top:8px">Líneas rojas en 2050</h3>
<p style="font-size:0.82em"><span class="st cross">cruzada</span> déficit &gt; 3 · deuda &gt; 105 · deuda &gt; 120 · <b>esfuerzo &gt; 40</b> &nbsp; <span class="st near">cerca</span> pobreza infantil</p>
<h3 style="margin-top:8px">Lectura</h3>
<ul style="font-size:0.85em"><li>La única palanca que ataca la deuda directamente: <b>−13,5 pp</b> en 2050 — pero la ratio sigue creciendo porque el déficit primario del vintage no se cierra con 1 pp.</li><li>Coste: el ajuste frena la demanda (MULT 1,4): paro +0,7 y esfuerzo de vivienda cruza la línea roja.</li><li>Ilustra el dilema del perfil 🗳️ Político: qué palanca mover sin cruzar una línea roja.</li></ul>
</div>
</div>

---

# Escenario S4 · productividad <span class="sub">λ de 0,9 a 1,4 %/año — el canal del crecimiento</span>

<div class="g2" style="grid-template-columns: 1.05fr 0.95fr">
<div><img class="shot" src="media/scen_S4_top.png"><p class="cap">Inicio con el preset aplicado: los deslizadores movidos en morado, pill «condicional», KPIs con Δ vs base.</p></div>
<div>
<h3>Horizonte 2050 · Δ vs base</h3>
<div class="g3" style="gap:8px"><div class="kpi "><div class="num">206,9<small>%PIB</small></div><div class="lbl">Deuda 2050</div><div class="d"><span class="dn">−16,9 vs base</span></div></div><div class="kpi "><div class="num">−14,4<small>%PIB</small></div><div class="lbl">Saldo 2050</div><div class="d"><span class="dn">+0,6</span></div></div><div class="kpi "><div class="num">3,2<small>%</small></div><div class="lbl">Crecimiento real</div><div class="d"><span class="dn">+0,5</span></div></div><div class="kpi "><div class="num">9,9<small>%</small></div><div class="lbl">Paro 2050</div><div class="d"><span class="dn">−0,2</span></div></div><div class="kpi navy"><div class="num">3,0<small>%</small></div><div class="lbl">IPCA 2050</div><div class="d">=</div></div><div class="kpi coral"><div class="num">40,2<small>%</small></div><div class="lbl">Esfuerzo vivienda</div><div class="d"><span class="up">+0,4</span></div></div></div>
<h3 style="margin-top:8px">Líneas rojas en 2050</h3>
<p style="font-size:0.82em"><span class="st cross">cruzada</span> déficit &gt; 3 · deuda &gt; 105 · deuda &gt; 120 · esfuerzo &gt; 40 (por décimas) &nbsp; <span class="st near">cerca</span> pobreza infantil</p>
<h3 style="margin-top:8px">Lectura</h3>
<ul style="font-size:0.85em"><li>Medio punto de productividad reduce la deuda <b>más que un punto de consolidación</b> (−16,9 vs −13,5) y sin subir el paro: g trabaja en la identidad todos los años.</li><li>Es la palanca «buena» — y la más difícil de mover en la realidad; el modelo enseña la aritmética, no si es realista.</li><li>El precio de la vivienda sube con g (E_IPV_G 1,1): el esfuerzo roza la línea roja.</li></ul>
</div>
</div>

---

# Escenario S7 · adverso <span class="sub">tipos +200 pb · petróleo +50 % · prima 150 pb, a la vez</span>

<div class="g2" style="grid-template-columns: 1.05fr 0.95fr">
<div><img class="shot" src="media/scen_S7_top.png"><p class="cap">Inicio con el preset aplicado: los deslizadores movidos en morado, pill «condicional», KPIs con Δ vs base.</p></div>
<div>
<h3>Horizonte 2050 · Δ vs base</h3>
<div class="g3" style="gap:8px"><div class="kpi coral"><div class="num">349,8<small>%PIB</small></div><div class="lbl">Deuda 2050</div><div class="d"><span class="up">+126,0 vs base</span></div></div><div class="kpi coral"><div class="num">−28,8<small>%PIB</small></div><div class="lbl">Saldo 2050</div><div class="d"><span class="up">−13,8</span></div></div><div class="kpi coral"><div class="num">6,5<small>%</small></div><div class="lbl">Bono 10A</div><div class="d"><span class="up">+3,1</span></div></div><div class="kpi coral"><div class="num">11,1<small>%</small></div><div class="lbl">Paro 2050</div><div class="d"><span class="up">+1,0</span></div></div><div class="kpi gold"><div class="num">3,3<small>%</small></div><div class="lbl">IPCA 2030</div><div class="d"><span class="up">+0,3</span></div></div><div class="kpi gold"><div class="num">15,4<small>%</small></div><div class="lbl">Esfuerzo vivienda</div><div class="d"><span class="dn">−24,4</span></div></div></div>
<h3 style="margin-top:8px">Líneas rojas en 2050</h3>
<p style="font-size:0.82em"><span class="st cross">cruzada</span> déficit &gt; 3 · déficit &gt; 11,3 · deuda &gt; 105 · deuda &gt; 120 &nbsp; <span class="st near">cerca</span> <b>bono &gt; 7 %</b> · pobreza infantil</p>
<h3 style="margin-top:8px">Lectura</h3>
<ul style="font-size:0.85em"><li>Los canales se refuerzan: +126 pp no es la suma de S1 (+83) y S2 (−2) más la prima — la interacción se dibuja como barra aparte.</li><li>El bono entra en <b>banda de aviso del 7 %</b>: el punto de no retorno empírico de GRC/PRT/IRL. A partir de ahí el mercado exige más precisamente porque duda.</li><li>Déficit por debajo del suelo de 2009. Es el escenario que mira el 💼 Bonista.</li></ul>
</div>
</div>

---

<!-- _class: dense -->
# Los 8 presets comparados <span class="sub">motor v1.0.0 · horizonte 2050 salvo indicación · Δ vs base entre paréntesis</span>

<table>
<tr><th>Preset</th><th>Palancas</th><th class="n">Deuda 2030</th><th class="n">Deuda 2050</th><th class="n">Saldo 2050</th><th class="n">Paro 2050</th><th class="n">Bono 10A</th><th class="n">Esfuerzo 2050</th><th>Líneas rojas 2050 (además de las 4 de base)</th></tr>
<tr><td><b>S0</b> base</td><td>—</td><td class="n">112,9</td><td class="n"><b>223,8</b></td><td class="n">−15,0</td><td class="n">10,1</td><td class="n">3,4</td><td class="n">39,8</td><td><span class="st near">cerca</span> esfuerzo · pobreza infantil</td></tr>
<tr><td><b>S1</b> tipos</td><td>r 4,80</td><td class="n">118,6</td><td class="n"><b>306,9</b> <span class="up">(+83,1)</span></td><td class="n">−23,3</td><td class="n">10,7</td><td class="n">5,4</td><td class="n">15,5</td><td><span class="st near">cerca</span> pobreza infantil</td></tr>
<tr><td><b>S2</b> petróleo</td><td>pᵐ +50</td><td class="n">106,2</td><td class="n"><b>221,8</b> <span class="dn">(−2,0)</span></td><td class="n">−14,9</td><td class="n">10,5</td><td class="n">3,4</td><td class="n">39,7</td><td><span class="st near">cerca</span> esfuerzo · pobreza infantil · IPCA 2030 3,6</td></tr>
<tr><td><b>S3</b> consolidación</td><td>sp +1,0</td><td class="n">110,1</td><td class="n"><b>210,3</b> <span class="dn">(−13,5)</span></td><td class="n">−13,5</td><td class="n">10,8</td><td class="n">3,4</td><td class="n">44,2</td><td><span class="st cross">cruzada</span> esfuerzo &gt; 40</td></tr>
<tr><td><b>S4</b> productividad</td><td>λ 1,4</td><td class="n">110,3</td><td class="n"><b>206,9</b> <span class="dn">(−16,9)</span></td><td class="n">−14,4</td><td class="n">9,9</td><td class="n">3,4</td><td class="n">40,2</td><td><span class="st cross">cruzada</span> esfuerzo &gt; 40 (40,2)</td></tr>
<tr><td><b>S5</b> desregulación</td><td>z −1 · τ −1,5</td><td class="n">112,9</td><td class="n"><b>223,8</b> (=)</td><td class="n">−15,0</td><td class="n"><b>8,5</b></td><td class="n">3,4</td><td class="n">39,8</td><td><span class="st near">cerca</span> esfuerzo · pobreza infantil</td></tr>
<tr><td><b>S6</b> envejecimiento</td><td>β₆₅ +0,6</td><td class="n">115,9</td><td class="n"><b>282,0</b> <span class="up">(+58,2)</span></td><td class="n">−20,8</td><td class="n">10,1</td><td class="n">3,4</td><td class="n">39,8</td><td><span class="st near">cerca</span> esfuerzo · pobreza infantil</td></tr>
<tr><td><b>S7</b> adverso</td><td>r 4,80 · pᵐ 50 · σ 150</td><td class="n">113,5</td><td class="n"><b>349,8</b> <span class="up">(+126,0)</span></td><td class="n">−28,8</td><td class="n">11,1</td><td class="n">6,5</td><td class="n">15,4</td><td><span class="st cross">cruzada</span> déficit &gt; 11,3 &nbsp; <span class="st near">cerca</span> <b>bono &gt; 7 %</b></td></tr>
</table>

<p class="cap">Las 4 líneas rojas cruzadas en todos los escenarios a 2050: déficit &gt; 3 %, deuda &gt; 105 %, deuda &gt; 120 % — y la ratio sube en todos porque el déficit primario del vintage no se cierra. S5 mueve el paro (−1,6) pero no la deuda: las palancas de oferta desplazan WS/PS sin tocar la identidad en este motor. Ningún escenario baja la ratio: la deuda no se devuelve, se diluye con crecimiento o no se diluye.</p>

---

# Guion de demostración en 5 minutos <span class="sub">un recorrido que enseña el modelo entero</span>

<div class="flow">
<div class="node"><b>0:00 · Inicio en base</b>Señala los 4 KPIs, el abanico y las 3 líneas rojas ya cruzadas hoy. «Nada está proyectado todavía».<span class="k">S0</span></div><div class="arr">→</div>
<div class="node"><b>1:00 · Preset S1</b>Tipos +200 pb. Deuda 2050 salta de 224 a 307. Abre «ver el mecanismo»: la cadena REFI → E_R → Okun.<span class="k">S1</span></div><div class="arr">→</div>
<div class="node"><b>2:00 · Comprador</b>Salta al perfil 🔑: la cuota sube con el bono, el precio cae. La Δ vs base en cada KPI.<span class="k">persona/03</span></div><div class="arr">→</div>
<div class="node"><b>3:00 · Laboratorio</b>Abanico hasta 2070 (anchura, no mediana) y matriz de sensibilidad: r y β₆₅ pesan más que sp.<span class="k">laboratorio</span></div><div class="arr">→</div>
<div class="node"><b>4:00 · Análogos</b>Horizonte 2050 → «Buscar análogo histórico». Tres vecinos, veredicto r − g, 8 diferencias estructurales.<span class="k">analog</span></div><div class="arr">→</div>
<div class="node"><b>4:45 · Límites</b>«Qué no puede decirte»: no es previsión, constantes calibradas, sin banco central endógeno.<span class="k">como-funciona</span></div>
</div>

<div class="g2" style="margin-top:12px">
<div class="card gold"><h2><img class="ico" src="icons/_c/warning_F2B134.svg" width="22" height="22" alt=""> Antes de la defensa</h2><p>La API duerme en Hugging Face sin uso: abre la web 2 minutos antes para despertarla (≈1 min). El motor TypeScript en el navegador cubre Inicio y perfiles aunque la API tarde; el abanico y los análogos necesitan el servidor.</p></div>
<div class="card"><h2><img class="ico" src="icons/_c/check_13A89E.svg" width="22" height="22" alt=""> Frases que anclan</h2><p>«Proyección condicional, no previsión» · «la anchura, no la mediana» · «mientras r &lt; g la deuda se diluye sola» · «las palancas no suman» · «no contradicho, que es menos que validado».</p></div>
</div>

---

# Qué no puede decirte <span class="sub">los límites forman parte del modelo, no de la letra pequeña</span>

<div class="g3">
<div class="card coral"><h2><img class="ico" src="icons/_c/dismiss_F4645A.svg" width="26" height="26" alt=""> No es una previsión</h2><p>Con todas las palancas en su base, lo que ves es la senda central del vintage, no un pronóstico. Deuda 2050 = 223,8 %PIB es aritmética condicional.</p></div>
<div class="card gold"><h2><img class="ico" src="icons/_c/settings_F2B134.svg" width="26" height="26" alt=""> Constantes calibradas, no estimadas</h2><p>Vienen de la literatura y de la calibración v16. La pestaña Evidencia declara cuáles son identificables con los datos congelados y cuáles no.</p></div>
<div class="card navy"><h2><img class="ico" src="icons/_c/bank_0B2545.svg" width="26" height="26" alt=""> Sin política monetaria endógena</h2><p>Mueves el tipo a mano; no hay un banco central que reaccione a la inflación que el propio modelo genera.</p></div>
<div class="card "><h2><img class="ico" src="icons/_c/history_13A89E.svg" width="26" height="26" alt=""> Sin ruptura estructural</h2><p>Coeficientes fijos en todo el horizonte. El modelo no sabe representar una crisis que cambie las reglas del juego — el HMM de Inicio enseña que España las ha cambiado.</p></div>
<div class="card "><h2><img class="ico" src="icons/_c/question_13A89E.svg" width="26" height="26" alt=""> Capacidad discriminante modesta</h2><p>Impago: AUC 0,674. Gemelo empírico: R² fuera de país ≈ 0. Se publican como tales: ordenan, no calibran niveles.</p></div>
<div class="card coral"><h2><img class="ico" src="icons/_c/shield_F4645A.svg" width="26" height="26" alt=""> No es consejo</h2><p>Ni de compra, ni de venta, ni de voto. Pie de página en todas las pestañas: «proyección condicional, no recomendación».</p></div>
</div>

---

<!-- _class: cover -->

<span class="tag">GRACIAS</span>

# España en escenarios

## Una pregunta, una identidad, diez palancas — y el margen de error a la vista

<p style="margin-top:30px"><img class="ico" src="icons/_c/globe_9fd9d3.svg" width="22" height="22" alt=""> <b>danribes.github.io/tfm-data-science</b></p>
<p><img class="ico" src="icons/_c/db_9fd9d3.svg" width="22" height="22" alt=""> <b>danribes-evo-espana-api.hf.space</b> &nbsp;·&nbsp; <img class="ico" src="icons/_c/doc_9fd9d3.svg" width="22" height="22" alt=""> github.com/danribes/tfm-data-science</p>
<p style="font-size:0.8em;margin-top:22px">FastAPI · numpy · pandas · React · Vite · TypeScript · Zustand · Vitest · MSW · pytest · Marp · iconografía Microsoft Fluent UI System Icons</p>
<p style="font-size:0.72em;color:#8aa0b8">Daniel Ribes · Máster en Data Science · vintage 2026-07-31 · motor v1.0.0</p>
