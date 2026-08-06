# V16 Engine Extraction — Source Material for Implementation Plan

Extraction pass over the legacy `v16_perfiles_lab` design artifacts. Every code block below is
copied byte-for-byte from the named source file and line range (extracted programmatically via
Python file reads + exact line-range slicing, never retyped, to guarantee verbatim accuracy).
CSV values are read with Python's `csv` module and reproduced as the literal field strings from
the file (no reformatting, no rounding).

Sources read (local disk only):
- `/home/dan/projects/evo_final_work/legacy/design_data/design/v16_perfiles_lab/_v16_template.html` (1015 lines)
- `/home/dan/projects/evo_final_work/legacy/design_data/design/v16_perfiles_lab/build_v16.py` (99 lines)
- `/home/dan/projects/evo_final_work/legacy/design_data/data/gold/*.csv` (9 gold CSVs)
- `/home/dan/projects/evo_final_work/legacy/design_data/data/kpis_perfiles.json`
- `/home/dan/projects/evo_final_work/legacy/design_data/design/v12_limites_fuentes.md`
- `/home/dan/projects/evo_final_work/legacy/design_data/design/v16_perfiles_lab/v16_perfiles_lab.html` (built output — used only to read the embedded `calib` payload, since
  `build_v16.py`'s bisection solve is not runnable standalone without the full data pipeline)

---

## S1. Engine JS verbatim — scenario engine core

Source: `/home/dan/projects/evo_final_work/legacy/design_data/design/v16_perfiles_lab/_v16_template.html`, lines 239–416 (inside the single `<script>` block that runs 237–1013).
This is the semi-structural model: constants (`V0`, `BASE`, `C`), the lever→GDP-deviation chain,
Okun's law, the Phillips curve, wage-setting, the debt identity, refinancing, and the French
mortgage-payment formula, plus `LEVERS` and `PRESETS`.

```js
const D = /*__DATA__*/null;
const K = D.kpi, SER = D.series, GC = D.central, DEP = D.olddep, CAL = D.calib;

/* ============================================================ formato ==== */
const nf = (v, d) => (v === null || v === undefined || !isFinite(v)) ? "s/d"
  : new Intl.NumberFormat("es-ES", {minimumFractionDigits: d, maximumFractionDigits: d}).format(v).replace("-", "−");
const sg = (v, d) => (v >= 0 ? "+" : "−") + nf(Math.abs(v), d);
const eur = v => new Intl.NumberFormat("es-ES", {maximumFractionDigits: 0}).format(v).replace("-", "−");

/* ============================================================ motor ====== */
const Y0 = 2026, Y1 = 2050, NY = Y1 - Y0 + 1;

// valores del vintage (data/kpis_perfiles.json) — anclan el año 0
const V0 = {
  u:      K.paro_total.valor,          // 10,1 %      2026-06
  pi:     K.hicp_es.valor,             // 3,0 % a/a   2025-12
  g:      K.pib_yoy.valor,             // +2,7 % a/a  2026-Q2
  bono:   K.bono10y_es.valor,          // 3,42 %      2026-06
  precio: K.precio_vivienda_mediano.valor,
  cuota:  K.cuota_hipoteca_mediana.valor,
  salmes: CAL.salario_mes_bruto,       // 24.497/14
  salario:K.salario_medio.valor,
  ipv:    K.vivienda_precio_yoy.valor, // +12,8 % a/a 2026-Q1
  pens:   K.gasto_pensiones_pib.valor,     // 13,23 % PIB 2024
  arop:   K.arop_infantil.valor,       // 28,5 %      2025
  edu:    K.gasto_educacion_pib.valor,     // 4,1 % PIB
  d1:     K.salarios_publicos_pib.valor,
  p2:     K.consumo_intermedio_pib.valor,
  d3:     K.subvenciones_pib.valor,
  p51:    K.inversion_publica_pib.valor,
  gtot:   K.gasto_total_pib.valor,
  temp:   K.temporalidad.valor,
  auton:  K.autoempleo.valor,
  bls:    K.bls_endurecimiento.valor,
  hip:    K.hipotecas_anuales.valor,
  sobre:  K.sobrecarga_vivienda.valor,
  ujuv:   K.paro_juvenil.valor,
  vida:   K.esperanza_vida.valor
};

// posición base de cada palanca = el vintage (o la mediana del central)
const BASE = {r: K.euribor12m.valor, prima: K.spread_es_de.valor, sp: 0, lam: 0.9,
              pm: 0, tau: 0, z: 0, ext: 1.8, dem: 0, idx: 0};

// constantes calibradas — todas declaradas en el rail
const C = {
  MULT: 1.40,   // multiplicador fiscal (CORE Macro U3)
  RHO:  0.62,   // persistencia de la desviación de nivel del PIB
  E_R:  0.45,   // pp de PIB por pp de tipo (canal inversión/consumo, U3+U6)
  E_EXT:0.25,   // peso de la demanda externa (U7)
  E_PM: 0.012,  // pp de PIB por 1 % de shock de importaciones
  OKUN: 0.48,   // Okun: pp de paro por pp de PIB (ya estimado en E4)
  KAPPA:0.22,   // pendiente de Phillips (U2/U4)
  GAMMA:0.045,  // pass-through de p^m a IPCA (identificación 2021-23)
  THETA:0.55,   // inercia de expectativas
  PHI:  0.30,   // curva WS: salario nominal por pp de holgura
  A_Z:  1.10, A_TAU: 0.30, A_LAM: 0.45,   // desplazadores de u* (WS–PS)
  REFI: 0.14,   // fracción de deuda que se refinancia cada año
  TERM: 0.17,   // prima de plazo 10a sobre Euríbor (3,42 − 2,80 − 0,45)
  DIFF: CAL.diferencial_hipotecario,      // diferencial hipotecario implícito
  IPV_LR: 3.0, IPV_REV: 0.60,             // reversión del IPV a su media larga
  E_IPV_R: 2.6, E_IPV_G: 1.1,
  RJUV: 2.317   // ratio paro juvenil / total, estable en la serie 5a
};

const french = (p, tipo, n) => { const i = tipo / 1200; return p * i / (1 - Math.pow(1 + i, -n)); };

function run(L) {
  const R = {};
  ["lvl","u","pi","g","gnom","wnom","wreal","wrealIdx","b","ief","int","pb","saldo",
   "ipv","precio","cuota","salmes","salario","esf","pens","dep","arop","edu","d1",
   "nomreal","p2","d3","p51","gtot","bls","temp","ujuv","auton","hip","sobre",
   "bono","spread","r","deficitAbs","vida"].forEach(k => R[k] = []);

  const bono  = L.r + C.TERM + L.prima / 100;
  const shock = -(L.sp - BASE.sp) - C.E_R * (L.r - BASE.r)
                + C.E_EXT * (L.ext - BASE.ext) - C.E_PM * (L.pm - BASE.pm);
  const uStarDev = C.A_Z * L.z + C.A_TAU * L.tau - C.A_LAM * (L.lam - BASE.lam);

  let lvl = 0, piDev = 0, di = 0, b = GC["2025"].deuda,
      salIdx = 1, wrIdx = 1, pensFac = 1, nomIdx = 1, precio = V0.precio;

  for (let k = 0; k < NY; k++) {
    const y = Y0 + k, gc = GC[String(y)], prev = lvl;

    lvl = C.RHO * lvl + (1 - C.RHO) * C.MULT * shock;      // desviación de nivel del PIB (%)
    const gapU = C.OKUN * lvl;                              // holgura: u por debajo de u*
    const u  = V0.u + uStarDev - gapU;
    piDev = C.THETA * piDev + C.KAPPA * gapU + C.GAMMA * (L.pm - BASE.pm) * Math.pow(0.45, k);
    const pi = V0.pi + piDev;
    const g  = V0.g + (lvl - prev) + (L.lam - BASE.lam);

    // --- deuda: identidad b_t = b_{t-1}(1+i)/(1+g) − pb, anclada al escenario central
    const gnom = gc.g_nominal + (g - V0.g) + piDev;
    di = di + C.REFI * ((bono - V0.bono) - di);
    const ief = gc.r_efectivo + di;
    const pb  = gc.pb + L.sp - gc.presion_demog * L.dem;
    const bprev = b;
    b = bprev * (1 + ief / 100) / (1 + gnom / 100) - pb;
    const intr = bprev * ief / 100;
    const saldo = pb - intr;

    // --- salarios (WS): nominal = π + λ + φ·holgura ; real = λ + φ·holgura
    const wnom = pi + L.lam + C.PHI * gapU;
    const wreal = wnom - pi;
    if (k > 0) { salIdx *= (1 + wnom / 100); wrIdx *= (1 + wreal / 100); }

    // --- vivienda
    const ipv = C.IPV_LR + (V0.ipv - C.IPV_LR) * Math.pow(C.IPV_REV, k)
                - C.E_IPV_R * (L.r - BASE.r) + C.E_IPV_G * (g - V0.g);
    if (k > 0) precio *= (1 + ipv / 100);
    const cuota = french(precio * 0.8, L.r + C.DIFF, 300);
    const salmes = V0.salmes * salIdx;
    const esf = cuota / salmes * 100;

    // --- pensiones: identidad mecánica pensión×nº / PIB
    if (k > 0) pensFac *= (1 + (pi + L.idx) / 100) / (1 + gnom / 100);
    if (k > 0) nomIdx *= (1 + L.idx / 100);
    // β₆₅ amplifica la deriva demográfica proyectada; en 2026 el índice vale 1 por construcción
    const depIdx = 1 + (DEP[String(y)] / DEP[String(Y0)] - 1) * (1 + L.dem);
    const dep = DEP[String(Y0)] * depIdx;
    const pens = V0.pens * depIdx * pensFac;

    R.lvl.push(lvl); R.u.push(u); R.pi.push(pi); R.g.push(g); R.gnom.push(gnom);
    R.wnom.push(wnom); R.wreal.push(wreal); R.wrealIdx.push(wrIdx * 100);
    R.b.push(b); R.ief.push(ief); R.int.push(intr); R.pb.push(pb); R.saldo.push(saldo);
    R.deficitAbs.push(Math.abs(Math.min(0, saldo)));
    R.ipv.push(ipv); R.precio.push(precio); R.cuota.push(cuota);
    R.salmes.push(salmes); R.salario.push(V0.salario * salIdx); R.esf.push(esf);
    R.pens.push(pens); R.dep.push(dep);
    R.nomreal.push(nomIdx * 100);
    R.arop.push(V0.arop + 0.55 * (u - V0.u) + 0.90 * L.sp);
    R.edu.push(V0.edu - 0.090 * L.sp);
    R.d1.push(V0.d1 - 0.240 * L.sp);
    R.p2.push(V0.p2 - 0.125 * L.sp);
    R.d3.push(V0.d3 - 0.031 * L.sp);
    R.p51.push(V0.p51 - 0.145 * L.sp);
    R.gtot.push(V0.gtot - 1.0 * L.sp);
    R.bls.push(V0.bls + 12 * (L.r - BASE.r) + 2.5 * (u - V0.u));
    R.temp.push(V0.temp + 0.25 * (u - V0.u) - 1.5 * L.z);
    R.ujuv.push(C.RJUV * u);
    R.auton.push(V0.auton + 0.12 * (u - V0.u) - 0.40 * (g - V0.g));
    R.hip.push(Math.max(0, V0.hip * (1 - 1.6 * (esf / (V0.cuota / V0.salmes * 100) - 1))));
    R.sobre.push(V0.sobre + 0.18 * (esf - V0.cuota / V0.salmes * 100));
    R.bono.push(bono); R.spread.push(L.prima); R.r.push(L.r); R.vida.push(V0.vida);
  }
  return R;
}

/* ============================================================ palancas === */
const LEVERS = [
  {id:"r",    sym:"r",   nm:"Tipo de interés · Euríbor 12m", u:"%",       min:0,   max:6,   st:0.05, d:2, src:"ecb_euribor12m.csv · 2026-06"},
  {id:"prima",sym:"σ",   nm:"Prima de riesgo · spread ES–DE", u:"pb",     min:0,   max:400, st:5,    d:0, src:"ecb_bono10y_{es,de}.csv · 2026-06"},
  {id:"sp",   sym:"sp",  nm:"Saldo primario · Δ vs central",  u:"pp PIB", min:-4,  max:4,   st:0.1,  d:1, src:"gold_escenarios_deuda.csv (central)"},
  {id:"lam",  sym:"λ",   nm:"Productividad",                  u:"%/año",  min:-0.5,max:2.5, st:0.1,  d:1, src:"PWT + INE · desplaza la PS"},
  {id:"pm",   sym:"pᵐ",  nm:"Precio importaciones/energía",   u:"% a/a",  min:-50, max:100, st:5,    d:0, src:"WEO commodity prices"},
  {id:"tau",  sym:"τ",   nm:"Presión fiscal · cuña laboral",  u:"pp",     min:-5,  max:5,   st:0.25, d:2, src:"Eurostat GFS · desplaza la WS"},
  {id:"z",    sym:"z",   nm:"Instituciones laborales",        u:"índice", min:-2,  max:2,   st:0.1,  d:1, src:"OECD/Eurostat · desplaza la WS"},
  {id:"ext",  sym:"Y*",  nm:"Demanda externa",                u:"% a/a",  min:-4,  max:6,   st:0.1,  d:1, src:"WEO · canal exterior (U7)"},
  {id:"dem",  sym:"β₆₅", nm:"Presión demográfica",            u:"×",      min:-1,  max:1,   st:0.05, d:2, src:"gold_projections.csv · variante"},
  {id:"idx",  sym:"ι",   nm:"Indexación pensiones/nóminas",   u:"IPC+pp", min:-1.5,max:1,   st:0.1,  d:1, src:"regla de revalorización · palanca"}
];

const PRESETS = [
  {id:"S0", nm:"S0 base",            set:{}},
  {id:"S1", nm:"S1 tipos +200 pb",   set:{r: BASE.r + 2}},
  {id:"S2", nm:"S2 petróleo +50 %",  set:{pm: 50}},
  {id:"S3", nm:"S3 consolidación",   set:{sp: 1.0}},
  {id:"S4", nm:"S4 productividad",   set:{lam: 1.4}},
  {id:"S5", nm:"S5 desregulación lab.", set:{z: -1.0, tau: -1.5}},
  {id:"S6", nm:"S6 envejecimiento",  set:{dem: 0.6}},
  {id:"S7", nm:"S7 adverso",         set:{r: BASE.r + 2, pm: 50, prima: 150}}
];

let L = Object.assign({}, BASE);
let HZ = 2026, CUR = 0;
const kOf = y => Math.max(0, Math.min(NY - 1, y - Y0));
const dirty = () => LEVERS.some(v => Math.abs(L[v.id] - BASE[v.id]) > 1e-9);
```

### S1b. Chart & series helper functions (verbatim)

Source: `/home/dan/projects/evo_final_work/legacy/design_data/design/v16_perfiles_lab/_v16_template.html`, lines 419–473. Not part of the numeric engine itself, but every persona
panel's rendering depends on these — included for completeness (`chart()` draws the SVG lines/
bands/thresholds; `sPts`/`sVals`/`sLabs` read the historical `SER` series).

