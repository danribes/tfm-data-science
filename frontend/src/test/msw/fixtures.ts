import type { PersonaCard, PresetOut } from "../../api/types";
import type { RedLineDef } from "../../engine/redlines";

export const MOCK_VINTAGE = "2026-07-31";

export const mockPresets: PresetOut[] = [
  { id: "S0", nm: "S0 base", set: {} },
  { id: "S1", nm: "S1 tipos +200 pb", set: { r: 4.8 } },
  { id: "S2", nm: "S2 petróleo +50 %", set: { pm: 50.0 } },
  { id: "S3", nm: "S3 consolidación", set: { sp: 1.0 } },
  { id: "S4", nm: "S4 productividad", set: { lam: 1.4 } },
  { id: "S5", nm: "S5 desregulación lab.", set: { z: -1.0, tau: -1.5 } },
  { id: "S6", nm: "S6 envejecimiento", set: { dem: 0.6 } },
  { id: "S7", nm: "S7 adverso", set: { r: 4.8, pm: 50.0, prima: 150.0 } },
];

export const mockRedlines: RedLineDef[] = [
  { id: "bono_rescate", label: "Bono 10A > 7 %", series: "bono", threshold: 7.0, cmp: "gt", source: "zona rescate: GRC/PRT/IRL pidieron rescate con bonos ≈7 %; ES tocó 7,6 % en jul-2012 [hist]" },
  { id: "paro_record", label: "Paro > 26,9 %", series: "u", threshold: 26.9, cmp: "gt", source: "máximo histórico ES (T1-2013) [hist]" },
  { id: "deficit_maastricht", label: "Déficit > 3 % PIB", series: "saldo", threshold: -3.0, cmp: "lt", source: "umbral Maastricht [regla UE]" },
  { id: "deficit_suelo_2009", label: "Déficit > 11,3 % PIB", series: "saldo", threshold: -11.3, cmp: "lt", source: "suelo 2009: ES −11,3 % PIB [hist]" },
  { id: "deuda_105", label: "Deuda > 105 % PIB", series: "b", threshold: 105.0, cmp: "gt", source: "crack23: «deuda brutal que ya está por encima del 105 %» [comentario]" },
  { id: "deuda_120", label: "Deuda > 120 % PIB", series: "b", threshold: 120.0, cmp: "gt", source: "≈ pico COVID ES 2020: 119,3 [hist]" },
  { id: "inflacion_10", label: "Inflación > 10 %", series: "pi", threshold: 10.0, cmp: "gt", source: "ola inflacionaria 2022: ES pico 10,8 % jul-2022 [hist]" },
  { id: "esfuerzo_40", label: "Esfuerzo vivienda > 40 %", series: "esf", threshold: 40.0, cmp: "gt", source: "definición Eurostat de sobrecarga (housing cost overburden) [UE]" },
  { id: "pobreza_infantil_30", label: "Pobreza infantil > 30 %", series: "arop", threshold: 30.0, cmp: "gt", source: "ES 27–28 % crónico, 30 % en picos post-2013; media UE ≈19 % [hist]" },
];

