import type { AnySeriesKey } from "../engine/derived";
import type { Levers } from "../engine/levers";

type LeverKey = keyof Levers;

/** A question a reader can actually ask, bound to what answers it.
 *
 *  The binding is the point. A free-text box over a scenario engine invites
 *  questions the engine cannot answer, and answering them anyway is how a
 *  tool starts inventing. Each question here names the series that answers it,
 *  so the reply is a number the engine computed rather than prose about it. */
export interface PersonaQuestion {
  id: string;
  /** What the reader sees, phrased the way they would ask it. */
  text: string;
  /** The series whose value is the answer. */
  series: AnySeriesKey;
  /** A second series worth seeing next to it, when one number is misleading
   *  on its own — a price means little without the payment it implies. */
  companion?: AnySeriesKey;
  /** One sentence naming the mechanism, in the engine's own terms. */
  mechanism: string;
  /** Levers the reader is most likely to want to move for this question.
   *  Ranked offline from sensitivity_matrix rather than guessed. */
  levers: LeverKey[];
  /** Concept to look up in the corpus, when it is reachable. */
  concept?: string;
  /** Questions to offer next — ids in the same set. */
  followUps: string[];
}

/** 03 · quien quiere comprar vivienda. */
export const Q03: PersonaQuestion[] = [
  {
    id: "precio",
    text: "¿Cuánto costará una vivienda media?",
    series: "precio",
    companion: "cuota",
    mechanism:
      "El precio revierte hacia su crecimiento de largo plazo (IPV_LR) desde el " +
      "dato de partida, corregido por el tipo de interés y por la desviación del PIB.",
    levers: ["r", "lam"],
    concept: "determinantes del precio de la vivienda",
    followUps: ["esfuerzo", "cuota", "euribor"],
  },
  {
    id: "cuota",
    text: "¿Cuánto pagaré de hipoteca al mes?",
    series: "cuota",
    companion: "salmes",
    mechanism:
      "Cuota francesa a 25 años sobre el 80 % del precio, al Euríbor más el " +
      "diferencial hipotecario estimado (DIFF).",
    levers: ["r", "lam"],
    concept: "esfuerzo hipotecario de los hogares",
    followUps: ["esfuerzo", "precio", "euribor"],
  },
  {
    id: "esfuerzo",
    text: "¿Qué parte de mi sueldo se irá en la hipoteca?",
    series: "esf",
    companion: "salmes",
    mechanism:
      "Cuota sobre salario mensual. El numerador lo mueve el tipo; el " +
      "denominador, la curva de salarios (π + λ + φ·holgura).",
    levers: ["r", "lam", "z"],
    concept: "regla del 35 % de esfuerzo hipotecario",
    followUps: ["euribor", "salarios", "precio"],
  },
  {
    id: "euribor",
    text: "¿Y si el Euríbor sube al 4,8 %?",
    series: "esf",
    companion: "cuota",
    mechanism:
      "El tipo entra dos veces y en sentidos opuestos: encarece la cuota y " +
      "abarata el precio (E_IPV_R). El efecto neto sobre el esfuerzo es la suma.",
    levers: ["r"],
    concept: "transmisión de la política monetaria a la vivienda",
    followUps: ["esfuerzo", "cuota", "precio"],
  },
  {
    id: "salarios",
    text: "¿Mejora si los salarios crecen más rápido?",
    series: "esf",
    companion: "salmes",
    mechanism:
      "λ desplaza la curva de salarios y con ella el denominador del esfuerzo; " +
      "no toca la cuota, que depende del tipo y del precio.",
    levers: ["lam", "z"],
    concept: "crecimiento de los salarios reales",
    followUps: ["esfuerzo", "cuota"],
  },
];