```js
function chart(el, spec) {
  const W = 660, H = spec.h || 420, ml = 56, mr = 12, mt = 12, mb = 20;
  const xs = spec.x, n = xs.length;
  let lo = spec.lo, hi = spec.hi;
  if (lo === undefined) {
    const all = spec.lines.flatMap(l => l.v).concat(spec.band ? spec.band.lo.concat(spec.band.hi) : []).filter(isFinite);
    lo = Math.min.apply(null, all); hi = Math.max.apply(null, all);
    const pad = (hi - lo) * 0.16 || 1; lo -= pad; hi += pad;
  }
  const X = i => ml + (W - ml - mr) * (n === 1 ? 0 : i / (n - 1));
  const Y = v => mt + (H - mt - mb) * (1 - (v - lo) / (hi - lo || 1));
  const path = v => v.map((q, i) => (i ? "L" : "M") + X(i).toFixed(1) + " " + Y(q).toFixed(1)).join(" ");
  let s = '<svg class="chart" viewBox="0 0 ' + W + ' ' + H + '" role="img">';
  const ticks = 4;
  for (let t = 0; t <= ticks; t++) {
    const v = lo + (hi - lo) * t / ticks, y = Y(v);
    s += '<line x1="' + ml + '" y1="' + y.toFixed(1) + '" x2="' + (W - mr) + '" y2="' + y.toFixed(1) +
         '" stroke="var(--grid)" stroke-width="1"/>' +
         '<text x="' + (ml - 4) + '" y="' + (y + 3).toFixed(1) + '" text-anchor="end">' +
         nf(v, spec.dec !== undefined ? spec.dec : (hi - lo > 40 ? 0 : 1)) +
         (t === ticks && spec.u ? " " + spec.u : "") + '</text>';
  }
  if (spec.red !== undefined && spec.red >= lo && spec.red <= hi) {
    s += '<line x1="' + ml + '" y1="' + Y(spec.red).toFixed(1) + '" x2="' + (W - mr) + '" y2="' + Y(spec.red).toFixed(1) +
         '" stroke="var(--div-neg)" stroke-width="1" stroke-dasharray="4 3"/>';
  }
  if (spec.band) {
    const up = spec.band.hi.map((q, i) => (i ? "L" : "M") + X(i).toFixed(1) + " " + Y(q).toFixed(1)).join(" ");
    const dn = spec.band.lo.map((q, i) => "L" + X(i).toFixed(1) + " " + Y(q).toFixed(1)).reverse().join(" ");
    s += '<path d="' + up + " " + dn + ' Z" fill="var(--band-out)" opacity=".75"/>';
  }
  spec.lines.forEach(l => {
    s += '<path d="' + path(l.v) + '" fill="none" stroke="' + (l.c || "var(--s1)") + '" stroke-width="' +
         (l.w || 2) + '"' + (l.dash ? ' stroke-dasharray="5 4"' : "") + ' stroke-linejoin="round"/>';
    if (l.dot !== false) {
      const i = l.v.length - 1;
      s += '<circle cx="' + X(i).toFixed(1) + '" cy="' + Y(l.v[i]).toFixed(1) + '" r="3.2" fill="' + (l.c || "var(--s1)") + '"/>';
    }
  });
  (spec.ann || []).forEach(a => {
    s += '<text x="' + X(a.i).toFixed(1) + '" y="' + (Y(a.v) + (a.dy || -8)).toFixed(1) +
         '" class="lbl" text-anchor="' + (a.anch || "middle") + '">' + a.t + '</text>';
  });
  const lab = [0, Math.floor((n - 1) / 2), n - 1];
  lab.forEach((i, j) => {
    s += '<text x="' + X(i).toFixed(1) + '" y="' + (H - 6) + '" text-anchor="' +
         (j === 0 ? "start" : j === 2 ? "end" : "middle") + '">' + xs[i] + '</text>';
  });
  s += "</svg>";
  el.innerHTML = s;
}

const sPts = key => SER[key].puntos;
const sVals = key => sPts(key).map(p => p[1]);
const sLabs = key => sPts(key).map(p => String(p[0]).replace(/\.0$/, ""));
```

### S1c. DOM wiring / render loop (verbatim)

Source: `/home/dan/projects/evo_final_work/legacy/design_data/design/v16_perfiles_lab/_v16_template.html`, lines 808–1012 (end of the `<script>` block, `</script>` is line 1013).
`buildRail()`, `railState()`, `statusOf()` (semáforo status logic), `render()` (the main render
function — calls `run(L)` and `run(BASE)` and drives every panel), `readURL()`/`writeURL()`
(shareable-state query-string encoding), and `fit()` (viewport scaling), plus the bootstrap calls
at the very end of the script.

```js
const $ = id => document.getElementById(id);

function buildRail() {
  $("presets").innerHTML = PRESETS.map(p => '<span class="ps" data-p="' + p.id + '">' + p.nm + '</span>').join("");
  $("levers").innerHTML = LEVERS.map(v =>
    '<div class="lev" id="lev-' + v.id + '">' +
      '<div class="l1"><span class="sym">' + v.sym + '</span><span class="nm">' + v.nm + '</span>' +
      '<span class="vv" id="vv-' + v.id + '"></span></div>' +
      '<input type="range" id="in-' + v.id + '" min="' + v.min + '" max="' + v.max + '" step="' + v.st + '" value="' + BASE[v.id] + '">' +
      '<div class="src">' + v.src + '</div></div>').join("");
  LEVERS.forEach(v => $("in-" + v.id).addEventListener("input", e => {
    L[v.id] = parseFloat(e.target.value); render();
  }));
  $("presets").addEventListener("click", e => {
    const id = e.target.getAttribute("data-p"); if (!id) return;
    const p = PRESETS.find(q => q.id === id);
    L = Object.assign({}, BASE, p.set);
    LEVERS.forEach(v => $("in-" + v.id).value = L[v.id]);
    render();
  });
  document.querySelectorAll(".hb").forEach(b => b.addEventListener("click", () => {
    HZ = +b.getAttribute("data-y");
    document.querySelectorAll(".hb").forEach(x => x.classList.toggle("on", x === b));
    render();
  }));
  $("motor").innerHTML =
    "<b>Motor declarado</b> · multiplicador 1,40 · persistencia 0,62 · elasticidad al tipo 0,45 · Okun 0,48 · " +
    "Phillips κ 0,22 · pass-through pᵐ 0,045 · inercia θ 0,55 · WS φ 0,30 · refi 14 %/año · " +
    "prima de plazo 0,17 pp · diferencial hipotecario " + nf(C.DIFF, 2) + " pp. " +
    "Deuda: bₜ = bₜ₋₁(1+i)/(1+g) − sp, anclada al escenario central de gold_escenarios_deuda.csv " +
    "(nominal 3,3 %, más exigente que el 5,7 % del vintage: discrepancia declarada). " +
    "La base NO es una predicción — congela el vintage " + D.vintage + "; el motor calcula desviaciones.";
  $("chipVintage").textContent = "vintage " + D.vintage;
  $("tabs").innerHTML = P.map((p, i) => '<span class="tab" data-i="' + i + '">' + p.pill + '</span>').join("");
  $("tabs").addEventListener("click", e => {
    const i = e.target.getAttribute("data-i"); if (i === null) return;
    CUR = +i; render();
  });
}

function railState() {
  LEVERS.forEach(v => {
    const moved = Math.abs(L[v.id] - BASE[v.id]) > 1e-9;
    const el = $("vv-" + v.id);
    el.textContent = nf(L[v.id], v.d) + " " + v.u;
    el.classList.toggle("moved", moved);
    $("lev-" + v.id).classList.toggle("hot", P[CUR].hot.indexOf(v.id) >= 0);
  });
  const hit = PRESETS.find(p => {
    const t = Object.assign({}, BASE, p.set);
    return LEVERS.every(v => Math.abs(t[v.id] - L[v.id]) < 1e-9);
  });
  document.querySelectorAll(".ps").forEach(b => b.classList.toggle("on", hit && b.getAttribute("data-p") === hit.id));
  $("chipMode").textContent = hit ? hit.nm : "escenario a medida";
}

function statusOf(val, thr, cmp) {
  if (thr === null || val === null) return ["s/d", ""];
  const cross = cmp === "lt" ? val < thr : val > thr;
  if (cross) return ["cruzada", "cross"];
  const near = Math.abs(val - thr) <= Math.abs(thr || 1) * 0.12;
  return near ? ["cerca", "near"] : ["segura", "safe"];
}

function render() {
  const R = run(L), B = run(BASE), k = kOf(HZ), p = P[CUR], y = Y0 + k;
  const fresh = !dirty() && HZ === Y0;
  railState();

  document.querySelectorAll(".tab").forEach((t, i) => t.classList.toggle("on", i === CUR));
  $("h1").textContent = p.h1;
  $("meta").textContent = p.meta;
  $("seal").textContent = fresh ? "📅 dato observado · vintage" : "🔮 condicional · " + y;
  $("seal").className = "badge-fwd" + (fresh ? "" : " lab");
  $("footProfile").textContent = "v16 · perfil " + p.id + " — " + p.foot;
  $("footL").textContent = "⚠ base = vintage " + D.vintage + " congelado · el motor calcula desviaciones con elasticidades declaradas";
  $("footR").textContent = "horizonte " + y + " · desviación de nivel del PIB " + sg(R.lvl[k], 2) + " %";

  // --- tarjetas
  $("outs").innerHTML = p.outs.map(o => {
    const v = R[o.k][k], bv = B[o.k][k], dv = v - bv;
    const big0 = o.u === "€" || o.u === "€/año" || o.u === "€/mes" || o.u === "fincas";
    const eps = 0.5 * Math.pow(10, -(big0 ? 0 : o.d));
    const lo = o.dial[0], hi = o.dial[1];
    const pct = Math.max(0, Math.min(100, (v - lo) / (hi - lo) * 100));
    const bpct = Math.max(0, Math.min(100, (bv - lo) / (hi - lo) * 100));
    let cls = "";
    if (o.red !== undefined) {
      const bad = o.red < 0 ? v < o.red : (o.k === "edu" || o.k === "nomreal" || o.k === "wrealIdx" || o.k === "p51") ? v < o.red : v > o.red;
      cls = bad ? " bad" : Math.abs(v - o.red) <= Math.abs(o.red || 1) * 0.12 ? " warn2" : " ok";
    }
    const rpct = o.red === undefined ? null : Math.max(0, Math.min(100, (o.red - lo) / (hi - lo) * 100));
    const big = o.u === "€" || o.u === "€/año" || o.u === "€/mes" || o.u === "fincas";
    return '<div class="out"><span class="o-seal">' + (fresh ? "📅" : "🔮") + '</span>' +
      '<div class="o-label">' + o.lab + '</div>' +
      '<div class="o-val">' + (big ? eur(v) : nf(v, o.d)) + ' <small>' + o.u + '</small></div>' +
      '<div class="o-delta' + (Math.abs(dv) < eps ? "" : (dv > 0 ? " bad" : " good")) + '">' +
        (Math.abs(dv) < eps ? "= base" : (big ? sg(dv, 0) : sg(dv, o.d)) + " vs base") + '</div>' +
      '<div class="gaugebar"><span class="f' + cls + '" style="width:' + pct.toFixed(1) + '%"></span>' +
        '<span class="bm" style="left:' + bpct.toFixed(1) + '%"></span>' +
        (rpct === null ? "" : '<span class="rl" style="left:' + rpct.toFixed(1) + '%"></span>') + '</div>' +
      '<div class="o-note">' + o.note + '</div></div>';
  }).join("");

  // --- gráfico histórico (📅 dato observado, no depende de las palancas)
  $("hAt").innerHTML = p.hA.t + " <small>" + p.hA.s + "</small>";
  $("lgA").innerHTML = '<span><i style="background:var(--retro)"></i>' + p.hA.lg + "</span>" +
    (p.hA.red !== undefined ? '<span><s style="border-color:var(--div-neg)"></s>línea roja ' + nf(p.hA.red, 1) + "</span>" : "");
  const lines = [{v: sVals(p.hA.key), c: "var(--retro)"}];
  if (p.hA.key2) lines.push({v: sVals(p.hA.key2), c: "var(--baseline)", w: 1.5});
  chart($("chA"), {x: sLabs(p.hA.key), lines: lines, u: p.hA.u, red: p.hA.red});

  // --- gráfico de proyección (🔮 responde a las palancas)
  $("hBt").innerHTML = p.hB.t + " <small>" + p.hB.s + "</small>";
  $("lgB").innerHTML = '<span><i style="background:var(--lab)"></i>escenario actual</span>' +
    '<span><s></s>base congelada (vintage)</span>' +
    (p.hB.band ? '<span><i style="background:var(--band-out);height:8px"></i>banda p5–p95 heredada (MC)</span>' : "") +
    (p.hB.red !== undefined ? '<span><s style="border-color:var(--div-neg)"></s>línea roja</span>' : "");
  chart($("chB"), {
    x: YRS, u: p.hB.u, red: p.hB.red,
    band: p.hB.band ? {lo: fanLo, hi: fanHi} : null,
    lines: [{v: B[p.hB.k], c: "var(--baseline)", w: 1.6, dash: true, dot: false},
            {v: R[p.hB.k], c: "var(--lab)", w: 2.4}]
  });

  // --- semáforo
  $("hReds").innerHTML = 'Semáforo <small>umbral vs valor en ' + y + '</small>';
  $("reds").innerHTML = p.reds.map(rr => {
    let val = null;
    if (rr.k === "ipvreal") val = R.ipv[k] - R.pi[k]; else if (rr.k) val = R[rr.k][k];
    const st = statusOf(val, rr.thr, rr.cmp);
    return '<div class="rl-item"><span class="ic">' + rr.ic + '</span>' +
      '<span class="t">' + rr.t + '</span>' +
      '<span class="st ' + st[1] + '">' + (val === null ? "s/d" : nf(val, rr.d === undefined ? 1 : rr.d)) + '</span>' +
      '<span class="x">' + st[0] + " · " + rr.x + '</span></div>';
  }).join("");

  // --- transmisión con delta vivo
  $("chains").innerHTML = p.chains.map(c => {
    const v = R[c.k][k], dv = v - B[c.k][k], ce = 0.5 * Math.pow(10, -c.d);
    const cl = Math.abs(dv) < ce ? "flat" : dv > 0 ? "up" : "dn";
    return '<div class="ch"><span class="a">' + c.a + '</span><span class="arr">→</span>' +
      '<span class="u">' + c.u + '</span><span class="arr">→</span>' + c.t +
      '<span class="d ' + cl + '">' + nf(v, c.d) + " " + c.un +
      (Math.abs(dv) < ce ? "" : " (" + sg(dv, c.d) + ")") + '</span></div>';
  }).join("");

  // --- atribución: cuánto de la desviación aporta cada palanca por separado
  const key = p.hB.k, tot = R[key][k] - B[key][k];
  const dd = (p.outs.find(o => o.k === key) || {d: 1}).d;
  const unit = p.hB.u || "";
  $("hAttr").innerHTML = 'Atribución <small>' + p.hB.t.toLowerCase() + " en " + y + '</small>';
  const parts = LEVERS.filter(v => Math.abs(L[v.id] - BASE[v.id]) > 1e-9).map(v => {
    const one = {}; one[v.id] = L[v.id];
    return {nm: v.sym + " · " + v.nm.split(" · ")[0], c: run(Object.assign({}, BASE, one))[key][k] - B[key][k]};
  });
  if (!parts.length) {
    $("attr").innerHTML = '<div class="at-none">Todas las palancas en su base: el escenario coincide con el vintage ' +
      D.vintage + ' congelado. Mueve una palanca del rail para ver cuánto aporta cada una por separado ' +
      'y qué queda como interacción entre ellas.</div>';
  } else {
    const inter = tot - parts.reduce((a, q) => a + q.c, 0);
    parts.push({nm: "interacción entre palancas", c: inter, soft: true});
    const mx = Math.max.apply(null, parts.map(q => Math.abs(q.c))) || 1;
    $("attr").innerHTML =
      '<div class="at" style="border-bottom:1px solid var(--grid);padding-bottom:4px">' +
        '<span class="an" style="color:var(--ink)">total vs base</span>' +
        '<span class="av ' + (tot > 0 ? "up" : "dn") + '">' + sg(tot, dd) + " " + unit + '</span></div>' +
      parts.map(q => '<div class="at"><span class="an"' + (q.soft ? ' style="font-weight:600"' : "") + '>' + q.nm + '</span>' +
        '<span class="av ' + (Math.abs(q.c) < 1e-9 ? "" : q.c > 0 ? "up" : "dn") + '">' + sg(q.c, dd) + '</span>' +
        '<span class="ab"><i style="width:' + (Math.abs(q.c) / mx * 50).toFixed(1) + '%;left:50%;' +
        (q.c < 0 ? "transform:translateX(-100%);" : "") + (q.soft ? "opacity:.45;" : "") + '"></i></span></div>').join("");
  }

  $("narr").textContent = p.narr(R, k, y);
  $("cite").innerHTML = p.cite;
  writeURL();
}

function readURL() {
  const q = new URLSearchParams(location.search);
  if (q.has("p")) CUR = Math.max(0, Math.min(P.length - 1, +q.get("p")));
  if (q.has("h")) HZ = Math.max(Y0, Math.min(Y1, +q.get("h")));
  LEVERS.forEach(v => { if (q.has(v.id)) L[v.id] = parseFloat(q.get(v.id)); });
  document.querySelectorAll(".hb").forEach(x => x.classList.toggle("on", +x.getAttribute("data-y") === HZ));
  LEVERS.forEach(v => $("in-" + v.id).value = L[v.id]);
}
function writeURL() {
  const q = new URLSearchParams();
  q.set("p", CUR); q.set("h", HZ);
  LEVERS.forEach(v => { if (Math.abs(L[v.id] - BASE[v.id]) > 1e-9) q.set(v.id, L[v.id]); });
  history.replaceState(null, "", "?" + q.toString());
}

function fit() {
  const s = Math.min(1, (window.innerWidth - 24) / 1680);
  $("app").style.transform = "scale(" + s + ")";
  $("app").style.marginBottom = (24 - 1080 * (1 - s)) + "px";
}

buildRail();
readURL();
render();
fit();
window.addEventListener("resize", fit);
```