/** The 4 shipped cards — verbatim from the phase-1 /personas payload (engine/spain.py PERSONAS). */
// Generated from engine/spain.py PERSONAS — the same twelve cards the server
// serves. Hand-maintaining this list let the mock fall four personas behind the
// app, which kept a test passing under a name that had stopped being true.
// Regenerate with: python -m tools.gen_persona_fixture
export const mockPersonaCards: PersonaCard[] = [
  {
    id: "01",
    pill: "💼 Bonista",
    foot: "💼 bonista",
    h1: "💼 Inversor en bonos: ¿me pagarán los 10 años?",
    meta: "ecb_bono10y_es.csv · ecb_bono10y_de.csv · eurostat_gov_debt_es.csv · eurostat_gov_deficit_es.csv · interest_paid.csv · gold_escenarios_deuda.csv",
    hot: ["r", "prima", "sp", "dem"],
    series_keys: ["bono10y_es_5a"],
    outs: [{ k: "bono", lab: "Bono 10A España" }, { k: "spread", lab: "Spread ES–DE" }, { k: "b", lab: "Deuda pública" }, { k: "saldo", lab: "Saldo público" }, { k: "int", lab: "Intereses / PIB" }],
    headline: "b",
    reds: [{ t: "Deuda > 105 %PIB", thr: 105.0, k: "b", cmp: "gt", d: 1, x: "narrativa crack23 [comentario]" }, { t: "Deuda > 120 %PIB", thr: 120.0, k: "b", cmp: "gt", d: 1, x: "techo COVID 2020: 119,3 [hist]" }, { t: "Bono 10A > 7 %", thr: 7.0, k: "bono", cmp: "gt", d: 2, x: "zona rescate: crisis 2012 [hist]" }],
  },
  {
    id: "02",
    pill: "🏦 Banca",
    foot: "🏦 banca hipotecaria",
    h1: "🏦 Banco hipotecario: ¿a quién presto, a qué tipo y con qué mora esperada?",
    meta: "ecb_euribor12m.csv · bls_criterios_vivienda.csv · ine_hipotecas_ccaa.csv · eurostat_hpi_q_es.csv · gold_cuota_teorica.csv",
    hot: ["r", "z", "tau", "ext"],
    series_keys: ["euribor12m_5a"],
    outs: [{ k: "r", lab: "Euríbor 12m" }, { k: "bls", lab: "BLS endurecimiento" }, { k: "hip", lab: "Nueva producción" }, { k: "ipv", lab: "Precio vivienda a/a" }, { k: "cuota", lab: "Cuota mediana" }],
    headline: "cuota",
    reds: [{ t: "IPV real a/a > 10 %", thr: 10.0, k: "ipvreal", cmp: "gt", d: 1, x: "burbuja 2004-07 [hist] · IPV nominal − IPCA" }, { t: "BLS endurecimiento > 20 %", thr: 20.0, k: "bls", cmp: "gt", d: 0, x: "nivel de contracción de crédito [hist]" }, { t: "Paro > 15 % (motor de mora)", thr: 15.0, k: "u", cmp: "gt", d: 1, x: "último nivel visto en 2021-07 (15,2) [hist]" }],
  },
  {
    id: "03",
    pill: "🔑 Comprador",
    foot: "🔑 comprador de vivienda",
    h1: "🔑 Comprador de vivienda: ¿qué esfuerzo me exige el techo?",
    meta: "gold_cuota_teorica.csv · ine_salarios.csv (EAES) · ecb_euribor12m.csv · eurostat_hpi_q_es.csv · eurostat_overburden_es.csv",
    hot: ["r", "lam", "z", "pm"],
    series_keys: ["vivienda_precio_yoy_5a"],
    outs: [{ k: "precio", lab: "Precio mediano CCAA" }, { k: "cuota", lab: "Cuota mediana" }, { k: "esf", lab: "Esfuerzo cuota/renta" }, { k: "ipv", lab: "Precio vivienda a/a" }, { k: "sobre", lab: "Sobrecarga vivienda" }],
    headline: "esf",
    reds: [{ t: "Esfuerzo cuota/renta > 35 %", thr: 35.0, k: "esf", cmp: "gt", d: 1, x: "regla prudencial [regla]" }, { t: "Sobrecarga > 40 % renta", thr: 15.0, k: "sobre", cmp: "gt", d: 1, x: "definición Eurostat · muerde al flujo nuevo [UE]" }, { t: "IPV a/a > 10 %", thr: 10.0, k: "ipv", cmp: "gt", d: 1, x: "burbuja 2004-07 [hist]" }],
  },
  {
    id: "04",
    pill: "🚀 Emprendedor",
    foot: "🚀 emprendedor",
    h1: "🚀 ¿Aguanta el ciclo lo que tarda mi empresa en nacer?",
    meta: "eurostat_gdp_q_es.csv · eurostat_hicp_manr_es.csv · ecb_euribor12m.csv · eurostat_une_rt_m_es.csv · wb_self_employment.csv",
    hot: ["r", "ext", "pm", "sp"],
    series_keys: ["pib_yoy_5a"],
    outs: [{ k: "g", lab: "Ciclo · PIB real" }, { k: "u", lab: "Paro · talento" }, { k: "pi", lab: "IPCA · coste inputs" }, { k: "r", lab: "Euríbor · financiación" }, { k: "auton", lab: "Autoempleo" }],
    headline: "g",
    reds: [{ t: "PIB a/a < 0 %", thr: 0.0, k: "g", cmp: "lt", d: 1, x: "recesión técnica [regla]" }, { t: "IPCA > 4 % sostenido", thr: 4.0, k: "pi", cmp: "gt", d: 1, x: "episodio 2022: pico 10,7 % (jul-2022) [hist]" }, { t: "Euríbor 12m > 4 %", thr: 4.0, k: "r", cmp: "gt", d: 2, x: "techo del ciclo de subidas 2023 [hist]" }],
  },
  {
    id: "05",
    pill: "🏛️ Funcionario",
    foot: "🏛️ funcionario",
    h1: "🏛️ ¿Mi nómina real sobrevive al ajuste que viene?",
    meta: "gov_10a_exp.csv · eurostat_gov_deficit_es.csv · eurostat_gov_debt_es.csv · eurostat_hicp_manr_es.csv",
    hot: ["sp", "idx", "pm", "dem"],
    series_keys: ["deficit_pib_hist"],
    outs: [{ k: "d1", lab: "Masa salarial D1" }, { k: "nomreal", lab: "Poder de compra nómina" }, { k: "pi", lab: "IPCA · erosión" }, { k: "saldo", lab: "Saldo público" }, { k: "gtot", lab: "Gasto total AAPP" }],
    headline: "nomreal",
    reds: [{ t: "Déficit > 3 % PIB", thr: -3.0, k: "saldo", cmp: "lt", d: 1, x: "procedimiento de déficit excesivo [regla UE]" }, { t: "Deuda > 105 % PIB", thr: 105.0, k: "b", cmp: "gt", d: 1, x: "umbral narrativo, no legal [comentario]" }, { t: "Poder de compra < 100", thr: 100.0, k: "nomreal", cmp: "lt", d: 1, x: "congelaciones y recortes 2010-15 [hist]" }],
  },
  {
    id: "06",
    pill: "🗳️ Político",
    foot: "🗳️ político (decisor honesto)",
    h1: "🗳️ ¿Qué palanca puedo mover sin cruzar una línea roja?",
    meta: "eurostat_gov_debt_es · eurostat_gov_deficit_es · eurostat_une_rt_m_es · eurostat_gdp_q_es · interest_paid · gold_escenarios_deuda",
    hot: ["sp", "r", "tau", "z", "lam", "dem"],
    series_keys: ["deficit_pib_hist"],
    outs: [{ k: "b", lab: "Deuda pública" }, { k: "saldo", lab: "Saldo público" }, { k: "u", lab: "Paro total" }, { k: "g", lab: "PIB real" }, { k: "int", lab: "Intereses" }],
    headline: "b",
    reds: [{ t: "Deuda > 120 % PIB", thr: 120.0, k: "b", cmp: "gt", d: 1, x: "techo COVID 2020: 119,3 [hist]" }, { t: "Déficit > 3 % PIB", thr: -3.0, k: "saldo", cmp: "lt", d: 1, x: "regla fiscal UE [regla UE]" }, { t: "Paro > 15 %", thr: 15.0, k: "u", cmp: "gt", d: 1, x: "coste social del ajuste [hist]" }],
  },
  {
    id: "07",
    pill: "🕳️ Corrupto",
    foot: "🕳️ político corrupto · sátira de transparencia",
    h1: "🕳️ ¿Dónde no mira nadie? — las partidas con más discrecionalidad, señaladas para quien SÍ mira",
    meta: "gov_10a_exp.csv (P2 · D3 · P51G) · interest_paid.csv",
    hot: ["sp", "dem"],
    series_keys: ["inversion_publica_pib_hist"],
    outs: [{ k: "p2", lab: "Consumo intermedio P2" }, { k: "d3", lab: "Subvenciones D3" }, { k: "p51", lab: "Inversión pública P51G" }, { k: "gtot", lab: "Gasto total" }, { k: "int", lab: "Intereses D41" }],
    headline: "p51",
    reds: [{ t: "Contratos menores · adjudicación", thr: null, k: null, cmp: null, d: null, x: "la señal vive a nivel de contrato — sin serie pública [hueco de datos]" }, { t: "WGI control de la corrupción", thr: null, k: null, cmp: null, d: null, x: "API archivada: descarga manual en govindicators.org [hueco de datos]" }, { t: "Inversión pública < 2 % PIB", thr: 2.0, k: "p51", cmp: "lt", d: 2, x: "cruzada en 2016-17 (2,0): obra parada = renegociación [hist]" }],
  },
  {
    id: "08",
    pill: "🧒 Infancia",
    foot: "🧒 infancia",
    h1: "🧒 ¿Qué país hereda quien hoy tiene 8 años?",
    meta: "eurostat_arop_child_es · eurostat_gov_edu_es · eurostat_gov_debt_es · gold_projections · gold_escenarios_deuda",
    hot: ["sp", "dem", "z", "lam"],
    series_keys: ["arop_infantil_hist"],
    outs: [{ k: "arop", lab: "AROP infantil (<16)" }, { k: "edu", lab: "Gasto en educación" }, { k: "b", lab: "Deuda heredada" }, { k: "dep", lab: "Dependencia 65+" }, { k: "vida", lab: "Esperanza de vida" }],
    headline: "b",
    reds: [{ t: "AROP infantil > 25 %", thr: 25.0, k: "arop", cmp: "gt", d: 1, x: "peor cuartil UE — cruzada de forma persistente [UE]" }, { t: "Educación < 4,8 % PIB (UE27)", thr: 4.8, k: "edu", cmp: "lt", d: 2, x: "0,7 pp por debajo de la media UE27 [UE]" }, { t: "Dependencia > 50/100", thr: 50.0, k: "dep", cmp: "gt", d: 1, x: "sin precedente histórico [hist inédito]" }],
  },
  {
    id: "09",
    pill: "🌅 Jubilado",
    foot: "🌅 jubilado",
    h1: "🌅 ¿Mi pensión sigue al IPC — y quién la paga en 2035?",
    meta: "eurostat_pensions_pcgdp_es.csv · eurostat_hicp_manr_es.csv · gold_projections.csv · life_expectancy_e0.csv",
    hot: ["idx", "dem", "pm", "sp"],
    series_keys: ["hicp_es_5a"],
    outs: [{ k: "pens", lab: "Gasto en pensiones" }, { k: "nomreal", lab: "Poder de compra" }, { k: "pi", lab: "IPCA · la referencia" }, { k: "dep", lab: "Dependencia 65+" }, { k: "vida", lab: "Esperanza de vida" }],
    headline: "pens",
    reds: [{ t: "Gasto pensiones > 15 % PIB", thr: 15.0, k: "pens", cmp: "gt", d: 2, x: "nunca alcanzado en la serie [hist inédito]" }, { t: "Dependencia 65+ > 50/100", thr: 50.0, k: "dep", cmp: "gt", d: 1, x: "se cruza entre 2035 y 2050 [hist inédito]" }, { t: "Poder de compra < 100", thr: 100.0, k: "nomreal", cmp: "lt", d: 1, x: "la palanca ι es la que decide, no el IPC [regla]" }],
  },
  {
    id: "10",
    pill: "🎓 Joven",
    foot: "🎓 joven que entra al mercado laboral",
    h1: "🎓 ¿Primer contrato o cola del paro — y podré irme de casa?",
    meta: "eurostat_une_rt_m_es.csv · eurostat_temp_share_es.csv · eurostat_hpi_q_es.csv · eurostat_overburden_es.csv · ine_salarios.csv",
    hot: ["z", "tau", "ext", "r", "sp"],
    series_keys: ["paro_juvenil_5a", "paro_total_5a"],
    outs: [{ k: "ujuv", lab: "Paro juvenil <25" }, { k: "temp", lab: "Temporalidad" }, { k: "ipv", lab: "Precio vivienda a/a" }, { k: "sobre", lab: "Sobrecarga vivienda" }, { k: "salario", lab: "Salario medio" }],
    headline: "ujuv",
    reds: [{ t: "Paro juvenil > 40 %", thr: 40.0, k: "ujuv", cmp: "gt", d: 1, x: "cota del ciclo anterior; 2013 la superó [hist]" }, { t: "Temporalidad > 25 %", thr: 25.0, k: "temp", cmp: "gt", d: 1, x: "la serie vivió sobre ese nivel hasta 2022-Q1 [hist]" }, { t: "IPV > +10 % a/a", thr: 10.0, k: "ipv", cmp: "gt", d: 1, x: "cinco trimestres seguidos >10 % en la serie [hist]" }],
  },
  {
    id: "11",
    pill: "📋 Indefinido",
    foot: "📋 trabajador indefinido",
    h1: "📋 ¿Crece mi salario por encima del IPC?",
    meta: "ine_salarios.csv · eurostat_hicp_manr_es.csv · eurostat_une_rt_m_es.csv · eurostat_temp_share_es.csv · eurostat_gdp_q_es.csv",
    hot: ["lam", "z", "pm", "tau"],
    series_keys: ["hicp_es_5a"],
    outs: [{ k: "wrealIdx", lab: "Salario real acumulado" }, { k: "salario", lab: "Salario medio" }, { k: "pi", lab: "IPCA · el listón" }, { k: "u", lab: "Paro total" }, { k: "temp", lab: "Temporalidad" }],
    headline: "wrealIdx",
    reds: [{ t: "IPCA > 4 % sostenido", thr: 4.0, k: "pi", cmp: "gt", d: 1, x: "cruzado en 2022-23: el salario real cayó [hist]" }, { t: "Paro > 15 %", thr: 15.0, k: "u", cmp: "gt", d: 1, x: "por encima, el poder de negociación se hunde [hist]" }, { t: "Salario real < 100", thr: 100.0, k: "wrealIdx", cmp: "lt", d: 1, x: "pérdida acumulada desde 2026 [aritmética]" }],
  },
  {
    id: "12",
    pill: "🧾 Autónomo",
    foot: "🧾 autónomo",
    h1: "🧾 ¿Caja, cuota y ciclo — en qué orden me golpean?",
    meta: "wb_self_employment.csv · eurostat_gdp_q_es.csv · eurostat_hicp_manr_es.csv · ecb_euribor12m.csv · eurostat_une_rt_m_es.csv",
    hot: ["r", "pm", "ext", "sp"],
    series_keys: ["autoempleo_hist"],
    outs: [{ k: "auton", lab: "Autoempleo" }, { k: "g", lab: "Ciclo · demanda" }, { k: "pi", lab: "IPCA · coste inputs" }, { k: "r", lab: "Euríbor · póliza" }, { k: "u", lab: "Paro · repliegue" }],
    headline: "g",
    reds: [{ t: "PIB a/a < 0 %", thr: 0.0, k: "g", cmp: "lt", d: 1, x: "recesión técnica [regla]" }, { t: "IPCA > 4 % sostenido", thr: 4.0, k: "pi", cmp: "gt", d: 1, x: "episodio 2022: pico 10,7 % [hist]" }, { t: "Euríbor 12m > 4 %", thr: 4.0, k: "r", cmp: "gt", d: 2, x: "techo del ciclo de subidas 2023 [hist]" }],
  },
];