/** 01 · quien presta al Estado. */
export const Q01: PersonaQuestion[] = [
  {
    id: "cupon",
    text: "¿Qué cupón me tendrá que pagar el bono a 10 años?",
    series: "bono",
    companion: "spread",
    mechanism:
      "Euríbor más la prima temporal (TERM) más el spread soberano. Si la " +
      "realimentación de deuda está activa, el spread se ensancha solo cuando " +
      "la deuda supera el umbral B_CRIT.",
    levers: ["r", "prima"],
    concept: "determinantes de la prima de riesgo soberana",
    followUps: ["deuda", "intereses", "adverso"],
  },
  {
    id: "deuda",
    text: "¿Hasta dónde llega la deuda pública?",
    series: "b",
    companion: "int",
    mechanism:
      "Identidad de la deuda: b crece con (1+i)/(1+g) y baja con el saldo " +
      "primario. Cuando el tipo efectivo supera al crecimiento nominal, la bola " +
      "de nieve empuja sola.",
    levers: ["sp", "r", "prima"],
    concept: "sostenibilidad de la deuda pública r menos g",
    followUps: ["intereses", "cupon", "adverso"],
  },
  {
    id: "intereses",
    text: "¿Cuánto del presupuesto se va sólo en intereses?",
    series: "int",
    companion: "saldo",
    mechanism:
      "Sobre el stock del año anterior al tipo efectivo, que se acerca al bono " +
      "de mercado al ritmo de refinanciación (REFI, 14 % al año).",
    levers: ["r", "prima", "sp"],
    concept: "carga de intereses de la deuda pública",
    followUps: ["deuda", "cupon"],
  },
  {
    id: "adverso",
    text: "¿Y si la prima de riesgo se dispara?",
    series: "b",
    companion: "bono",
    mechanism:
      "La prima entra en el cupón, el cupón en el tipo efectivo vía " +
      "refinanciación, y el tipo efectivo en la identidad de la deuda. El " +
      "efecto tarda años en verse entero: sólo se refinancia el 14 % anual.",
    levers: ["prima", "r"],
    concept: "episodios de tensión en la deuda soberana",
    followUps: ["deuda", "intereses", "cupon"],
  },
];

/** 02 · quien presta a los hogares. */
export const Q02: PersonaQuestion[] = [
  {
    id: "esfuerzo",
    text: "¿Qué esfuerzo soportan los hogares con hipoteca?",
    series: "esf",
    companion: "cuota",
    mechanism:
      "Cuota sobre nómina. El tipo mueve el numerador y la curva de salarios " +
      "el denominador; por encima del 35 % la regla prudencial se considera rota.",
    levers: ["r", "lam"],
    concept: "esfuerzo hipotecario y capacidad de pago",
    followUps: ["mora", "colateral"],
  },
  {
    id: "mora",
    text: "¿Cuánto riesgo de impago hay en la cartera?",
    series: "u",
    companion: "esf",
    mechanism:
      "El paro es la variable que el motor sí proyecta: sale de Okun sobre la " +
      "desviación del PIB. La mora bancaria en sí no está en el corte de datos.",
    levers: ["z", "lam", "sp"],
    concept: "determinantes de la morosidad hipotecaria",
    followUps: ["esfuerzo", "colateral"],
  },
  {
    id: "colateral",
    text: "¿Qué pasa con el valor de la garantía?",
    series: "ipv",
    companion: "precio",
    mechanism:
      "El IPV revierte hacia su crecimiento de largo plazo estimado, corregido " +
      "por el tipo y por la desviación del PIB. Marca el LTV efectivo y la " +
      "severidad si hay impago.",
    levers: ["r", "lam"],
    concept: "precio de la vivienda como colateral bancario",
    followUps: ["esfuerzo", "mora"],
  },
];