---

## S2. Persona dependents JS verbatim — the `P` array (12 personas)

Source: `/home/dan/projects/evo_final_work/legacy/design_data/design/v16_perfiles_lab/_v16_template.html`, lines 480–805 (`const P = [ ... ];`). This is the complete per-persona
specification: which `R.*` / `run()` output keys each persona's dials (`outs`), headline charts
(`hA`, `hB`), semáforo thresholds (`reds`), causal chain callouts (`chains`), and the narrative
string function (`narr`) read from the shared macro path computed by `run(L)`/`run(BASE)`. No
persona has its own separate math — all 12 read from the one `R` object `run()` returns.

Persona blocks start at these lines (1-indexed, `id` field line):

- line 482: id `"01"` — `💼 Bonista` (`💼 bonista`)
- line 509: id `"02"` — `🏦 Banca` (`🏦 banca hipotecaria`)
- line 536: id `"03"` — `🔑 Comprador` (`🔑 comprador de vivienda`)
- line 563: id `"04"` — `🚀 Emprendedor` (`🚀 emprendedor`)
- line 590: id `"05"` — `🏛️ Funcionario` (`🏛️ funcionario`)
- line 617: id `"06"` — `🗳️ Político` (`🗳️ político (decisor honesto)`)
- line 644: id `"07"` — `🕳️ Corrupto` (`🕳️ político corrupto · sátira de transparencia`)
- line 671: id `"08"` — `🧒 Infancia` (`🧒 infancia`)
- line 698: id `"09"` — `🌅 Jubilado` (`🌅 jubilado`)
- line 725: id `"10"` — `🎓 Joven` (`🎓 joven que entra al mercado laboral`)
- line 752: id `"11"` — `📋 Indefinido` (`📋 trabajador indefinido`)
- line 779: id `"12"` — `🧾 Autónomo` (`🧾 autónomo`)

Full verbatim array:

```js
const P = [
{
  id:"01", pill:"💼 Bonista", foot:"💼 bonista",
  h1:"💼 Inversor en bonos: ¿me pagarán los 10 años?",
  meta:"ecb_bono10y_es.csv · ecb_bono10y_de.csv · eurostat_gov_debt_es.csv · eurostat_gov_deficit_es.csv · interest_paid.csv · gold_escenarios_deuda.csv",
  hot:["r","prima","sp","dem"],
  outs:[
    {lab:"Bono 10A España", k:"bono", d:2, u:"%", dial:[0,7], red:7, note:"r + prima de plazo 0,17 + spread/100"},
    {lab:"Spread ES–DE", k:"spread", d:0, u:"pb", dial:[0,400], note:"palanca directa · mín. 5a hoy · máx 123 pb (2022-07)"},
    {lab:"Deuda pública", k:"b", d:1, u:"%PIB", dial:[0,180], red:105, note:"bₜ = bₜ₋₁(1+i)/(1+g) − sp · anclada al central"},
    {lab:"Saldo público", k:"saldo", d:1, u:"%PIB", dial:[-8,2], red:-3, note:"saldo primario − intereses"},
    {lab:"Intereses / PIB", k:"int", d:1, u:"%PIB", dial:[0,8], red:5.0, note:"bₜ₋₁ · tipo efectivo · 2,4 %PIB observado 2025 → 2,83 en 2026 (central)"}
  ],
  hA:{t:"El precio de prestar a España", s:"bono 10A mensual · 2021-07 → 2026-06 · ecb_bono10y_es.csv", key:"bono10y_es_5a", u:"%", lg:"bono 10A observado (📅 dato)"},
  hB:{t:"La deuda que el acreedor compra", s:"identidad de deuda 2026–2050 · banda p5–p95 del Monte Carlo heredado", k:"b", u:"%PIB", band:true, red:105},
  reds:[
    {ic:"🏛️", t:"Deuda > 105 %PIB", thr:105, k:"b", cmp:"gt", d:1, x:"narrativa crack23 [comentario]"},
    {ic:"🏛️", t:"Deuda > 120 %PIB", thr:120, k:"b", cmp:"gt", d:1, x:"techo COVID 2020: 119,3 [hist]"},
    {ic:"💶", t:"Bono 10A > 7 %", thr:7, k:"bono", cmp:"gt", d:2, x:"zona rescate: crisis 2012 [hist]"}
  ],
  chains:[
    {a:"tipo BCE", u:"Euríbor", t:"coste de refinanciación", k:"int", d:1, un:"%PIB"},
    {a:"saldo primario", u:"emisión neta", t:"senda de deuda", k:"b", d:1, un:"%PIB"},
    {a:"prima de riesgo", u:"spread", t:"cupón exigido", k:"bono", d:2, un:"%"}
  ],
  narr:(R,k,y)=>`Con las palancas de hoy el cupón a 10 años sale a ${nf(R.bono[k],2)} % y el spread a ${nf(R.spread[k],0)} pb. En ${y} la identidad de deuda deja el saldo en ${nf(R.b[k],1)} %PIB con ${nf(R.int[k],1)} puntos de PIB en intereses — gasto que nadie elige. La banda p5–p95 del Monte Carlo heredado sigue debajo: lo que un acreedor mira no es la mediana, es la anchura.`,
  cite:"identidad anclada a <code>gold_escenarios_deuda.csv</code> (escenario central)"
},
{
  id:"02", pill:"🏦 Banca", foot:"🏦 banca hipotecaria",
  h1:"🏦 Banco hipotecario: ¿a quién presto, a qué tipo y con qué mora esperada?",
  meta:"ecb_euribor12m.csv · bls_criterios_vivienda.csv · ine_hipotecas_ccaa.csv · eurostat_hpi_q_es.csv · gold_cuota_teorica.csv",
  hot:["r","z","tau","ext"],
  outs:[
    {lab:"Euríbor 12m", k:"r", d:2, u:"%", dial:[0,6], red:4.16, note:"palanca directa · pico del ciclo 4,16"},
    {lab:"BLS endurecimiento", k:"bls", d:0, u:"% neto", dial:[-20,60], red:20, note:"10 + 12·Δr + 2,5·Δu"},
    {lab:"Nueva producción", k:"hip", d:0, u:"fincas", dial:[0,700000], note:"500.906 · (1 − 1,6·Δesfuerzo relativo)"},
    {lab:"Precio vivienda a/a", k:"ipv", d:1, u:"%", dial:[-10,16], red:10, note:"reversión a 3 % − 2,6·Δr + 1,1·Δg"},
    {lab:"Cuota mediana", k:"cuota", d:0, u:"€/mes", dial:[0,2000], note:"francesa · 80 % LTV · 25a · dif. " + nf(C.DIFF,2) + " pp"}
  ],
  hA:{t:"El precio del dinero hipotecario", s:"Euríbor 12m mensual · 2021-07 → 2026-06 · ecb_euribor12m.csv", key:"euribor12m_5a", u:"%", lg:"Euríbor 12m observado (📅 dato)"},
  hB:{t:"La cuota de la nueva producción", s:"cuota teórica mediana 2026–2050 · 80 % LTV, 25 años", k:"cuota", u:"€"},
  reds:[
    {ic:"🏠", t:"IPV real a/a > 10 %", thr:10, k:"ipvreal", cmp:"gt", d:1, x:"burbuja 2004-07 [hist] · IPV nominal − IPCA"},
    {ic:"🏦", t:"BLS endurecimiento > 20 %", thr:20, k:"bls", cmp:"gt", d:0, x:"nivel de contracción de crédito [hist]"},
    {ic:"📉", t:"Paro > 15 % (motor de mora)", thr:15, k:"u", cmp:"gt", d:1, x:"último nivel visto en 2021-07 (15,2) [hist]"}
  ],
  chains:[
    {a:"Euríbor", u:"cuota nueva", t:"esfuerzo del hogar", k:"esf", d:1, un:"%"},
    {a:"IPV", u:"LTV efectivo", t:"severidad si impago", k:"ipv", d:1, un:"% a/a"},
    {a:"paro", u:"mora", t:"pérdida esperada", k:"u", d:1, un:"%"}
  ],
  narr:(R,k,y)=>`El margen lo marca un Euríbor al ${nf(R.r[k],2)} % y el riesgo lo marcan el empleo (paro ${nf(R.u[k],1)} %) y un colateral que se mueve al ${sg(R.ipv[k],1)} % anual. En ${y} la cuota mediana teórica sale a ${eur(R.cuota[k])} €/mes y el esfuerzo sobre la nómina media a ${nf(R.esf[k],1)} %. Hueco declarado: la serie de mora bancaria (NPL, Banco de España) sigue sin conectar — data/README.md.`,
  cite:"cuota calibrada contra <code>gold_cuota_teorica.csv</code> (745 €/mes con Euríbor 2,80 %)"
},
{
  id:"03", pill:"🔑 Comprador", foot:"🔑 comprador de vivienda",
  h1:"🔑 Comprador de vivienda: ¿qué esfuerzo me exige el techo?",
  meta:"gold_cuota_teorica.csv · ine_salarios.csv (EAES) · ecb_euribor12m.csv · eurostat_hpi_q_es.csv · eurostat_overburden_es.csv",
  hot:["r","lam","z","pm"],
  outs:[
    {lab:"Precio mediano CCAA", k:"precio", d:0, u:"€", dial:[0,600000], note:"171.444 € (2024) capitalizado con el IPV del motor"},
    {lab:"Cuota mediana", k:"cuota", d:0, u:"€/mes", dial:[0,2000], note:"francesa · 80 % LTV · 25 años"},
    {lab:"Esfuerzo cuota/renta", k:"esf", d:1, u:"%", dial:[0,100], red:35, note:"cuota / (salario bruto/14) · regla prudencial 35 %"},
    {lab:"Precio vivienda a/a", k:"ipv", d:1, u:"%", dial:[-10,16], red:10, note:"reversión a 3 % − 2,6·Δr + 1,1·Δg"},
    {lab:"Sobrecarga vivienda", k:"sobre", d:1, u:"% hogares", dial:[0,25], note:"7,2 + 0,18·Δesfuerzo · Eurostat >40 % renta"}
  ],
  hA:{t:"El colateral corre más que Europa", s:"IPV España a/a trimestral · 2020-Q2 → 2026-Q1 · eurostat_hpi_q_es.csv", key:"vivienda_precio_yoy_5a", u:"%", red:10, lg:"IPV observado (📅 dato) · línea 10 %"},
  hB:{t:"La cuota contra la nómina", s:"esfuerzo = cuota / salario bruto mensual · 2026–2050", k:"esf", u:"%", red:35},
  reds:[
    {ic:"💶", t:"Esfuerzo cuota/renta > 35 %", thr:35, k:"esf", cmp:"gt", d:1, x:"regla prudencial [regla]"},
    {ic:"🏠", t:"Sobrecarga > 40 % renta", thr:15, k:"sobre", cmp:"gt", d:1, x:"definición Eurostat · muerde al flujo nuevo [UE]"},
    {ic:"📈", t:"IPV a/a > 10 %", thr:10, k:"ipv", cmp:"gt", d:1, x:"burbuja 2004-07 [hist]"}
  ],
  chains:[
    {a:"Euríbor", u:"cuota", t:"esfuerzo sobre la nómina", k:"esf", d:1, un:"%"},
    {a:"IPV", u:"entrada 20 %", t:"años de ahorro previo", k:"precio", d:0, un:"€"},
    {a:"salarios", u:"WS: π+λ+φ·holgura", t:"renta disponible", k:"salmes", d:0, un:"€/mes"}
  ],
  narr:(R,k,y)=>`En ${y} el precio mediano sale a ${eur(R.precio[k])} € — entrada del 20 %: ${eur(R.precio[k]*0.2)} € — y la cuota a ${eur(R.cuota[k])} €/mes contra un salario bruto de ${eur(R.salmes[k])} €/mes. El esfuerzo queda en ${nf(R.esf[k],1)} % frente a la regla prudencial del 35 %. Las dos ramas cuelgan de la misma palanca: el tipo mueve la cuota por arriba y el precio por abajo.`,
  cite:"anclado a <code>gold_cuota_teorica.csv</code> y <code>ine_salarios.csv</code> (EAES 2024)"
},
{
  id:"04", pill:"🚀 Emprendedor", foot:"🚀 emprendedor",
  h1:"🚀 ¿Aguanta el ciclo lo que tarda mi empresa en nacer?",
  meta:"eurostat_gdp_q_es.csv · eurostat_hicp_manr_es.csv · ecb_euribor12m.csv · eurostat_une_rt_m_es.csv · wb_self_employment.csv",
  hot:["r","ext","pm","sp"],
  outs:[
    {lab:"Ciclo · PIB real", k:"g", d:1, u:"% a/a", dial:[-4,8], red:0, note:"PIB potencial (λ+0,9) + cambio de nivel"},
    {lab:"Paro · talento", k:"u", d:1, u:"%", dial:[0,30], red:15, note:"u* − Okun·nivel · β = 0,48"},
    {lab:"IPCA · coste inputs", k:"pi", d:1, u:"% a/a", dial:[-2,14], red:4, note:"Phillips + pass-through de pᵐ"},
    {lab:"Euríbor · financiación", k:"r", d:2, u:"%", dial:[0,6], red:4, note:"palanca directa"},
    {lab:"Autoempleo", k:"auton", d:1, u:"% empleo", dial:[0,25], note:"14,5 + 0,12·Δu − 0,40·Δg"}
  ],
  hA:{t:"El ciclo que financia (o mata) el plan", s:"PIB real a/a trimestral · 2021-Q3 → 2026-Q2 · eurostat_gdp_q_es.csv", key:"pib_yoy_5a", u:"%", red:0, lg:"PIB observado (📅 dato)"},
  hB:{t:"El ciclo proyectado", s:"PIB real a/a 2026–2050 · escenario vs base", k:"g", u:"%", red:0},
  reds:[
    {ic:"📉", t:"PIB a/a < 0 %", thr:0, k:"g", cmp:"lt", d:1, x:"recesión técnica [regla]"},
    {ic:"🔥", t:"IPCA > 4 % sostenido", thr:4, k:"pi", cmp:"gt", d:1, x:"episodio 2022: pico 10,7 % (jul-2022) [hist]"},
    {ic:"💶", t:"Euríbor 12m > 4 %", thr:4, k:"r", cmp:"gt", d:2, x:"techo del ciclo de subidas 2023 [hist]"}
  ],
  chains:[
    {a:"BCE", u:"Euríbor", t:"coste del circulante", k:"r", d:2, un:"%"},
    {a:"IPCA", u:"costes input", t:"margen y precios propios", k:"pi", d:1, un:"%"},
    {a:"ciclo", u:"demanda", t:"supervivencia del proyecto", k:"g", d:1, un:"%"}
  ],
  narr:(R,k,y)=>`El plan de negocio apuesta a la vez por el ciclo y por los tipos: en ${y} la empresa paga el circulante al ${nf(R.r[k],2)} % y vende contra una demanda que crece al ${sg(R.g[k],1)} %, con costes de input al ${nf(R.pi[k],1)} % y un mercado laboral al ${nf(R.u[k],1)} % de paro. La desviación de nivel del PIB frente a la base es de ${sg(R.lvl[k],1)} puntos. El motor describe el terreno; no dice si emprender.`,
  cite:"multiplicador 1,4 y Okun 0,48 declarados en el rail · <code>PLAN_ESCENARIOS_CORE §4.2</code>"
},
{
  id:"05", pill:"🏛️ Funcionario", foot:"🏛️ funcionario",
  h1:"🏛️ ¿Mi nómina real sobrevive al ajuste que viene?",
  meta:"gov_10a_exp.csv · eurostat_gov_deficit_es.csv · eurostat_gov_debt_es.csv · eurostat_hicp_manr_es.csv",
  hot:["sp","idx","pm","dem"],
  outs:[
    {lab:"Masa salarial D1", k:"d1", d:2, u:"% PIB", dial:[0,15], note:"10,9 − 0,24·sp · D1 = 24 % del gasto total"},
    {lab:"Poder de compra nómina", k:"nomreal", d:1, u:"= 100 en 2026", dial:[60,130], red:100, note:"Π(1 + ι) · ι = IPC + palanca de indexación"},
    {lab:"IPCA · erosión", k:"pi", d:1, u:"% a/a", dial:[-2,14], red:4, note:"lo que hay que igualar para no perder"},
    {lab:"Saldo público", k:"saldo", d:1, u:"% PIB", dial:[-8,2], red:-3, note:"saldo primario − intereses · regla UE 3 %"},
    {lab:"Gasto total AAPP", k:"gtot", d:1, u:"% PIB", dial:[0,55], note:"45,4 − sp · pico 51,4 (2020) · mín 38,3 (2003)"}
  ],
  hA:{t:"El déficit: dos cráteres y una regla", s:"saldo público anual · 1995 → 2025 · eurostat_gov_deficit_es.csv", key:"deficit_pib_hist", u:"%", red:-3, lg:"saldo observado (📅 dato) · línea −3 %"},
  hB:{t:"La nómina real bajo la regla de indexación", s:"poder adquisitivo acumulado · 100 = 2026", k:"nomreal", u:"", red:100},
  reds:[
    {ic:"📜", t:"Déficit > 3 % PIB", thr:-3, k:"saldo", cmp:"lt", d:1, x:"procedimiento de déficit excesivo [regla UE]"},
    {ic:"🏛️", t:"Deuda > 105 % PIB", thr:105, k:"b", cmp:"gt", d:1, x:"umbral narrativo, no legal [comentario]"},
    {ic:"🧊", t:"Poder de compra < 100", thr:100, k:"nomreal", cmp:"lt", d:1, x:"congelaciones y recortes 2010-15 [hist]"}
  ],
  chains:[
    {a:"saldo primario", u:"regla fiscal UE", t:"presión sobre D1", k:"d1", d:2, un:"% PIB"},
    {a:"IPCA", u:"deflactor", t:"nómina real", k:"nomreal", d:1, un:"idx"},
    {a:"demografía", u:"gasto rígido", t:"espacio para lo discrecional", k:"b", d:1, un:"%PIB"}
  ],
  narr:(R,k,y)=>`La masa salarial pública es la mayor partida ajustable individual: en ${y} queda en ${nf(R.d1[k],2)} % del PIB. Con el IPCA al ${nf(R.pi[k],1)} % y la regla de indexación en IPC${L.idx>=0?"+":"−"}${nf(Math.abs(L.idx),1)} pp, el poder de compra acumulado desde 2026 va por ${nf(R.nomreal[k],1)} (base 100). El saldo público está en ${nf(R.saldo[k],1)} % del PIB frente al −3 % de la regla. El sistema proyecta la senda; no reparte el ajuste.`,
  cite:"pesos de gasto de <code>gov_10a_exp.csv</code> (2023) · senda fiscal de <code>gold_escenarios_deuda.csv</code>"
},
{
  id:"06", pill:"🗳️ Político", foot:"🗳️ político (decisor honesto)",
  h1:"🗳️ ¿Qué palanca puedo mover sin cruzar una línea roja?",
  meta:"eurostat_gov_debt_es · eurostat_gov_deficit_es · eurostat_une_rt_m_es · eurostat_gdp_q_es · interest_paid · gold_escenarios_deuda",
  hot:["sp","r","tau","z","lam","dem"],
  outs:[
    {lab:"Deuda pública", k:"b", d:1, u:"%PIB", dial:[0,180], red:105, note:"identidad · 105 y 120 como líneas"},
    {lab:"Saldo público", k:"saldo", d:1, u:"%PIB", dial:[-8,2], red:-3, note:"regla fiscal UE"},
    {lab:"Paro total", k:"u", d:1, u:"%", dial:[0,30], red:15, note:"u* (WS–PS) − Okun · el coste social de consolidar"},
    {lab:"PIB real", k:"g", d:1, u:"% a/a", dial:[-4,8], red:0, note:"potencial + cambio de nivel"},
    {lab:"Intereses", k:"int", d:1, u:"%PIB", dial:[0,8], red:5.0, note:"bₜ₋₁ · tipo efectivo · gasto que nadie elige · crowding-out"}
  ],
  hA:{t:"Dónde te pilla el ciclo", s:"saldo público anual 1995–2025 · % PIB · eurostat_gov_deficit_es.csv", key:"deficit_pib_hist", u:"%", red:-3, lg:"saldo observado (📅 dato)"},
  hB:{t:"El mapa de consecuencias", s:"deuda 2026–2050 · escenario vs base · banda p5–p95 heredada", k:"b", u:"%PIB", band:true, red:105},
  reds:[
    {ic:"🏛️", t:"Deuda > 120 % PIB", thr:120, k:"b", cmp:"gt", d:1, x:"techo COVID 2020: 119,3 [hist]"},
    {ic:"📜", t:"Déficit > 3 % PIB", thr:-3, k:"saldo", cmp:"lt", d:1, x:"regla fiscal UE [regla UE]"},
    {ic:"👥", t:"Paro > 15 %", thr:15, k:"u", cmp:"gt", d:1, x:"coste social del ajuste [hist]"}
  ],
  chains:[
    {a:"saldo primario", u:"bola de nieve r−g", t:"senda de deuda", k:"b", d:1, un:"%PIB"},
    {a:"palanca de gasto", u:"multiplicador 1,4", t:"paro", k:"u", d:1, un:"%"},
    {a:"tipos", u:"refinanciación", t:"espacio fiscal", k:"int", d:1, un:"%PIB"}
  ],
  narr:(R,k,y)=>`Ninguna palanca sale gratis y el tablero lo enseña: con este escenario la deuda de ${y} queda en ${nf(R.b[k],1)} %PIB, el saldo en ${nf(R.saldo[k],1)} y los intereses en ${nf(R.int[k],1)} puntos de PIB, mientras el paro se sitúa en ${nf(R.u[k],1)} % y el PIB crece al ${sg(R.g[k],1)} %. Consolidar desplaza la mediana pero no borra la banda; sostener el gasto apuntala el PIB de hoy y empina la senda. La elección «correcta» no aparece en ninguna columna del CSV.`,
  cite:"batería S0–S7 y elasticidades de <code>PLAN_ESCENARIOS_CORE §2.1/§4.2</code>"
},
{
  id:"07", pill:"🕳️ Corrupto", foot:"🕳️ político corrupto · sátira de transparencia",
  h1:"🕳️ ¿Dónde no mira nadie? — las partidas con más discrecionalidad, señaladas para quien SÍ mira",
  meta:"gov_10a_exp.csv (P2 · D3 · P51G) · interest_paid.csv",
  hot:["sp","dem"],
  outs:[
    {lab:"Consumo intermedio P2", k:"p2", d:2, u:"%PIB", dial:[0,10], note:"5,7 − 0,125·sp · contratación de bienes y servicios"},
    {lab:"Subvenciones D3", k:"d3", d:2, u:"%PIB", dial:[0,5], note:"1,4 − 0,031·sp · transferencias discrecionales"},
    {lab:"Inversión pública P51G", k:"p51", d:2, u:"%PIB", dial:[0,6], red:2, note:"3,0 − 0,145·sp · β 2,2× su peso (episodio 2009-16)"},
    {lab:"Gasto total", k:"gtot", d:1, u:"%PIB", dial:[0,60], note:"el denominador que difumina todo lo demás"},
    {lab:"Intereses D41", k:"int", d:1, u:"%PIB", dial:[0,8], note:"cero discrecionalidad: se paga sí o sí"}
  ],
  hA:{t:"La obra pública y su ciclo", s:"inversión pública P51G, % PIB, 1995–2023 · gov_10a_exp.csv", key:"inversion_publica_pib_hist", u:"%", red:2, lg:"P51G observado (📅 dato) · línea 2 %"},
  hB:{t:"Lo primero que se corta", s:"inversión pública proyectada · β 2,2× frente al gasto total", k:"p51", u:"%PIB", red:2},
  reds:[
    {ic:"🧾", t:"Contratos menores · adjudicación", thr:null, k:null, x:"la señal vive a nivel de contrato — sin serie pública [hueco de datos]"},
    {ic:"🌐", t:"WGI control de la corrupción", thr:null, k:null, x:"API archivada: descarga manual en govindicators.org [hueco de datos]"},
    {ic:"🏗️", t:"Inversión pública < 2 % PIB", thr:2, k:"p51", cmp:"lt", d:2, x:"cruzada en 2016-17 (2,0): obra parada = renegociación [hist]"}
  ],
  chains:[
    {a:"adjudicación", u:"sobrecoste", t:"consumo intermedio P2", k:"p2", d:2, un:"%PIB"},
    {a:"subvención", u:"clientela", t:"D3 no dice quién cobra", k:"d3", d:2, un:"%PIB"},
    {a:"obra pública", u:"modificados", t:"P51G solo enseña el total", k:"p51", d:2, un:"%PIB"}
  ],
  narr:(R,k,y)=>`Mueve la palanca fiscal y mira qué se encoge primero: en ${y} la inversión pública queda en ${nf(R.p51[k],2)} %PIB, el consumo intermedio en ${nf(R.p2[k],2)} y las subvenciones en ${nf(R.d3[k],2)}, mientras los intereses —los únicos que nadie puede desviar— se sitúan en ${nf(R.int[k],1)}. Los datos solo vigilan lo que se publica: se ve el bulto, nunca la mano. Cada serie que falta es una casilla que a alguien le conviene en blanco.`,
  cite:"agregados COFOG/ESA de <code>gov_10a_exp.csv</code> · huecos: contratación menor y WGI"
},
{
  id:"08", pill:"🧒 Infancia", foot:"🧒 infancia",
  h1:"🧒 ¿Qué país hereda quien hoy tiene 8 años?",
  meta:"eurostat_arop_child_es · eurostat_gov_edu_es · eurostat_gov_debt_es · gold_projections · gold_escenarios_deuda",
  hot:["sp","dem","z","lam"],
  outs:[
    {lab:"AROP infantil (<16)", k:"arop", d:1, u:"%", dial:[0,50], red:25, note:"28,5 + 0,55·Δu + 0,90·sp"},
    {lab:"Gasto en educación", k:"edu", d:2, u:"%PIB", dial:[0,8], red:4.8, note:"4,1 − 0,090·sp · línea = media UE27 4,8"},
    {lab:"Deuda heredada", k:"b", d:1, u:"%PIB", dial:[0,300], red:120, note:"la herencia que no eligió"},
    {lab:"Dependencia 65+", k:"dep", d:1, u:"/100", dial:[0,100], red:50, note:"deriva 32,6 → 59,0 amplificada por β₆₅ · gold_projections.csv"},
    {lab:"Esperanza de vida", k:"vida", d:1, u:"años", dial:[0,100], note:"84,0 (2024) · el horizonte que verá"}
  ],
  hA:{t:"La pobreza infantil no es coyuntura", s:"AROP <16 años, %, 1995–2025 · eurostat_arop_child_es.csv", key:"arop_infantil_hist", u:"%", red:25, lg:"AROP infantil observado (📅 dato) · línea 25 %"},
  hB:{t:"La herencia: deuda cuando cumpla 32", s:"deuda 2026–2050 · escenario vs base · banda heredada", k:"b", u:"%PIB", band:true, red:120},
  reds:[
    {ic:"🧒", t:"AROP infantil > 25 %", thr:25, k:"arop", cmp:"gt", d:1, x:"peor cuartil UE — cruzada de forma persistente [UE]"},
    {ic:"🎓", t:"Educación < 4,8 % PIB (UE27)", thr:4.8, k:"edu", cmp:"lt", d:2, x:"0,7 pp por debajo de la media UE27 [UE]"},
    {ic:"👴", t:"Dependencia > 50/100", thr:50, k:"dep", cmp:"gt", d:1, x:"sin precedente histórico [hist inédito]"}
  ],
  chains:[
    {a:"consolidación", u:"transferencias a familias", t:"AROP infantil", k:"arop", d:1, un:"%"},
    {a:"deuda hoy", u:"intereses mañana", t:"espacio fiscal de su generación", k:"int", d:1, un:"%PIB"},
    {a:"dependencia", u:"menos hombros", t:"cada activo sostiene a más mayores", k:"dep", d:1, un:"/100"}
  ],
  narr:(R,k,y)=>`Es el único perfil que no ha elegido nada: cada palanca que se mueva hoy aterriza en su ${y}, con la deuda en ${nf(R.b[k],1)} %PIB y ${nf(R.dep[k],1)} mayores por cada 100 personas en edad de trabajar. Su pobreza sí tiene palanca medida: el AROP infantil queda en ${nf(R.arop[k],1)} % y la educación en ${nf(R.edu[k],2)} %PIB frente al 4,8 de la UE27. El sistema no dice qué hacer; enseña quién cobra la factura de cada elección.`,
  cite:"palancas medidas de <code>gold_pobreza_infantil.csv</code> · demografía de <code>gold_projections.csv</code>"
},
{
  id:"09", pill:"🌅 Jubilado", foot:"🌅 jubilado",
  h1:"🌅 ¿Mi pensión sigue al IPC — y quién la paga en 2035?",
  meta:"eurostat_pensions_pcgdp_es.csv · eurostat_hicp_manr_es.csv · gold_projections.csv · life_expectancy_e0.csv",
  hot:["idx","dem","pm","sp"],
  outs:[
    {lab:"Gasto en pensiones", k:"pens", d:2, u:"% PIB", dial:[0,30], red:15, note:"13,23 × (dep/dep₂₀₂₆) × Π(1+π+ι)/(1+gₙ)"},
    {lab:"Poder de compra", k:"nomreal", d:1, u:"= 100 en 2026", dial:[60,130], red:100, note:"Π(1 + ι) · ι = regla de revalorización"},
    {lab:"IPCA · la referencia", k:"pi", d:1, u:"% a/a", dial:[-2,14], red:4, note:"lo que la indexación debe seguir"},
    {lab:"Dependencia 65+", k:"dep", d:1, u:"/100", dial:[0,80], red:50, note:"deriva 32,6 (2026) → 59,0 (2050) amplificada por β₆₅"},
    {lab:"Esperanza de vida", k:"vida", d:1, u:"años", dial:[0,100], note:"84,0 (2024) · más años que financiar"}
  ],
  hA:{t:"Lo que la indexación debe seguir", s:"IPCA mensual · 2021-01 → 2025-12 · eurostat_hicp_manr_es.csv", key:"hicp_es_5a", u:"%", red:4, lg:"IPCA observado (📅 dato) · línea 4 %"},
  hB:{t:"La factura de la demografía", s:"gasto en pensiones · % PIB · identidad mecánica 2026–2050", k:"pens", u:"%PIB", red:15},
  reds:[
    {ic:"👴", t:"Gasto pensiones > 15 % PIB", thr:15, k:"pens", cmp:"gt", d:2, x:"nunca alcanzado en la serie [hist inédito]"},
    {ic:"🧮", t:"Dependencia 65+ > 50/100", thr:50, k:"dep", cmp:"gt", d:1, x:"se cruza entre 2035 y 2050 [hist inédito]"},
    {ic:"📈", t:"Poder de compra < 100", thr:100, k:"nomreal", cmp:"lt", d:1, x:"la palanca ι es la que decide, no el IPC [regla]"}
  ],
  chains:[
    {a:"IPC", u:"regla ι", t:"pensión nominal del año siguiente", k:"nomreal", d:1, un:"idx"},
    {a:"demografía", u:"cohortes ya nacidas", t:"nº de pensiones", k:"dep", d:1, un:"/100"},
    {a:"crecimiento nominal", u:"denominador", t:"gasto en % del PIB", k:"pens", d:2, un:"%PIB"}
  ],
  narr:(R,k,y)=>`Aritmética sobre cohortes ya nacidas: la dependencia 65+ llega a ${nf(R.dep[k],1)} por cada 100 en edad de trabajar en ${y}, y con la regla de indexación en IPC${L.idx>=0?"+":"−"}${nf(Math.abs(L.idx),1)} pp el gasto en pensiones se sitúa en ${nf(R.pens[k],2)} % del PIB con un poder de compra acumulado de ${nf(R.nomreal[k],1)} (base 100). El abanico es estrecho en demografía y ancho en política. Identidad mecánica declarada: no incorpora altas, bajas ni empleo.`,
  cite:"demografía de <code>gold_projections.csv</code> · gasto de <code>eurostat_pensions_pcgdp_es.csv</code>"
},
{
  id:"10", pill:"🎓 Joven", foot:"🎓 joven que entra al mercado laboral",
  h1:"🎓 ¿Primer contrato o cola del paro — y podré irme de casa?",
  meta:"eurostat_une_rt_m_es.csv · eurostat_temp_share_es.csv · eurostat_hpi_q_es.csv · eurostat_overburden_es.csv · ine_salarios.csv",
  hot:["z","tau","ext","r","sp"],
  outs:[
    {lab:"Paro juvenil <25", k:"ujuv", d:1, u:"%", dial:[0,50], red:40, note:"2,317 × paro total · ratio estable en la serie 5a"},
    {lab:"Temporalidad", k:"temp", d:1, u:"% asalariados", dial:[0,35], red:25, note:"15,3 + 0,25·Δu − 1,5·z"},
    {lab:"Precio vivienda a/a", k:"ipv", d:1, u:"%", dial:[-10,16], red:10, note:"el muro de la emancipación"},
    {lab:"Sobrecarga vivienda", k:"sobre", d:1, u:"% hogares", dial:[0,25], note:"7,2 + 0,18·Δesfuerzo"},
    {lab:"Salario medio", k:"salario", d:0, u:"€/año", dial:[0,60000], note:"24.497 € (2024) capitalizado con la WS"}
  ],
  hA:{t:"Siempre ~2×: paro juvenil vs total", s:"mensual · 2021-07 → 2026-06 · eurostat_une_rt_m_es.csv", key:"paro_juvenil_5a", key2:"paro_total_5a", u:"%", lg:"paro juvenil (📅 dato) · paro total"},
  hB:{t:"El amortiguador del ciclo", s:"paro juvenil proyectado 2026–2050 · escenario vs base", k:"ujuv", u:"%", red:40},
  reds:[
    {ic:"🎓", t:"Paro juvenil > 40 %", thr:40, k:"ujuv", cmp:"gt", d:1, x:"cota del ciclo anterior; 2013 la superó [hist]"},
    {ic:"📝", t:"Temporalidad > 25 %", thr:25, k:"temp", cmp:"gt", d:1, x:"la serie vivió sobre ese nivel hasta 2022-Q1 [hist]"},
    {ic:"🏠", t:"IPV > +10 % a/a", thr:10, k:"ipv", cmp:"gt", d:1, x:"cinco trimestres seguidos >10 % en la serie [hist]"}
  ],
  chains:[
    {a:"ciclo", u:"LIFO", t:"paro juvenil ~2× el total", k:"ujuv", d:1, un:"%"},
    {a:"precio vivienda", u:"emancipación", t:"edad de salida", k:"ipv", d:1, un:"% a/a"},
    {a:"temporalidad", u:"renta no acreditable", t:"acceso a hipoteca", k:"temp", d:1, un:"%"}
  ],
  narr:(R,k,y)=>`El joven es el amortiguador del ciclo: la beta más alta del sistema. En ${y} su paro sale a ${nf(R.ujuv[k],1)} % con el total en ${nf(R.u[k],1)} %, y la temporalidad en ${nf(R.temp[k],1)} %. Superado el primer contrato aparece el segundo muro: vivienda al ${sg(R.ipv[k],1)} % anual frente a un salario medio de ${eur(R.salario[k])} € — y los salarios de entrada quedan por debajo de esa media. El sistema describe la secuencia; no la corrige.`,
  cite:"ratio juvenil/total calibrado sobre <code>eurostat_une_rt_m_es.csv</code> (serie 5a)"
},
{
  id:"11", pill:"📋 Indefinido", foot:"📋 trabajador indefinido",
  h1:"📋 ¿Crece mi salario por encima del IPC?",
  meta:"ine_salarios.csv · eurostat_hicp_manr_es.csv · eurostat_une_rt_m_es.csv · eurostat_temp_share_es.csv · eurostat_gdp_q_es.csv",
  hot:["lam","z","pm","tau"],
  outs:[
    {lab:"Salario real acumulado", k:"wrealIdx", d:1, u:"= 100 en 2026", dial:[60,180], red:100, note:"Π(1 + λ + φ·holgura) · WS–PS"},
    {lab:"Salario medio", k:"salario", d:0, u:"€/año", dial:[0,80000], note:"24.497 € × Π(1 + π + λ + φ·holgura)"},
    {lab:"IPCA · el listón", k:"pi", d:1, u:"% a/a", dial:[-2,14], red:4, note:"lo que hay que batir cada año"},
    {lab:"Paro total", k:"u", d:1, u:"%", dial:[0,30], red:15, note:"bajo el 15 % el poder insider se sostiene"},
    {lab:"Temporalidad", k:"temp", d:1, u:"% asalariados", dial:[0,35], red:25, note:"el mercado dual alrededor del indefinido"}
  ],
  hA:{t:"Los episodios de erosión", s:"IPCA mensual · 2021-01 → 2025-12 · eurostat_hicp_manr_es.csv", key:"hicp_es_5a", u:"%", red:4, lg:"IPCA observado (📅 dato) · línea 4 %"},
  hB:{t:"El salario real, año a año", s:"índice acumulado 100 = 2026 · escenario vs base", k:"wrealIdx", u:"", red:100},
  reds:[
    {ic:"📈", t:"IPCA > 4 % sostenido", thr:4, k:"pi", cmp:"gt", d:1, x:"cruzado en 2022-23: el salario real cayó [hist]"},
    {ic:"👥", t:"Paro > 15 %", thr:15, k:"u", cmp:"gt", d:1, x:"por encima, el poder de negociación se hunde [hist]"},
    {ic:"📉", t:"Salario real < 100", thr:100, k:"wrealIdx", cmp:"lt", d:1, x:"pérdida acumulada desde 2026 [aritmética]"}
  ],
  chains:[
    {a:"IPCA", u:"convenio (con retardo)", t:"salario nominal", k:"pi", d:1, un:"%"},
    {a:"paro", u:"poder insider", t:"deriva salarial", k:"u", d:1, un:"%"},
    {a:"productividad λ", u:"curva PS", t:"techo del salario real", k:"wrealIdx", d:1, un:"idx"}
  ],
  narr:(R,k,y)=>`El abanico del indefinido es el más estrecho de los doce, pero 2022 enseñó la cola. Con estas palancas, en ${y} el salario real acumulado desde 2026 va por ${nf(R.wrealIdx[k],1)} (base 100) y el nominal medio por ${eur(R.salario[k])} €/año, con el IPCA al ${nf(R.pi[k],1)} % y el paro al ${nf(R.u[k],1)} %. A largo plazo el techo lo pone la productividad: λ = ${nf(L.lam,1)} %/año. El sistema muestra la brecha; no negocia el convenio.`,
  cite:"curva WS con φ = 0,30 · serie salarial de <code>ine_salarios.csv</code> (EAES 2024)"
},
{
  id:"12", pill:"🧾 Autónomo", foot:"🧾 autónomo",
  h1:"🧾 ¿Caja, cuota y ciclo — en qué orden me golpean?",
  meta:"wb_self_employment.csv · eurostat_gdp_q_es.csv · eurostat_hicp_manr_es.csv · ecb_euribor12m.csv · eurostat_une_rt_m_es.csv",
  hot:["r","pm","ext","sp"],
  outs:[
    {lab:"Autoempleo", k:"auton", d:1, u:"% empleo", dial:[0,25], note:"14,5 + 0,12·Δu − 0,40·Δg"},
    {lab:"Ciclo · demanda", k:"g", d:1, u:"% a/a", dial:[-4,8], red:0, note:"la facturación que llena la caja"},
    {lab:"IPCA · coste inputs", k:"pi", d:1, u:"% a/a", dial:[-2,14], red:4, note:"Phillips + pass-through de pᵐ"},
    {lab:"Euríbor · póliza", k:"r", d:2, u:"%", dial:[0,6], red:4, note:"palanca directa · coste de la caja"},
    {lab:"Paro · repliegue", k:"u", d:1, u:"%", dial:[0,30], red:15, note:"el mercado al que se vuelve si cierra"}
  ],
  hA:{t:"Cada vez menos autónomos", s:"autoempleo, % del empleo total anual · 2001 → 2025 · wb_self_employment.csv", key:"autoempleo_hist", u:"%", lg:"autoempleo observado (📅 dato)"},
  hB:{t:"La demanda que llena (o vacía) la caja", s:"PIB real a/a 2026–2050 · escenario vs base", k:"g", u:"%", red:0},
  reds:[
    {ic:"📉", t:"PIB a/a < 0 %", thr:0, k:"g", cmp:"lt", d:1, x:"recesión técnica [regla]"},
    {ic:"🔥", t:"IPCA > 4 % sostenido", thr:4, k:"pi", cmp:"gt", d:1, x:"episodio 2022: pico 10,7 % [hist]"},
    {ic:"💶", t:"Euríbor 12m > 4 %", thr:4, k:"r", cmp:"gt", d:2, x:"techo del ciclo de subidas 2023 [hist]"}
  ],
  chains:[
    {a:"ciclo", u:"facturación", t:"caja — sin colchón salarial", k:"g", d:1, un:"%"},
    {a:"Euríbor", u:"póliza de crédito", t:"coste de la caja", k:"r", d:2, un:"%"},
    {a:"IPCA", u:"costes", t:"precios propios", k:"pi", d:1, un:"%"}
  ],
  narr:(R,k,y)=>`Triple exposición sin amortiguador de nómina: en ${y} la demanda crece al ${sg(R.g[k],1)} %, los costes al ${nf(R.pi[k],1)} % y el crédito cuesta ${nf(R.r[k],2)} %, con el mercado de repliegue al ${nf(R.u[k],1)} % de paro. Hueco documentado: las bases de cotización del RETA no tienen API pública (data/README.md), así que la senda de la cuota de autónomo no está modelada. El orden del golpe depende del escenario — el motor lo enseña, nunca como certeza ni como consejo.`,
  cite:"serie estructural de <code>wb_self_employment.csv</code> · huecos declarados en <code>data/README.md</code>"
}
];
```