/** Historical series — REAL first/last points from the live payload, truncated for test size. */
export const mockSeries = {
  bono10y_es_5a: { fuente: "ecb_bono10y_es.csv", puntos: [["2021-07", 0.331], ["2021-08", 0.214], ["2021-09", 0.327], ["2026-04", 3.448], ["2026-05", 3.488], ["2026-06", 3.417]] },
  euribor12m_5a: { fuente: "ecb_euribor12m.csv", puntos: [["2021-07", -0.491], ["2021-08", -0.498], ["2021-09", -0.492], ["2026-04", 2.747], ["2026-05", 2.804], ["2026-06", 2.798]] },
  vivienda_precio_yoy_5a: { fuente: "eurostat_hpi_q_es.csv", puntos: [["2020-Q2", 2.2], ["2020-Q3", 1.8], ["2020-Q4", 1.7], ["2025-Q3", 12.8], ["2025-Q4", 12.9], ["2026-Q1", 12.8]] },
  deficit_pib_hist: { fuente: "eurostat_gov_deficit_es.csv", puntos: [["1995.0", -6.8], ["1996.0", -5.9], ["1997.0", -3.9], ["2023.0", -3.3], ["2024.0", -3.2], ["2025.0", -2.4]] },
} as const;

export const mockKpis = {
  euribor12m: { valor: 2.8, fuente: "ecb_euribor12m.csv", periodo: "2026-06" },
  spread_es_de: { valor: 45, fuente: "ecb_bono10y_es.csv · ecb_bono10y_de.csv", periodo: "2026-06" },
  paro_total: { valor: 10.1, periodo: "2026-06" },
  hicp_es: { valor: 3.0, periodo: "2025-12" },
  pib_yoy: { valor: 2.7, periodo: "2026-Q2" },
} as const;