/** 04 · quien monta una empresa. */
export const Q04: PersonaQuestion[] = [
  {
    id: "crecimiento",
    text: "¿Cómo va a crecer la economía?",
    series: "g",
    companion: "u",
    mechanism:
      "El nivel del PIB se desvía de la base según el multiplicador fiscal y " +
      "la demanda externa, con persistencia RHO. El crecimiento es la " +
      "diferencia de ese nivel año a año.",
    levers: ["ext", "sp", "lam"],
    concept: "determinantes del crecimiento del PIB",
    followUps: ["financiacion", "costes", "demanda"],
  },
  {
    id: "financiacion",
    text: "¿Cuánto me costará financiarme?",
    series: "r",
    companion: "g",
    mechanism:
      "El tipo de referencia es una palanca, no un resultado: el motor no " +
      "modela al BCE. Lo que sí modela es su efecto sobre inversión y consumo " +
      "vía E_R.",
    levers: ["r"],
    concept: "coste de capital e inversión empresarial",
    followUps: ["crecimiento", "costes"],
  },
  {
    id: "costes",
    text: "¿Cuánto me subirán los costes?",
    series: "pi",
    companion: "g",
    mechanism:
      "Phillips: inercia de expectativas más holgura más el traspaso de " +
      "precios importados (GAMMA), que decae geométricamente año a año.",
    levers: ["pm", "lam"],
    concept: "traspaso de precios de importación a la inflación",
    followUps: ["crecimiento", "demanda"],
  },
  {
    id: "demanda",
    text: "¿Y si se hunde la demanda externa?",
    series: "g",
    companion: "u",
    mechanism:
      "Y* entra en el shock de demanda con peso E_EXT y arrastra el nivel del " +
      "PIB; Okun lo convierte en paro con un retardo.",
    levers: ["ext"],
    concept: "demanda externa y ciclo económico",
    followUps: ["crecimiento", "costes"],
  },
];

/** 05 · quien cobra del presupuesto. */
export const Q05: PersonaQuestion[] = [
  {
    id: "poder",
    text: "¿Voy a perder poder adquisitivo?",
    series: "nomreal",
    companion: "pi",
    mechanism:
      "Índice base 100 en 2026: la nómina se revaloriza según la palanca de " +
      "indexación y se descuenta la inflación proyectada. Por debajo de 100 se " +
      "pierde poder de compra.",
    levers: ["idx", "pm"],
    concept: "indexación salarial e inflación",
    followUps: ["masa", "saldo"],
  },
  {
    id: "masa",
    text: "¿Habrá recortes en el empleo público?",
    series: "d1",
    companion: "saldo",
    mechanism:
      "La masa salarial pública en % del PIB se mueve con la consolidación " +
      "fiscal y con el denominador: crecer más rebaja la ratio sin tocar la nómina.",
    levers: ["sp", "lam"],
    concept: "consolidación fiscal y gasto en personal",
    followUps: ["poder", "saldo"],
  },
  {
    id: "saldo",
    text: "¿Cómo está la caja del Estado?",
    series: "saldo",
    companion: "b",
    mechanism:
      "Saldo primario menos intereses. Es lo que queda después de pagar la " +
      "deuda heredada, y la parte que el presupuesto no elige.",
    levers: ["sp", "r", "dem"],
    concept: "saldo público y espacio fiscal",
    followUps: ["masa", "poder"],
  },
];

/** 06 · quien decide. */
export const Q06: PersonaQuestion[] = [
  {
    id: "deuda",
    text: "¿Qué pasa con la deuda si no hago nada?",
    series: "b",
    companion: "int",
    mechanism:
      "Con las palancas en su valor observado, la senda la marca la identidad " +
      "de la deuda y la presión demográfica. No hacer nada también es un escenario.",
    levers: ["sp", "r", "dem"],
    concept: "sostenibilidad fiscal a largo plazo",
    followUps: ["coste", "espacio", "consolidar"],
  },
  {
    id: "consolidar",
    text: "¿Qué me cuesta consolidar?",
    series: "u",
    companion: "b",
    mechanism:
      "Subir el saldo primario baja la deuda, pero pasa por el multiplicador " +
      "(1,40) al nivel del PIB y de ahí a Okun. El paro es la factura.",
    levers: ["sp"],
    concept: "multiplicador fiscal y coste del ajuste",
    followUps: ["deuda", "coste", "espacio"],
  },
  {
    id: "espacio",
    text: "¿Cuánto espacio fiscal me queda?",
    series: "int",
    companion: "saldo",
    mechanism:
      "Los intereses son gasto que nadie elige: salen del stock heredado y del " +
      "tipo efectivo. Cuanto mayores, menor la parte del presupuesto que se decide.",
    levers: ["r", "prima", "sp"],
    concept: "espacio fiscal y carga de intereses",
    followUps: ["deuda", "consolidar"],
  },
  {
    id: "coste",
    text: "¿Y el paro, cómo queda?",
    series: "u",
    companion: "g",
    mechanism:
      "Okun sobre la desviación del nivel del PIB, más los desplazamientos del " +
      "paro estructural por instituciones, cuña fiscal y productividad.",
    levers: ["sp", "z", "lam"],
    concept: "ley de Okun y desempleo",
    followUps: ["consolidar", "deuda"],
  },
];