---

## S3. Anchor numbers (read from the CSVs, not from code)

### S3.1 `gold_escenarios_deuda.csv` — central scenario

Full header: `escenario,year,deuda,pb,r_efectivo,g_nominal,presion_demog`

"Central" is identified by the `escenario` column equal to the literal string `central`
(confirmed in `build_v16.py` line: `row["escenario"] != "central": continue`). Unique values
of `escenario` in this file: ['central', 'consolidacion', 'crecimiento', 'inversion', 'sin_demografia', 'tipos_altos']

Central-scenario rows for 2026 / 2030 / 2035 / 2050 (exact field strings from the CSV):

| year | escenario | deuda | pb | r_efectivo | g_nominal | presion_demog |
|---|---|---|---|---|---|---|
| 2026 | central | 106.32 | -1.35 | 2.68 | 3.3 | 0.45 |
| 2030 | central | 112.9 | -2.47 | 3.02 | 3.3 | 1.57 |
| 2035 | central | 129.18 | -4.01 | 3.25 | 3.3 | 3.11 |
| 2050 | central | 223.86 | -7.47 | 3.47 | 3.3 | 6.57 |

Raw CSV lines (verbatim, comma-joined field values as read by `csv.DictReader`):
```
escenario,year,deuda,pb,r_efectivo,g_nominal,presion_demog
central,2026,106.32,-1.35,2.68,3.3,0.45
central,2030,112.9,-2.47,3.02,3.3,1.57
central,2035,129.18,-4.01,3.25,3.3,3.11
central,2050,223.86,-7.47,3.47,3.3,6.57
```