/** Fixture montecarlo_seed42 pins at 2030/2050/2070; linear in between (display-only mock). */
export function mockPercentiles(years: number[]) {
  const pins: Record<string, Record<number, number>> = {
    p5: { 2026: 106.3, 2030: 107.2674, 2050: 176.4991, 2070: 271.9047 },
    p25: { 2026: 106.3, 2030: 110.7682, 2050: 206.8693, 2070: 347.1841 },
    p50: { 2026: 106.3, 2030: 113.3, 2050: 231.2999, 2070: 408.8999 },
    p75: { 2026: 106.3, 2030: 116.0439, 2050: 258.6826, 2070: 483.7138 },
    p95: { 2026: 106.3, 2030: 119.7131, 2050: 303.8985, 2070: 619.477 },
  };
  const interp = (pin: Record<number, number>, y: number): number => {
    const ys = Object.keys(pin).map(Number).sort((a, b) => a - b);
    if (y <= ys[0]) return pin[ys[0]];
    if (y >= ys[ys.length - 1]) return pin[ys[ys.length - 1]];
    const hi = ys.find((p) => p >= y)!;
    const lo = ys[ys.indexOf(hi) - 1];
    return pin[lo] + ((pin[hi] - pin[lo]) * (y - lo)) / (hi - lo);
  };
  return Object.fromEntries(
    (["p5", "p25", "p50", "p75", "p95"] as const).map((p) => [p, years.map((y) => interp(pins[p], y))]),
  ) as Record<"p5" | "p25" | "p50" | "p75" | "p95", number[]>;
}