/** 07 · dónde va el dinero discrecional. */
export const Q07: PersonaQuestion[] = [
  {
    id: "inversion",
    text: "¿Cuánta inversión pública se va a licitar?",
    series: "p51",
    companion: "saldo",
    mechanism:
      "La inversión (P51G) es la partida que primero absorbe el ajuste: se " +
      "recorta antes que la nómina o las transferencias porque no tiene quien " +
      "la defienda.",
    levers: ["sp", "dem"],
    concept: "inversión pública y contratación",
    followUps: ["intermedio", "subvenciones"],
  },
  {
    id: "intermedio",
    text: "¿Cuánto se gasta en consumo intermedio?",
    series: "p2",
    companion: "p51",
    mechanism:
      "P2 recoge compras corrientes de bienes y servicios: la partida con más " +
      "discrecionalidad por contrato y la menos visible en el agregado.",
    levers: ["sp"],
    concept: "consumo intermedio y contratación pública",
    followUps: ["inversion", "subvenciones"],
  },
  {
    id: "subvenciones",
    text: "¿Y las subvenciones?",
    series: "d3",
    companion: "saldo",
    mechanism:
      "D3 son transferencias sin contrapartida directa. El motor las proyecta " +
      "como cuota del PIB; quién las recibe no está en ningún CSV de este corte.",
    levers: ["sp", "dem"],
    concept: "subvenciones y transferencias públicas",
    followUps: ["inversion", "intermedio"],
  },
];

/** 08 · quien hereda el resultado. */
export const Q08: PersonaQuestion[] = [
  {
    id: "pobreza",
    text: "¿Cuántos niños seguirán en riesgo de pobreza?",
    series: "arop",
    companion: "u",
    mechanism:
      "El AROP infantil sigue a la renta familiar, y la renta familiar al " +
      "empleo. La línea roja de presentación está en el 30 %.",
    levers: ["z", "lam", "sp"],
    concept: "pobreza infantil y empleo de los hogares",
    followUps: ["educacion", "herencia"],
  },
  {
    id: "educacion",
    text: "¿Cuánto se invertirá en su educación?",
    series: "edu",
    companion: "saldo",
    mechanism:
      "El gasto educativo en % del PIB compite con el resto del presupuesto " +
      "bajo la misma restricción, y el envejecimiento empuja el gasto hacia " +
      "el otro extremo de la pirámide.",
    levers: ["sp", "dem"],
    concept: "gasto público en educación",
    followUps: ["pobreza", "herencia"],
  },
  {
    id: "herencia",
    text: "¿Qué deuda van a heredar?",
    series: "b",
    companion: "dep",
    mechanism:
      "La deuda de 2050 la pagan quienes hoy tienen menos de 16 años, con una " +
      "tasa de dependencia que para entonces casi se duplica respecto a 2026.",
    levers: ["sp", "dem", "r"],
    concept: "equidad intergeneracional y deuda",
    followUps: ["pobreza", "educacion"],
  },
];

/** 09 · quien cobra pensión. */
export const Q09: PersonaQuestion[] = [
  {
    id: "poder",
    text: "¿Me va a alcanzar la pensión?",
    series: "nomreal",
    companion: "pi",
    mechanism:
      "Índice base 100 en 2026: revalorización según la palanca de indexación " +
      "menos inflación. Por debajo de 100, la pensión compra menos que hoy.",
    levers: ["idx", "pm"],
    concept: "revalorización de las pensiones e inflación",
    followUps: ["gasto", "demografia"],
  },
  {
    id: "gasto",
    text: "¿Cuánto costará pagar las pensiones?",
    series: "pens",
    companion: "dep",
    mechanism:
      "El gasto en pensiones sobre PIB sube con la presión demográfica del " +
      "escenario y con la indexación elegida; son dos palancas distintas.",
    levers: ["dem", "idx"],
    concept: "gasto en pensiones y envejecimiento",
    followUps: ["demografia", "poder"],
  },
  {
    id: "demografia",
    text: "¿Cuántos cotizantes quedarán por pensionista?",
    series: "dep",
    companion: "pens",
    mechanism:
      "Tasa de dependencia de mayores de 65 sobre población en edad de " +
      "trabajar, de la proyección EUROPOP de Eurostat. Es dato proyectado, no " +
      "una palanca del motor.",
    levers: ["dem"],
    concept: "tasa de dependencia demográfica",
    followUps: ["gasto", "poder"],
  },
];