### S3.2 `gold_escenarios_deuda_mc.csv` — Monte Carlo percentiles

Full header: `escenario,year,p5,p25,p50,p75,p95`
Unique `escenario` values: ['central', 'consolidacion_2_5pp', 'crecimiento_alto', 'tipos_altos']

All scenarios × all percentiles for years 2030, 2050, 2070 (exact field strings):

| escenario | year | p5 | p25 | p50 | p75 | p95 |
|---|---|---|---|---|---|---|
| central | 2030 | 106.9 | 110.5 | 113.3 | 116.0 | 120.2 |
| central | 2050 | 177.7 | 207.1 | 231.3 | 258.0 | 302.5 |
| central | 2070 | 271.8 | 347.0 | 408.9 | 484.5 | 618.5 |
| consolidacion_2_5pp | 2030 | 96.9 | 100.6 | 103.3 | 106.1 | 110.0 |
| consolidacion_2_5pp | 2050 | 121.1 | 149.0 | 171.5 | 196.3 | 234.7 |
| consolidacion_2_5pp | 2070 | 174.0 | 239.8 | 298.0 | 364.9 | 482.1 |
| crecimiento_alto | 2030 | 100.2 | 103.8 | 106.4 | 108.9 | 112.8 |
| crecimiento_alto | 2050 | 149.6 | 175.8 | 196.3 | 219.3 | 255.7 |
| crecimiento_alto | 2070 | 213.5 | 273.7 | 321.3 | 379.4 | 481.2 |
| tipos_altos | 2030 | 109.4 | 113.3 | 116.1 | 119.0 | 123.3 |
| tipos_altos | 2050 | 203.3 | 237.4 | 264.2 | 293.7 | 344.1 |
| tipos_altos | 2070 | 344.6 | 438.7 | 518.3 | 612.9 | 783.5 |

Raw CSV lines:
```
escenario,year,p5,p25,p50,p75,p95
central,2030,106.9,110.5,113.3,116.0,120.2
central,2050,177.7,207.1,231.3,258.0,302.5
central,2070,271.8,347.0,408.9,484.5,618.5
consolidacion_2_5pp,2030,96.9,100.6,103.3,106.1,110.0
consolidacion_2_5pp,2050,121.1,149.0,171.5,196.3,234.7
consolidacion_2_5pp,2070,174.0,239.8,298.0,364.9,482.1
crecimiento_alto,2030,100.2,103.8,106.4,108.9,112.8
crecimiento_alto,2050,149.6,175.8,196.3,219.3,255.7
crecimiento_alto,2070,213.5,273.7,321.3,379.4,481.2
tipos_altos,2030,109.4,113.3,116.1,119.0,123.3
tipos_altos,2050,203.3,237.4,264.2,293.7,344.1
tipos_altos,2070,344.6,438.7,518.3,612.9,783.5
```

### S3.3 `gold_cuota_teorica.csv` — proving the €745/month figure

Full file (17 data rows, all CCAA + one `Nacional` aggregate row) — verbatim:
```
ccaa,eur_m2_2014,ipv14,ipv24,salario,eur_m2_2024,precio_vivienda,cuota_mensual,esfuerzo_pct,ratio_aseq_2024,supuestos
Andalucía,1204.92,97.08,158.47,23823.55,1966.96,177026.47,769.14,38.74,1.31,90m2 LTV80% 25a Euribor24(3.27)+1.0pp; ancla MITMA 2014 x IPV propio
Aragón,1154.18,99.16,151.04,26499.07,1758.06,158225.7,687.46,31.13,1.19,90m2 LTV80% 25a Euribor24(3.27)+1.0pp; ancla MITMA 2014 x IPV propio
"Asturias, Principado de",1297.03,98.51,141.1,26379.48,1857.72,167195.03,726.43,33.05,1.14,90m2 LTV80% 25a Euribor24(3.27)+1.0pp; ancla MITMA 2014 x IPV propio
"Balears, Illes",1883.32,93.99,174.24,27018.54,3491.51,314236.26,1365.29,60.64,1.29,90m2 LTV80% 25a Euribor24(3.27)+1.0pp; ancla MITMA 2014 x IPV propio
Canarias,1269.22,96.71,156.09,22876.11,2048.58,184371.82,801.06,42.02,1.26,90m2 LTV80% 25a Euribor24(3.27)+1.0pp; ancla MITMA 2014 x IPV propio
Cantabria,1486.92,97.21,156.31,25171.98,2390.94,215184.2,934.93,44.57,1.26,90m2 LTV80% 25a Euribor24(3.27)+1.0pp; ancla MITMA 2014 x IPV propio
Castilla - La Mancha,884.05,97.85,128.03,24053.78,1156.78,104110.49,452.34,22.57,1.02,90m2 LTV80% 25a Euribor24(3.27)+1.0pp; ancla MITMA 2014 x IPV propio
Castilla y León,1054.1,98.77,139.71,24372.12,1490.92,134182.48,583.0,28.7,1.14,90m2 LTV80% 25a Euribor24(3.27)+1.0pp; ancla MITMA 2014 x IPV propio
Cataluña,1654.45,95.4,168.59,29431.49,2923.89,263150.3,1143.34,46.62,1.3,90m2 LTV80% 25a Euribor24(3.27)+1.0pp; ancla MITMA 2014 x IPV propio
Extremadura,841.52,98.13,124.86,22942.04,1070.77,96369.2,418.7,21.9,0.99,90m2 LTV80% 25a Euribor24(3.27)+1.0pp; ancla MITMA 2014 x IPV propio
Galicia,1166.72,98.65,142.15,24575.2,1681.17,151305.31,657.39,32.1,1.11,90m2 LTV80% 25a Euribor24(3.27)+1.0pp; ancla MITMA 2014 x IPV propio
"Madrid, Comunidad de",2003.78,94.57,175.95,31223.88,3728.01,335521.3,1457.77,56.03,1.35,90m2 LTV80% 25a Euribor24(3.27)+1.0pp; ancla MITMA 2014 x IPV propio
"Murcia, Región de",988.92,98.37,143.77,24010.9,1445.38,130084.02,565.19,28.25,1.16,90m2 LTV80% 25a Euribor24(3.27)+1.0pp; ancla MITMA 2014 x IPV propio
Nacional,1449.72,96.55,159.66,27018.72,2397.34,215760.6,937.44,41.63,1.26,90m2 LTV80% 25a Euribor24(3.27)+1.0pp; ancla MITMA 2014 x IPV propio
"Navarra, Comunidad Foral de",1293.67,99.39,146.36,30995.15,1904.94,171444.46,744.89,28.84,1.12,90m2 LTV80% 25a Euribor24(3.27)+1.0pp; ancla MITMA 2014 x IPV propio
País Vasco,2422.07,99.04,147.9,33541.2,3616.89,325520.23,1414.32,50.6,1.16,90m2 LTV80% 25a Euribor24(3.27)+1.0pp; ancla MITMA 2014 x IPV propio
"Rioja, La",1069.85,99.48,145.98,26178.34,1569.9,141291.36,613.88,28.14,1.14,90m2 LTV80% 25a Euribor24(3.27)+1.0pp; ancla MITMA 2014 x IPV propio
```

`kpis_perfiles.json` → `kpi.cuota_hipoteca_mediana` = `{"valor": 745, "unidad": "EUR/mes (80% LTV, 25a)", "fuente": "gold_cuota_teorica.csv", "periodo": "2024"}`
`kpis_perfiles.json` → `kpi.precio_vivienda_mediano` = `{"valor": 171444, "unidad": "EUR", "fuente": "gold_cuota_teorica.csv", "periodo": "2024"}`
`kpis_perfiles.json` → `kpi.cuota_hipoteca_max` = `{"valor": {"ccaa": "Madrid, Comunidad de", "valor": 1458}, "unidad": "EUR/mes", "fuente": "gold_cuota_teorica.csv", "periodo": "2024"}`

**Provenance of 745 (verified by direct computation on the 17 rows, including `Nacional`):**
`statistics.median()` of the `cuota_mensual` column across all 17 rows = **744.89**
(rounds to 745). `statistics.median()` of `precio_vivienda` across the same 17 rows =
**171444.46** (rounds to 171444, matching `precio_vivienda_mediano`). Because there are 17
rows (odd count), the median is an actual row, not an average of two — and it is exactly the
`Navarra, Comunidad Foral de` row: `{"ccaa": "Navarra, Comunidad Foral de", "eur_m2_2014": "1293.67", "ipv14": "99.39", "ipv24": "146.36", "salario": "30995.15", "eur_m2_2024": "1904.94", "precio_vivienda": "171444.46", "cuota_mensual": "744.89", "esfuerzo_pct": "28.84", "ratio_aseq_2024": "1.12", "supuestos": "90m2 LTV80% 25a Euribor24(3.27)+1.0pp; ancla MITMA 2014 x IPV propio"}`.
So the "aggregate/CCAA" that identifies the €745/month figure is: the row-wise MEDIAN across the
16 CCAA + `Nacional` rows of `gold_cuota_teorica.csv`, column `cuota_mensual`, which happens to
land exactly on Navarra's row (744.89 → rounded to 745 in the KPI file).

### S3.4 Mortgage-spread solve (`build_v16.py`) — verbatim

Source: `/home/dan/projects/evo_final_work/legacy/design_data/design/v16_perfiles_lab/build_v16.py`, complete file (99 lines), verbatim:
```python
#!/usr/bin/env python3
"""
build_v16.py — genera design/v16_perfiles_lab/v16_perfiles_lab.html

v16 = v15 (12 perfiles, cifras reales) + laboratorio interactivo:
      las VARIABLES INDEPENDIENTES (§2.1 PLAN_ESCENARIOS_CORE) se mueven con
      sliders y todas las dependientes se recalculan con elasticidades declaradas.

Contrato de datos heredado: nada entra en la ficha sin pasar por data/.
Fuente única de cifras: data/kpis_perfiles.json  (+ gold_escenarios_deuda.csv
para la senda del escenario central y gold_projections.csv para demografía).

Reejecutable end-to-end:  python3 design/v16_perfiles_lab/build_v16.py
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
OUT = Path(__file__).resolve().parent / "v16_perfiles_lab.html"

# ---------------------------------------------------------------- data layer

kpis = json.loads((DATA / "kpis_perfiles.json").read_text(encoding="utf-8"))

# escenario central determinista: year -> {deuda, pb, r_efectivo, g_nominal, presion_demog}
central = {}
with (DATA / "gold" / "gold_escenarios_deuda.csv").open(encoding="utf-8") as fh:
    for row in csv.DictReader(fh):
        if row["escenario"] != "central":
            continue
        central[int(float(row["year"]))] = {
            "deuda": float(row["deuda"]),
            "pb": float(row["pb"]),
            "r_efectivo": float(row["r_efectivo"]),
            "g_nominal": float(row["g_nominal"]),
            "presion_demog": float(row["presion_demog"]),
        }

# ratio de dependencia 65+ (ES, variante baseline INE/Eurostat)
olddep = {}
with (DATA / "gold" / "gold_projections.csv").open(encoding="utf-8") as fh:
    for row in csv.DictReader(fh):
        if row["geo"] == "ES" and row["variant"] == "BSL":
            olddep[int(float(row["year"]))] = float(row["olddep"])

# diferencial hipotecario implícito: el que reproduce la cuota mediana teórica
# (745 €/mes, gold_cuota_teorica.csv) con Euríbor 12m = 2,80 % (ecb_euribor12m.csv)
precio = kpis["kpi"]["precio_vivienda_mediano"]["valor"]
cuota_obj = kpis["kpi"]["cuota_hipoteca_mediana"]["valor"]
euribor0 = kpis["kpi"]["euribor12m"]["valor"]


def cuota_francesa(principal: float, tipo_anual_pct: float, meses: int) -> float:
    i = tipo_anual_pct / 1200.0
    return principal * i / (1 - (1 + i) ** -meses)


lo, hi = 0.0, 6.0
for _ in range(80):
    mid = (lo + hi) / 2
    if cuota_francesa(precio * 0.8, euribor0 + mid, 300) < cuota_obj:
        lo = mid
    else:
        hi = mid
DIFERENCIAL = round(lo, 4)

payload = {
    "vintage": kpis["vintage"],
    "kpi": kpis["kpi"],
    "series": kpis["series"],
    "central": {str(y): v for y, v in sorted(central.items())},
    "olddep": {str(y): v for y, v in sorted(olddep.items()) if 2024 <= y <= 2060},
    "calib": {
        "diferencial_hipotecario": DIFERENCIAL,
        "salario_mes_bruto": round(kpis["kpi"]["salario_medio"]["valor"] / 14, 2),
        "i_ef_2025": round(
            kpis["kpi"]["intereses_deuda_pib"]["valor"]
            / kpis["kpi"]["deuda_pib_es"]["valor"]
            * 100,
            4,
        ),
    },
}

TEMPLATE = (Path(__file__).resolve().parent / "_v16_template.html").read_text(encoding="utf-8")
html = TEMPLATE.replace("/*__DATA__*/null", json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
OUT.write_text(html, encoding="utf-8")

print(f"escrito {OUT}  ({OUT.stat().st_size/1024:.1f} KB)")
print(f"  diferencial hipotecario implícito : {DIFERENCIAL:.4f} pp  -> cuota "
      f"{cuota_francesa(precio*0.8, euribor0+DIFERENCIAL, 300):.2f} €/mes")
print(f"  tipo efectivo de la deuda 2025    : {payload['calib']['i_ef_2025']:.3f} %")
print(f"  años escenario central            : {min(central)}–{max(central)}")
print(f"  dependencia 65+ 2026/2035/2050    : {olddep[2026]} / {olddep[2035]} / {olddep[2050]}")
```

**Resulting spread constant.** `build_v16.py` computes `DIFERENCIAL` via a bisection search (80
iterations over `[0.0, 6.0]`) solving for the mortgage-rate spread (over Euríbor12m) that makes
the French annuity formula (`cuota_francesa`, 80% LTV, 300 months) reproduce the €745/month
theoretical payment from `gold_cuota_teorica.csv`, then rounds to 4 decimals. The script is not
independently runnable here (it needs the full repo-relative `DATA` tree), so the resulting value
was read back out of the generated payload embedded in the built page
(`/home/dan/projects/evo_final_work/legacy/design_data/design/v16_perfiles_lab/v16_perfiles_lab.html`, the inlined `const D = {...}` object):
```json
{
  "diferencial_hipotecario": 1.4757,
  "salario_mes_bruto": 1749.79,
  "i_ef_2025": 2.3833
}
```
i.e. **`diferencial_hipotecario` = 1.4757** (percentage points, added to Euríbor12m + the `r`
lever inside `run()`: `french(precio * 0.8, L.r + C.DIFF, 300)`, template line 350). This is also
cross-referenced inside the engine constants block (S1) as `DIFF: CAL.diferencial_hipotecario`
(template line 298), i.e. the engine consumes exactly this solved value, not a separate literal.

---

## S4. Gold CSV schemas (all 9 files)

### `gold_escenarios_deuda.csv`
Row count (data rows, excluding header): **162**
```
escenario,year,deuda,pb,r_efectivo,g_nominal,presion_demog
central,2024,105.22,-0.9,2.43,3.3,0.0
central,2025,105.6,-1.13,2.57,3.3,0.23
```

### `gold_escenarios_deuda_mc.csv`
Row count (data rows, excluding header): **188**
```
escenario,year,p5,p25,p50,p75,p95
central,2024,104.4,104.9,105.2,105.6,106.1
central,2025,104.0,104.9,105.6,106.3,107.4
```

### `gold_cuota_teorica.csv`
Row count (data rows, excluding header): **17**
```
ccaa,eur_m2_2014,ipv14,ipv24,salario,eur_m2_2024,precio_vivienda,cuota_mensual,esfuerzo_pct,ratio_aseq_2024,supuestos
Andalucía,1204.92,97.08,158.47,23823.55,1966.96,177026.47,769.14,38.74,1.31,90m2 LTV80% 25a Euribor24(3.27)+1.0pp; ancla MITMA 2014 x IPV propio
Aragón,1154.18,99.16,151.04,26499.07,1758.06,158225.7,687.46,31.13,1.19,90m2 LTV80% 25a Euribor24(3.27)+1.0pp; ancla MITMA 2014 x IPV propio
```

### `gold_projections.csv`
Row count (data rows, excluding header): **9504**
```
geo,variant,year,population,net_migration,olddep,PC_Y0_14,PC_Y15_64,share65
AT,BSL,2023,9073118.0,35148.0,29.8,14.6,65.8,19.60000000000001
AT,BSL,2024,9101003.0,17990.0,30.4,14.6,65.5,19.900000000000006
```

### `gold_ccaa_trimestral.csv`
Row count (data rows, excluding header): **1540**
```
ccaa,anyo,quarter,ipv,ipv_nueva,ipv_segunda,ipc,salario_anual,salario_flag,ipv_b,sal_b,ipv_idx15,salario_idx15,ratio_asequibilidad
Andalucía,2007,1,70.93,49.302,83.012,68.94566666666667,,faltante,55.81525,19741.364999999998,127.07996470498655,,
Andalucía,2007,2,73.062,50.706,85.626,70.50166666666667,,faltante,55.81525,19741.364999999998,130.89970930883587,,
```

### `gold_asequibilidad_ccaa.csv`
Row count (data rows, excluding header): **306**
```
ccaa,anyo,ipv_indice,ipv_nueva,ipv_segunda,salario_medio,ipc_medio,ipv_idx15,salario_idx,ipc_idx15,ratio_asequibilidad,ratio_real
Andalucía,2008,75.0905,55.1205,83.4235,18755.255,73.17125,134.5340207201437,95.0048540209859,93.1863599845902,1.4160752322236723,1.5196164250410062
Andalucía,2009,72.6505,54.917500000000004,78.185,19386.205,72.832,130.16245560129175,98.20093494041573,92.75431225238974,1.325470635083759,1.4290124123577979
```

### `gold_pobreza_infantil.csv`
Row count (data rows, excluding header): **4**
```
palanca,cambio_transferencias,d_pobreza_infantil_pp,nivel_proyectado,ratio_infantil_total,reduccion_transferencias_es_pp,efecto_transferencias_infantil_pp,ciclo_predice
transferencias +25 %,0.25,-2.17,31.6,1.471,5.9,8.7,False
sin cambios,0.0,-0.0,33.8,1.471,5.9,8.7,False
```

### `gold_bienestar_pais.csv`
Row count (data rows, excluding header): **309**
```
iso3,y,rev,gdp_pc,urban,log_gdp,grupo,residual,semiancho_90,destacado,outcome,fecha_ejecucion
AFG,3.97,25.176,2937.483,23.931,7.985,Q1,0.173,0.683,False,mortalidad_u5_log,2026-07-19
AGO,3.892,27.458,11115.628,62.902,9.316,Q2,1.103,0.899,True,mortalidad_u5_log,2026-07-19
```

### `gold_fiscal_historico.csv`
Row count (data rows, excluding header): **3212**
```
iso3,year,exp_gdp,rev_gdp,fuente
AUS,1824,,1.7644218,gmd
AUS,1825,,2.4789283,gmd
```

---

## S5. `kpis_perfiles.json` shape

Top-level keys: `['vintage', 'fuentes', 'kpi', 'series']`

**NOT a per-persona structure.** `kpis_perfiles.json` has exactly 4 top-level keys —
`vintage`, `fuentes`, `kpi` (42 named indicators), `series` (21 named time series) — there is no
`personas` key and no per-persona sub-object in this file. The 12 personas exist only inside the
JS template's `P` array (see S2, `/home/dan/projects/evo_final_work/legacy/design_data/design/v16_perfiles_lab/_v16_template.html` lines 480–805). Each persona picks a subset of
`kpi`/`series` names to seed `V0` (template lines 252–277) and to key its `hA`/`hB` charts.
See the "NOT FOUND" section at the end for the exact discrepancy vs. the brief's assumption.

### 12 persona ids (exact spelling, from the `P` array, not from the JSON)

- `"01"` — pill: `💼 Bonista` — foot: `💼 bonista`
- `"02"` — pill: `🏦 Banca` — foot: `🏦 banca hipotecaria`
- `"03"` — pill: `🔑 Comprador` — foot: `🔑 comprador de vivienda`
- `"04"` — pill: `🚀 Emprendedor` — foot: `🚀 emprendedor`
- `"05"` — pill: `🏛️ Funcionario` — foot: `🏛️ funcionario`
- `"06"` — pill: `🗳️ Político` — foot: `🗳️ político (decisor honesto)`
- `"07"` — pill: `🕳️ Corrupto` — foot: `🕳️ político corrupto · sátira de transparencia`
- `"08"` — pill: `🧒 Infancia` — foot: `🧒 infancia`
- `"09"` — pill: `🌅 Jubilado` — foot: `🌅 jubilado`
- `"10"` — pill: `🎓 Joven` — foot: `🎓 joven que entra al mercado laboral`
- `"11"` — pill: `📋 Indefinido` — foot: `📋 trabajador indefinido`
- `"12"` — pill: `🧾 Autónomo` — foot: `🧾 autónomo`

### `fuentes` (verbatim)
```json
{
  "escenarios_mc": [
    "central",
    "consolidacion_2_5pp",
    "crecimiento_alto",
    "tipos_altos"
  ],
  "asequibilidad_nota": "ratio precario — usar gold_cuota_teorica para esfuerzo",
  "variantes_proyeccion": [
    "BSL",
    "HMIGR",
    "LFRT",
    "LMIGR",
    "LMRT",
    "NMIGR"
  ],
  "pobreza_infantil_palancas": [
    {
      "palanca": "transferencias +25 %",
      "cambio_transferencias": 0.25,
      "d_pobreza_infantil_pp": -2.17,
      "nivel_proyectado": 31.6,
      "ratio_infantil_total": 1.471,
      "reduccion_transferencias_es_pp": 5.9,
      "efecto_transferencias_infantil_pp": 8.7,
      "ciclo_predice": false
    },
    {
      "palanca": "sin cambios",
      "cambio_transferencias": 0.0,
      "d_pobreza_infantil_pp": -0.0,
      "nivel_proyectado": 33.8,
      "ratio_infantil_total": 1.471,
      "reduccion_transferencias_es_pp": 5.9,
      "efecto_transferencias_infantil_pp": 8.7,
      "ciclo_predice": false
    },
    {
      "palanca": "transferencias −50 %",
      "cambio_transferencias": -0.5,
      "d_pobreza_infantil_pp": 4.34,
      "nivel_proyectado": 38.1,
      "ratio_infantil_total": 1.471,
      "reduccion_transferencias_es_pp": 5.9,
      "efecto_transferencias_infantil_pp": 8.7,
      "ciclo_predice": false
    },
    {
      "palanca": "sin transferencias",
      "cambio_transferencias": -1.0,
      "d_pobreza_infantil_pp": 8.68,
      "nivel_proyectado": 42.5,
      "ratio_infantil_total": 1.471,
      "reduccion_transferencias_es_pp": 5.9,
      "efecto_transferencias_infantil_pp": 8.7,
      "ciclo_predice": false
    }
  ]
}
```

### Full list of the 42 `kpi` names (exact spelling, in file order)
```
bono10y_es
spread_es_de
euribor12m
hicp_es
hicp_eu27
paro_total
paro_juvenil
pib_yoy
deuda_pib_es
deuda_pib_de
deuda_pib_it
deuda_pib_eu27_2020
deficit_pib
vivienda_precio_yoy
vivienda_precio_yoy_eu27
sobrecarga_vivienda
arop_total
arop_infantil
gasto_pensiones_pib
gasto_pensiones_pib_eu27
gasto_educacion_pib
gasto_educacion_pib_eu27
temporalidad
autoempleo
ipc_ultimo
salario_medio
intereses_deuda_pib
consumo_intermedio_pib
subvenciones_pib
inversion_publica_pib
salarios_publicos_pib
gasto_total_pib
deuda_mc_2030
deuda_mc_2050
cuota_hipoteca_mediana
cuota_hipoteca_max
precio_vivienda_mediano
dependencia_65_2035
dependencia_65_2050
esperanza_vida
bls_endurecimiento
hipotecas_anuales
```

### Full list of the 21 `series` names (exact spelling, in file order)
```
bono10y_es_5a
spread_es_de_5a
euribor12m_5a
hicp_es_5a
paro_total_5a
paro_juvenil_5a
pib_yoy_5a
deuda_pib_es_hist
deficit_pib_hist
vivienda_precio_yoy_5a
arop_infantil_hist
gasto_pensiones_hist
temporalidad_hist
autoempleo_hist
salario_medio_hist
intereses_deuda_hist
inversion_publica_pib_hist
gasto_total_pib_hist
deuda_fan_p50
deuda_fan_p5
deuda_fan_p95
```

### Sample: the KPI/series entries the Jubilado persona (id `"09"`) actually consumes

The Jubilado block itself (verbatim JS, part of S2, template lines 698–724) references these
`R.*` output keys: `pens`, `nomreal`, `pi`, `dep`, `vida`; and series key `hicp_es_5a` for its `hA`
chart. Cross-referencing `V0` (template lines 252–277) and `run()` (template lines 306–386) back
to the raw KPI file, the underlying real-world entries are:

- `kpi.gasto_pensiones_pib` = `{"valor": 13.23, "unidad": "% PIB", "fuente": "eurostat_pensions_pcgdp_es.csv", "periodo": "2024"}`
- `kpi.hicp_es` = `{"valor": 3.0, "unidad": "% a/a", "fuente": "eurostat_hicp_manr_es.csv", "periodo": "2025-12"}`
- `kpi.esperanza_vida` = `{"valor": 84.0, "unidad": "años", "fuente": "life_expectancy_e0.csv", "periodo": "2024"}`
- `kpi.dependencia_65_2035` = `{"valor": 41.7, "unidad": "mayores por 100 en edad de trabajar", "fuente": "gold_projections.csv", "periodo": "2035"}`
- `kpi.dependencia_65_2050` = `{"valor": 59.0, "unidad": "mayores por 100 en edad de trabajar", "fuente": "gold_projections.csv", "periodo": "2050"}`
- `kpi.gasto_pensiones_pib_eu27` = `{"valor": 12.3, "unidad": "% PIB", "fuente": "eurostat_pensions_pcgdp_es.csv", "periodo": "2023"}`