/** 10 · quien empieza. */
export const Q10: PersonaQuestion[] = [
  {
    id: "paro",
    text: "¿Voy a encontrar trabajo?",
    series: "ujuv",
    companion: "u",
    mechanism:
      "El paro juvenil se proyecta como múltiplo estable del paro total " +
      "(RJUV = 2,3 en la serie de los últimos cinco años). Sube y baja con él.",
    levers: ["z", "tau", "lam"],
    concept: "desempleo juvenil en España",
    followUps: ["temporal", "vivienda"],
  },
  {
    id: "temporal",
    text: "¿Será un contrato temporal?",
    series: "temp",
    companion: "ujuv",
    mechanism:
      "La temporalidad responde a la cuña fiscal y a las instituciones " +
      "laborales, las dos palancas que desplazan el paro estructural.",
    levers: ["tau", "z"],
    concept: "temporalidad y dualidad del mercado laboral",
    followUps: ["paro", "vivienda"],
  },
  {
    id: "vivienda",
    text: "¿Podré independizarme?",
    series: "sobre",
    companion: "salario",
    mechanism:
      "La sobrecarga por coste de vivienda cruza precio y salario: la vivienda " +
      "sube con el IPV estimado y el salario con la curva de salarios.",
    levers: ["r", "lam"],
    concept: "emancipación juvenil y coste de la vivienda",
    followUps: ["paro", "temporal"],
  },
];

/** 11 · quien ya tiene contrato fijo. */
export const Q11: PersonaQuestion[] = [
  {
    id: "real",
    text: "¿Subirá mi sueldo más que los precios?",
    series: "wrealIdx",
    companion: "pi",
    mechanism:
      "Salario nominal (inflación + productividad + PHI·holgura) menos " +
      "inflación, acumulado desde 2026 en base 100. Lo que decide es λ, no π.",
    levers: ["lam", "pm"],
    concept: "salarios reales y productividad",
    followUps: ["salario", "empleo"],
  },
  {
    id: "salario",
    text: "¿Cuánto llegaré a ganar?",
    series: "salario",
    companion: "wrealIdx",
    mechanism:
      "Salario medio anual acumulando la revalorización nominal año a año " +
      "desde el dato de partida del vintage.",
    levers: ["lam", "pm"],
    concept: "evolución del salario medio",
    followUps: ["real", "empleo"],
  },
  {
    id: "empleo",
    text: "¿Peligra mi empleo?",
    series: "u",
    companion: "g",
    mechanism:
      "Okun sobre la desviación del PIB más los desplazamientos del paro " +
      "estructural por instituciones, cuña fiscal y productividad.",
    levers: ["z", "lam", "sp"],
    concept: "determinantes del desempleo",
    followUps: ["real", "salario"],
  },
];

/** 12 · quien trabaja por cuenta propia. */
export const Q12: PersonaQuestion[] = [
  {
    id: "actividad",
    text: "¿Cómo irá la actividad?",
    series: "g",
    companion: "auton",
    mechanism:
      "El nivel del PIB responde al multiplicador fiscal y a la demanda " +
      "externa con persistencia; el crecimiento es su variación anual.",
    levers: ["ext", "sp"],
    concept: "ciclo económico y trabajo autónomo",
    followUps: ["costes", "cuota", "financiacion"],
  },
  {
    id: "costes",
    text: "¿Cuánto me subirán los costes?",
    series: "pi",
    companion: "g",
    mechanism:
      "Phillips con traspaso de precios importados: el shock de insumos entra " +
      "con peso GAMMA y decae geométricamente año a año.",
    levers: ["pm"],
    concept: "costes de insumos e inflación",
    followUps: ["actividad", "financiacion"],
  },
  {
    id: "financiacion",
    text: "¿Cuánto me costará financiarme?",
    series: "r",
    companion: "pi",
    mechanism:
      "El tipo de referencia es una palanca del escenario, no un resultado: " +
      "el motor no modela la decisión del BCE, sólo sus efectos.",
    levers: ["r"],
    concept: "acceso a financiación de autónomos",
    followUps: ["actividad", "costes"],
  },
  {
    id: "cuota",
    text: "¿Habrá más o menos autónomos?",
    series: "auton",
    companion: "u",
    mechanism:
      "La cuota de autoempleo sobre el empleo total se mueve con el ciclo: " +
      "parte es emprendimiento y parte es refugio cuando falta el empleo por " +
      "cuenta ajena, y el motor no las separa.",
    levers: ["ext", "z", "tau"],
    concept: "autoempleo y mercado laboral",
    followUps: ["actividad", "costes"],
  },
];

export const PERSONA_QUESTIONS: Record<string, PersonaQuestion[]> = {
  "01": Q01, "02": Q02, "03": Q03, "04": Q04, "05": Q05, "06": Q06,
  "07": Q07, "08": Q08, "09": Q09, "10": Q10, "11": Q11, "12": Q12,
};

export const questionsFor = (id: string): PersonaQuestion[] =>
  PERSONA_QUESTIONS[id] ?? [];

/** Lowercase and strip diacritics: Spanish is routinely typed unaccented. */
export const norm = (s: string): string =>
  s.trim().toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "");

/** Words that carry no topic. Matching on these is worse than not matching:
 *  «cuando» appears in a mechanism sentence about spread feedback, so a
 *  question about unemployment scored a hit on the bond-coupon question and
 *  answered it. A wrong answer that looks confident beats no answer only for
 *  whoever is measuring engagement. */
const STOPWORDS = new Set([
  "que", "qué", "como", "cuando", "cuanto", "cuanta", "cuantos", "cuantas",
  "donde", "quien", "cual", "cuales", "por", "para", "con", "sin", "del",
  "las", "los", "una", "uno", "unos", "unas", "the", "esta", "este", "esto",
  "estos", "estas", "ese", "esa", "eso", "mas", "menos", "muy", "hay",
  "ser", "soy", "son", "sera", "seran", "tiene", "tengo", "voy", "vas",
  "pasa", "pasara", "sale", "saldra", "queda", "quedara", "sigue", "año",
  "anos", "años", "ano", "pero", "and", "yo", "mi", "me", "te", "se", "lo",
  "la", "el", "en", "de", "al", "un", "es", "si", "no", "ya", "hasta",
]);

const content = (s: string): string[] =>
  norm(s).split(/[^a-z0-9ñ]+/).filter((w) => w.length > 2 && !STOPWORDS.has(w));

/** Resolve free text to a bound question, or null when nothing fits.
 *
 *  The question's own wording counts for most, the concept next, the mechanism
 *  least — the mechanism is engine prose and shares vocabulary with every other
 *  question in the set, so letting it decide picks whichever question happens
 *  to be first. A single weak hit is not enough to answer on. */
export function matchQuestion(
  text: string,
  questions: PersonaQuestion[],
): PersonaQuestion | null {
  const words = content(text);
  if (!words.length) return null;

  let best: { q: PersonaQuestion; score: number } | null = null;
  for (const q of questions) {
    const inText = new Set(content(q.text));
    const inConcept = new Set(content(q.concept ?? ""));
    const inMech = new Set(content(q.mechanism));
    let score = 0;
    for (const w of words) {
      if (inText.has(w)) score += 3;
      else if (inConcept.has(w)) score += 2;
      else if (inMech.has(w)) score += 1;
    }
    if (score > (best?.score ?? 0)) best = { q, score };
  }
  // 3 = one solid hit on the question's own wording, or a concept hit plus a
  // mechanism one. Below that the match is coincidence.
  return best && best.score >= 3 ? best.q : null;
}