- `series.hicp_es_5a` (complete entry, verbatim — this is the persona's `hA` chart source):
```json
{
  "puntos": [
    [
      "2021-01",
      0.4
    ],
    [
      "2021-02",
      -0.1
    ],
    [
      "2021-03",
      1.2
    ],
    [
      "2021-04",
      2.0
    ],
    [
      "2021-05",
      2.4
    ],
    [
      "2021-06",
      2.5
    ],
    [
      "2021-07",
      2.9
    ],
    [
      "2021-08",
      3.3
    ],
    [
      "2021-09",
      4.0
    ],
    [
      "2021-10",
      5.4
    ],
    [
      "2021-11",
      5.5
    ],
    [
      "2021-12",
      6.6
    ],
    [
      "2022-01",
      6.2
    ],
    [
      "2022-02",
      7.6
    ],
    [
      "2022-03",
      9.8
    ],
    [
      "2022-04",
      8.3
    ],
    [
      "2022-05",
      8.5
    ],
    [
      "2022-06",
      10.0
    ],
    [
      "2022-07",
      10.7
    ],
    [
      "2022-08",
      10.5
    ],
    [
      "2022-09",
      9.0
    ],
    [
      "2022-10",
      7.3
    ],
    [
      "2022-11",
      6.7
    ],
    [
      "2022-12",
      5.5
    ],
    [
      "2023-01",
      5.9
    ],
    [
      "2023-02",
      6.0
    ],
    [
      "2023-03",
      3.1
    ],
    [
      "2023-04",
      3.8
    ],
    [
      "2023-05",
      2.9
    ],
    [
      "2023-06",
      1.6
    ],
    [
      "2023-07",
      2.1
    ],
    [
      "2023-08",
      2.4
    ],
    [
      "2023-09",
      3.3
    ],
    [
      "2023-10",
      3.5
    ],
    [
      "2023-11",
      3.3
    ],
    [
      "2023-12",
      3.3
    ],
    [
      "2024-01",
      3.5
    ],
    [
      "2024-02",
      2.9
    ],
    [
      "2024-03",
      3.3
    ],
    [
      "2024-04",
      3.4
    ],
    [
      "2024-05",
      3.8
    ],
    [
      "2024-06",
      3.6
    ],
    [
      "2024-07",
      2.9
    ],
    [
      "2024-08",
      2.4
    ],
    [
      "2024-09",
      1.7
    ],
    [
      "2024-10",
      1.8
    ],
    [
      "2024-11",
      2.4
    ],
    [
      "2024-12",
      2.8
    ],
    [
      "2025-01",
      2.9
    ],
    [
      "2025-02",
      2.9
    ],
    [
      "2025-03",
      2.2
    ],
    [
      "2025-04",
      2.2
    ],
    [
      "2025-05",
      2.0
    ],
    [
      "2025-06",
      2.3
    ],
    [
      "2025-07",
      2.7
    ],
    [
      "2025-08",
      2.7
    ],
    [
      "2025-09",
      3.0
    ],
    [
      "2025-10",
      3.2
    ],
    [
      "2025-11",
      3.2
    ],
    [
      "2025-12",
      3.0
    ]
  ],
  "fuente": "eurostat_hicp_manr_es.csv"
}
```

---

## S6. Presets S0–S7 verbatim

Source: `/home/dan/projects/evo_final_work/legacy/design_data/design/v16_perfiles_lab/_v16_template.html`, lines 402–411 (`const PRESETS = [ ... ];`) — duplicated here standalone for
convenience; identical text also appears inline inside S1's block (lines 239–416).

```js
const PRESETS = [
  {id:"S0", nm:"S0 base",            set:{}},
  {id:"S1", nm:"S1 tipos +200 pb",   set:{r: BASE.r + 2}},
  {id:"S2", nm:"S2 petróleo +50 %",  set:{pm: 50}},
  {id:"S3", nm:"S3 consolidación",   set:{sp: 1.0}},
  {id:"S4", nm:"S4 productividad",   set:{lam: 1.4}},
  {id:"S5", nm:"S5 desregulación lab.", set:{z: -1.0, tau: -1.5}},
  {id:"S6", nm:"S6 envejecimiento",  set:{dem: 0.6}},
  {id:"S7", nm:"S7 adverso",         set:{r: BASE.r + 2, pm: 50, prima: 150}}
];
```

For reference, `BASE` (the S0/no-lever-moved starting point every preset deviates from),
`/home/dan/projects/evo_final_work/legacy/design_data/design/v16_perfiles_lab/_v16_template.html` lines 280–281:
```js
const BASE = {r: K.euribor12m.valor, prima: K.spread_es_de.valor, sp: 0, lam: 0.9,
              pm: 0, tau: 0, z: 0, ext: 1.8, dem: 0, idx: 0};
```

---

## S7. Red-line values (semáforo thresholds) in v16, and v12's limits/sources table

### S7.1 v16 — every `reds:` threshold object in the template, verbatim

Extracted from `/home/dan/projects/evo_final_work/legacy/design_data/design/v16_perfiles_lab/_v16_template.html` by matching every line containing both `{ic:` and `thr:` (the shape
of every semáforo threshold entry across all 12 personas' `reds:[...]` arrays). All of these are
also present in context inside the full S2 dump (lines 480–805); this is the flat, dedicated list.

```js
/* line 496 */ {ic:"🏛️", t:"Deuda > 105 %PIB", thr:105, k:"b", cmp:"gt", d:1, x:"narrativa crack23 [comentario]"},
/* line 497 */ {ic:"🏛️", t:"Deuda > 120 %PIB", thr:120, k:"b", cmp:"gt", d:1, x:"techo COVID 2020: 119,3 [hist]"},
/* line 498 */ {ic:"💶", t:"Bono 10A > 7 %", thr:7, k:"bono", cmp:"gt", d:2, x:"zona rescate: crisis 2012 [hist]"}
/* line 523 */ {ic:"🏠", t:"IPV real a/a > 10 %", thr:10, k:"ipvreal", cmp:"gt", d:1, x:"burbuja 2004-07 [hist] · IPV nominal − IPCA"},
/* line 524 */ {ic:"🏦", t:"BLS endurecimiento > 20 %", thr:20, k:"bls", cmp:"gt", d:0, x:"nivel de contracción de crédito [hist]"},
/* line 525 */ {ic:"📉", t:"Paro > 15 % (motor de mora)", thr:15, k:"u", cmp:"gt", d:1, x:"último nivel visto en 2021-07 (15,2) [hist]"}
/* line 550 */ {ic:"💶", t:"Esfuerzo cuota/renta > 35 %", thr:35, k:"esf", cmp:"gt", d:1, x:"regla prudencial [regla]"},
/* line 551 */ {ic:"🏠", t:"Sobrecarga > 40 % renta", thr:15, k:"sobre", cmp:"gt", d:1, x:"definición Eurostat · muerde al flujo nuevo [UE]"},
/* line 552 */ {ic:"📈", t:"IPV a/a > 10 %", thr:10, k:"ipv", cmp:"gt", d:1, x:"burbuja 2004-07 [hist]"}
/* line 577 */ {ic:"📉", t:"PIB a/a < 0 %", thr:0, k:"g", cmp:"lt", d:1, x:"recesión técnica [regla]"},
/* line 578 */ {ic:"🔥", t:"IPCA > 4 % sostenido", thr:4, k:"pi", cmp:"gt", d:1, x:"episodio 2022: pico 10,7 % (jul-2022) [hist]"},
/* line 579 */ {ic:"💶", t:"Euríbor 12m > 4 %", thr:4, k:"r", cmp:"gt", d:2, x:"techo del ciclo de subidas 2023 [hist]"}
/* line 604 */ {ic:"📜", t:"Déficit > 3 % PIB", thr:-3, k:"saldo", cmp:"lt", d:1, x:"procedimiento de déficit excesivo [regla UE]"},
/* line 605 */ {ic:"🏛️", t:"Deuda > 105 % PIB", thr:105, k:"b", cmp:"gt", d:1, x:"umbral narrativo, no legal [comentario]"},
/* line 606 */ {ic:"🧊", t:"Poder de compra < 100", thr:100, k:"nomreal", cmp:"lt", d:1, x:"congelaciones y recortes 2010-15 [hist]"}
/* line 631 */ {ic:"🏛️", t:"Deuda > 120 % PIB", thr:120, k:"b", cmp:"gt", d:1, x:"techo COVID 2020: 119,3 [hist]"},
/* line 632 */ {ic:"📜", t:"Déficit > 3 % PIB", thr:-3, k:"saldo", cmp:"lt", d:1, x:"regla fiscal UE [regla UE]"},
/* line 633 */ {ic:"👥", t:"Paro > 15 %", thr:15, k:"u", cmp:"gt", d:1, x:"coste social del ajuste [hist]"}
/* line 658 */ {ic:"🧾", t:"Contratos menores · adjudicación", thr:null, k:null, x:"la señal vive a nivel de contrato — sin serie pública [hueco de datos]"},
/* line 659 */ {ic:"🌐", t:"WGI control de la corrupción", thr:null, k:null, x:"API archivada: descarga manual en govindicators.org [hueco de datos]"},
/* line 660 */ {ic:"🏗️", t:"Inversión pública < 2 % PIB", thr:2, k:"p51", cmp:"lt", d:2, x:"cruzada en 2016-17 (2,0): obra parada = renegociación [hist]"}
/* line 685 */ {ic:"🧒", t:"AROP infantil > 25 %", thr:25, k:"arop", cmp:"gt", d:1, x:"peor cuartil UE — cruzada de forma persistente [UE]"},
/* line 686 */ {ic:"🎓", t:"Educación < 4,8 % PIB (UE27)", thr:4.8, k:"edu", cmp:"lt", d:2, x:"0,7 pp por debajo de la media UE27 [UE]"},
/* line 687 */ {ic:"👴", t:"Dependencia > 50/100", thr:50, k:"dep", cmp:"gt", d:1, x:"sin precedente histórico [hist inédito]"}
/* line 712 */ {ic:"👴", t:"Gasto pensiones > 15 % PIB", thr:15, k:"pens", cmp:"gt", d:2, x:"nunca alcanzado en la serie [hist inédito]"},
/* line 713 */ {ic:"🧮", t:"Dependencia 65+ > 50/100", thr:50, k:"dep", cmp:"gt", d:1, x:"se cruza entre 2035 y 2050 [hist inédito]"},
/* line 714 */ {ic:"📈", t:"Poder de compra < 100", thr:100, k:"nomreal", cmp:"lt", d:1, x:"la palanca ι es la que decide, no el IPC [regla]"}
/* line 739 */ {ic:"🎓", t:"Paro juvenil > 40 %", thr:40, k:"ujuv", cmp:"gt", d:1, x:"cota del ciclo anterior; 2013 la superó [hist]"},
/* line 740 */ {ic:"📝", t:"Temporalidad > 25 %", thr:25, k:"temp", cmp:"gt", d:1, x:"la serie vivió sobre ese nivel hasta 2022-Q1 [hist]"},
/* line 741 */ {ic:"🏠", t:"IPV > +10 % a/a", thr:10, k:"ipv", cmp:"gt", d:1, x:"cinco trimestres seguidos >10 % en la serie [hist]"}
/* line 766 */ {ic:"📈", t:"IPCA > 4 % sostenido", thr:4, k:"pi", cmp:"gt", d:1, x:"cruzado en 2022-23: el salario real cayó [hist]"},
/* line 767 */ {ic:"👥", t:"Paro > 15 %", thr:15, k:"u", cmp:"gt", d:1, x:"por encima, el poder de negociación se hunde [hist]"},
/* line 768 */ {ic:"📉", t:"Salario real < 100", thr:100, k:"wrealIdx", cmp:"lt", d:1, x:"pérdida acumulada desde 2026 [aritmética]"}
/* line 793 */ {ic:"📉", t:"PIB a/a < 0 %", thr:0, k:"g", cmp:"lt", d:1, x:"recesión técnica [regla]"},
/* line 794 */ {ic:"🔥", t:"IPCA > 4 % sostenido", thr:4, k:"pi", cmp:"gt", d:1, x:"episodio 2022: pico 10,7 % [hist]"},
/* line 795 */ {ic:"💶", t:"Euríbor 12m > 4 %", thr:4, k:"r", cmp:"gt", d:2, x:"techo del ciclo de subidas 2023 [hist]"}
```

### S7.2 v12 — `v12_limites_fuentes.md`, complete file, verbatim

Source: `/home/dan/projects/evo_final_work/legacy/design_data/design/v12_limites_fuentes.md` (36 lines, full file reproduced below).

```markdown
# v12 — límites de los sliders y fuentes

Cada palanca del laboratorio de escenarios lleva un rango acotado empíricamente. Fuentes: `crack23/` (corpus del canal "El crack del 23", citas ≤15 palabras), `core_econ/` (CORE Econ, por unidad), `hist` (serie histórica oficial ES/EU conocida, se verificará contra gold).

## Palancas (independientes)

| # | Palanca | Mín | Base | Máx | Anclas y fuente |
|---|---|---:|---:|---:|---|
| 1 | Bono 10a ES (rendimiento) | 0,5 % | 3,2 % | **7,0 %** | Cap solicitado por el usuario = zona rescate: GRC/PRT/IRL pidieron rescate con bonos ≈7 %; ES tocó 7,6 % en jul-2012 [hist]. crack23: «pronto vamos a escuchar palabras de rescate» con Francia ≈4 % y prima ≈90 pb [crack23/telegram] |
| 2 | Euríbor 12m | −0,5 % | 2,6 % | 5,5 % | Mín −0,50 % (2021); máx 5,39 % (jul-2008) [hist]. crack23: «Euribor ya está en el 2,85 … llegaremos al 4 y medio», escenario crisis «acaba yéndose al 5 %» [crack23/markdown] |
| 3 | Shock petróleo/importaciones (Δ precio) | −50 % | 0 % | +150 % | CORE U4: primer shock 1973–74 (≈×4 nominal) inaugura la «alta inflación de los 70»; shocks 1973/1979/2022 marcados como episodios canónicos [CORE macro U4] |
| 4 | Saldo primario | −11 % PIB | −1,0 % | +4 % PIB | Déficit total ES 2009 ≈ −11,3 % PIB; superávits primarios ~+3 % en 1996–2007 [hist]. Doctrina deuda: recursión E3 |
| 5 | Productividad (λ, Δ anual) | −1,0 % | +0,7 % | +2,5 % | Rango histórico ES 1995–2024; convergencia europea como techo [hist; CORE U1: λ desplaza la PS] |
| 6 | Precio vivienda (Δ anual) | −15 % | +4 % | +15 % | Caída 2008–2013 ≈ −37 % acumulada (picos anuales ≈ −10/−15 %); burbuja 2003–07 ≈ +15 %/a [hist] |
| 7 | Gasto en pensiones (envejecimiento) | 13,2 % PIB | 13,2→15,1 % | 16,0 % PIB | β65 = 0,91 «los 65+ de 2035 ya nacieron» (senda D1); variante INE pesimista como techo [FINAL_PREDICTOR §E3; proyecciones INE] |
| 8 | Crecimiento eurozona (demanda externa g*) | −4,0 % | +1,2 % | +3,0 % | 2009 eurozona ≈ −4,5 %; techo = mejores años pre-2008 [hist; CORE U3 canal exportaciones] |

## Resultados (dependientes) con «líneas rojas»

| Resultado | Rango del dial | Línea roja | Ancla |
|---|---:|---:|---|
| Deuda/PIB 2035 | 60–160 % | 105 % / 120 % | crack23: «deuda brutal que ya está por encima del 105 %»; 120 % ≈ pico COVID ES [crack23; hist] |
| Crecimiento PIB (media 2026–35) | −3 – +4 % | < 0 % | recesión sostenida |
| Inflación (media) | −1 – +12 % | > 10 % | crack23: «la ola inflacionaria del 2022 que nos llevó por encima del 10 %»; ES pico 10,8 % jul-2022 [crack23; hist] |
| Paro | 6 – 28 % | 26,9 % | máximo histórico ES (T1-2013); CORE fig. 2.29: rango ES ≈3 %→~26 % 1960–2022 [CORE macro U2; hist] |
| Déficit público | −12 – +2 % PIB | −3 % / −11,3 % | umbral Maastricht; suelo 2009 [hist] |
| Esfuerzo vivienda (alquiler+hipoteca / renta) | 15–55 % | 40 % | umbral de sobrecarga de coste de vivienda (Eurostat housing cost overburden) [hist; puente F3] |
| Poder adquisitivo (renta real per cápita PPA, índice 2025=100) | 85–115 | < 95 | pérdida ≥5 pp ≈ década perdida (cf. 2008–13) [hist; puente F2] |
| Pobreza infantil (AROP <18) | 15–35 % | 30 % | ES ≈ 27–28 % reciente, pico ≈ 30 %+ post-2013; media UE ≈ 19 % [hist Eurostat ilc_li02; bloque F3] |

## Notas de método

- Los rangos de sliders son ENVOLVENTES históricas (lo vivido), no límites físicos; superarlos exigiría justificar un régimen nuevo — por eso el slider se detiene ahí (doctrina: escenarios condicionales al régimen histórico).
- El corpus crack23 aporta los umbrales narrativos («líneas rojas» del relato de crisis); siempre contrastados con la serie oficial antes de fijarlos en el motor (AC-E1/E2 de PLAN_ESCENARIOS_CORE.md).
- Anclas [hist] pendientes de verificación numérica contra la capa gold cuando el conector correspondiente esté cargado (D1–D6).
```

---

## NOT FOUND / discrepancies vs. the brief

- **`kpis_perfiles.json` is not organized by persona.** The brief (S5) asked for "the 12 persona
  ids/keys exactly as spelled" and "for ONE persona ... the complete KPI + series entries" as if
  the JSON itself had a per-persona structure. It does not — its 4 top-level keys are `vintage`,
  `fuentes`, `kpi`, `series`. The 12 persona ids/labels live exclusively in the JS `P` array inside
  `/home/dan/projects/evo_final_work/legacy/design_data/design/v16_perfiles_lab/_v16_template.html` (lines 480–805, id list captured in S2/S5 above). Handled by pulling the persona
  ids from the JS and cross-referencing which `kpi`/`series` entries each persona's block actually
  reads.
- **`build_v16.py`'s bisection solve is not independently re-runnable from this extraction task**
  (it imports `ROOT = Path(__file__).resolve().parents[2]` and reads `DATA/kpis_perfiles.json` and
  `DATA/gold/*.csv` via repo-relative paths that work when run as the actual repo script — re-
  executing it standalone here was avoidable risk for a read-only extraction task). Instead, the
  resulting `DIFERENCIAL` value (1.4757) was read back from the already-built output page's
  embedded JSON payload (`/home/dan/projects/evo_final_work/legacy/design_data/design/v16_perfiles_lab/v16_perfiles_lab.html`), which is the literal output of that same script for this
  vintage — same value, verified source.
- **Everything else the brief named was found on disk**: `manifest.csv` and
  `provenance_vintage_manifest.csv` both exist under `legacy/design_data/data/` (not requested for
  detailed extraction by S1–S7, but confirmed present; schemas below for completeness) —
  `manifest.csv` header `['source', 'url', 'fetched', 'bytes', 'raw_file', 'processed_file']` (16 data rows);
  `provenance_vintage_manifest.csv` header `['name', 'url', 'fetched_at', 'bytes']` (141 data rows).
- `v12_limites_fuentes.md` was found directly under `legacy/design_data/design/` (not nested in a
  `v12_scenario_lab/` subdirectory as the brief's phrasing suggested — there is no
  `v12_scenario_lab/` directory; the actual v12 artifact directory is named differently — files are
  `design/v12_limites_fuentes.md`, `design/v12_laboratorio_escenarios.html/.png/.pdf`).

