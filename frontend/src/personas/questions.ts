import type { AnySeriesKey } from "../engine/derived";
import type { Levers } from "../engine/levers";

type LeverKey = keyof Levers;

/** The year a persona question is answered at when the reader has not picked
 *  one themselves.
 *
 *  Y0 is the untouched baseline: every delta is zero there, so a question
 *  answered at Y0 returns today's value and reads as a feature that does not
 *  work. 2035 is far enough out that the mechanism has run and near enough
 *  that the reader can still picture it. Series pinned to the end of the
 *  projection (the debt) report 2050 regardless. */
export const ANSWER_YEAR = 2035;

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
  /** One sentence naming the mechanism, in the engine's own terms. Kept for a
   *  reviewer; the page folds it into «Detalle técnico». */
  mechanism: string;
  /** The same mechanism for a reader with no economics: no constant names,
   *  no formulas, each checked against the engine code. Shown first. */
  plain: string;
  /** Levers the reader is most likely to want to move for this question.
   *  Ranked offline from sensitivity_matrix rather than guessed. */
  levers: LeverKey[];
  /** Concept to look up in the corpus, when it is reachable. */
  concept?: string;
  /** Other words a reader may use for the same thing, weighted like the title.
   *  «rendimiento» is the ordinary Spanish for a bond yield and appears in no
   *  question text; without it, the most natural phrasing of the question the
   *  set does answer gets refused. */
  synonyms?: string[];
  /** El supuesto que la pregunta enuncia, cuando enuncia uno concreto.
   *
   *  «¿Y si el Euríbor sube al 4,8 %?» nombra un valor y la aplicación
   *  respondía con el Euríbor en su base: el titular decía 49,1 % —el caso
   *  base— debajo de una pregunta sobre una subida. Una pregunta que no
   *  aplica su propia premisa no es un escenario, es un titular.
   *
   *  Sólo lo llevan las preguntas que citan una cifra. Las cualitativas
   *  —«¿y si se dispara la prima?»— no traen supuesto porque elegir el valor
   *  por el lector seria inventarle la premisa.
   */
  apply?: Partial<Levers>;
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
    plain:
      "La subida anual del precio parte del fuerte ritmo de hoy y se acerca poco " +
      "a poco a su media histórica, en torno al 1,2 %. Un Euríbor más alto la " +
      "frena sobre todo los primeros años, y lo que el piso deja de subir ya no " +
      "lo recupera. Más productividad hace crecer más la economía y acelera la " +
      "subida.",
    levers: ["r", "lam"],
    concept: "determinantes del precio de la vivienda",
    synonyms: ["piso", "casa", "inmueble", "vivienda", "precio del metro"],
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
    plain:
      "Es la cuota de quien firma ese año un préstamo por el 80 % del precio de " +
      "la vivienda, al Euríbor más un margen fijo del banco. Un Euríbor más alto " +
      "la sube, aunque abarate algo el piso. También sube con el precio, que " +
      "crece más deprisa si hay más productividad.",
    levers: ["r", "lam"],
    concept: "esfuerzo hipotecario de los hogares",
    synonyms: ["hipoteca", "mensualidad", "letra", "pago mensual"],
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
    plain:
      "El esfuerzo empeora al principio porque la vivienda sube mucho más deprisa " +
      "que los sueldos, y mejora cuando el precio se modera. Un Euríbor más alto " +
      "lo sube. Más productividad apenas lo cambia: acelera los sueldos, pero " +
      "algo más el precio del piso. Las instituciones laborales no lo mueven.",
    levers: ["r", "lam", "z"],
    concept: "regla del 35 % de esfuerzo hipotecario",
    synonyms: ["esfuerzo", "porcentaje del sueldo", "parte del salario"],
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
    plain:
      "El Euríbor actúa por dos lados: sube el interés de la hipoteca y encarece " +
      "la cuota, pero frena el precio de la vivienda y eso la abarata un poco. " +
      "Pesa más lo primero. Además enfría la economía y frena los sueldos, así " +
      "que el esfuerzo sube.",
    levers: ["r"],
    apply: { r: 4.8 },
    concept: "transmisión de la política monetaria a la vivienda",
    synonyms: ["euribor", "subida de tipos", "bce"],
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
    plain:
      "En el motor los sueldos crecen con la inflación y la productividad. Pero " +
      "más productividad también acelera la economía y, con ella, el precio de la " +
      "vivienda, que gana algo más de ritmo que el sueldo: el esfuerzo no mejora, " +
      "incluso empeora un poco. Las instituciones laborales no mueven el sueldo.",
    levers: ["lam", "z"],
    concept: "crecimiento de los salarios reales",
    synonyms: ["sueldo", "nomina", "salario"],
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
    plain:
      "Sólo lo mueven el Euríbor y la prima de riesgo, punto por punto: si " +
      "cualquiera de los dos sube un punto (en la prima, 100 puntos básicos), el " +
      "cupón sube un punto. En el motor es el mismo todos los años y no se " +
      "encarece aunque crezca la deuda: la prima es un supuesto que se fija con " +
      "su palanca.",
    levers: ["r", "prima"],
    concept: "determinantes de la prima de riesgo soberana",
    synonyms: ["rendimiento", "rentabilidad", "yield", "tir", "tipo del bono", "interes del bono"],
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
    plain:
      "Cada año la deuda crece con sus intereses y pesa menos cuanto más crece la " +
      "economía, precios incluidos; el saldo primario la baja si hay superávit y " +
      "la sube si hay déficit. Un Euríbor o una prima más altos encarecen los " +
      "intereses poco a poco, y si el interés supera al crecimiento, sube aunque " +
      "ese saldo esté en cero.",
    levers: ["sp", "r", "prima"],
    concept: "sostenibilidad de la deuda pública r menos g",
    synonyms: ["endeudamiento", "pasivo", "ratio de deuda", "bola de nieve"],
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
    plain:
      "Se calculan con el interés medio que paga el Estado sobre la deuda del año " +
      "anterior. Si el Euríbor o la prima suben, ese interés medio recoge la " +
      "subida poco a poco, porque cada año sólo se renueva en torno al 14 % de la " +
      "deuda. Recortar el déficit del Estado deja, con los años, menos deuda y " +
      "menos intereses.",
    levers: ["r", "prima", "sp"],
    concept: "carga de intereses de la deuda pública",
    synonyms: ["coste de la deuda", "servicio de la deuda", "pago de intereses"],
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
    plain:
      "Una prima más alta encarece enseguida el bono nuevo, pero la deuda ya " +
      "emitida conserva su interés y sólo se renueva en torno al 14 % al año, así " +
      "que el coste medio sube despacio. Esos intereses de más se suman a la " +
      "deuda año tras año. En el motor la prima no frena la economía: actúa sólo " +
      "por esta vía.",
    levers: ["prima", "r"],
    concept: "episodios de tensión en la deuda soberana",
    synonyms: ["spread", "rescate", "tension financiera", "crisis de deuda"],
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
    plain:
      "Un Euríbor más alto encarece la cuota al momento; frena algo el precio de " +
      "la vivienda, pero no lo compensa. Más productividad sube los sueldos, pero " +
      "acelera algo más el precio de la casa, así que el esfuerzo no baja: sube " +
      "un poco. Por encima del 35 %, la regla de prudencia habitual lo da por " +
      "excesivo.",
    levers: ["r", "lam"],
    concept: "esfuerzo hipotecario y capacidad de pago",
    synonyms: ["esfuerzo", "carga hipotecaria", "ratio de endeudamiento"],
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
    plain:
      "El motor no calcula la morosidad de los bancos, que no está en los datos: " +
      "responde con el paro como señal de riesgo. El paro sube si la economía " +
      "produce menos (por ejemplo, si el Estado recorta el déficit) o con un " +
      "marco laboral más protector, y baja con más productividad.",
    levers: ["z", "lam", "sp"],
    concept: "determinantes de la morosidad hipotecaria",
    synonyms: ["mora", "morosidad", "impago", "npl", "default"],
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
    plain:
      "El motor arranca del fuerte ritmo de subida de 2026 y lo acerca cada año a " +
      "su media histórica, en torno al 1,2 % anual. Un Euríbor más alto frena la " +
      "subida sobre todo los primeros años y deja el precio algo más bajo; más " +
      "productividad hace crecer más la economía y acelera la subida de forma " +
      "duradera.",
    levers: ["r", "lam"],
    concept: "precio de la vivienda como colateral bancario",
    synonyms: ["colateral", "garantia", "ltv", "tasacion", "valor del inmueble"],
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
    plain:
      "Sin tocar palancas, el crecimiento se queda en el de hoy. Cada punto más " +
      "de productividad es un punto más de crecimiento, todos los años. Más " +
      "demanda de otros países o más déficit del Estado lo suben, y lo contrario " +
      "lo baja, pero sólo unos años: la economía cambia de tamaño poco a poco y " +
      "luego vuelve a su ritmo.",
    levers: ["ext", "sp", "lam"],
    concept: "determinantes del crecimiento del PIB",
    synonyms: ["economia", "pib", "crecimiento", "recesion", "actividad"],
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
    plain:
      "Este número no lo calcula el motor: es el Euríbor que eliges en la " +
      "palanca, igual todos los años, porque el motor no predice qué hará el " +
      "Banco Central Europeo. Sí calcula su efecto: un Euríbor más alto frena la " +
      "inversión y el consumo, y la economía crece menos durante unos años.",
    levers: ["r"],
    concept: "coste de capital e inversión empresarial",
    synonyms: ["credito", "prestamo", "financiacion", "euribor"],
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
    plain:
      "Sin tocar palancas, la inflación se queda en la de hoy. Si se encarecen la " +
      "energía y lo que compramos fuera, sube los primeros años y el empujón se " +
      "va apagando; como además frena la economía, a la larga queda algo por " +
      "debajo. Una economía más animada la sube un poco. La productividad no la " +
      "mueve.",
    levers: ["pm", "lam"],
    concept: "traspaso de precios de importación a la inflación",
    synonyms: ["inflacion", "ipc", "precios", "energia", "costes"],
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
    plain:
      "Si los países que nos compran crecen menos, se exporta menos y la economía " +
      "va quedando por debajo de donde estaría: el crecimiento baja sobre todo " +
      "los primeros años y luego vuelve a su ritmo, pero lo perdido no se " +
      "recupera. Por eso el paro sube y se queda más alto.",
    levers: ["ext"],
    concept: "demanda externa y ciclo económico",
    synonyms: ["exportaciones", "demanda externa", "clientes", "mercado exterior"],
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
    plain:
      "Sólo lo mueve la subida de pensiones y nóminas: el motor supone que suben " +
      "cada año lo mismo que los precios más lo que marque esa palanca, y esa " +
      "diferencia se acumula. Con la palanca en cero, se queda en 100. El precio " +
      "de la energía mueve la inflación, pero no este índice, porque la nómina la " +
      "sigue.",
    levers: ["idx", "pm"],
    concept: "indexación salarial e inflación",
    synonyms: ["sueldo", "nomina", "poder adquisitivo", "subida salarial"],
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
    plain:
      "Sólo lo mueve el saldo primario: por cada punto que mejora (menos " +
      "déficit), el motor quita 0,24 puntos de PIB a los salarios públicos, y al " +
      "revés si empeora. La productividad no lo cambia: la cifra no se recalcula " +
      "aunque la economía crezca más. Es un reparto fijo del ajuste, que no " +
      "distingue plantilla de sueldos.",
    levers: ["sp", "lam"],
    concept: "consolidación fiscal y gasto en personal",
    synonyms: ["recortes", "plantilla", "empleo publico", "masa salarial"],
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
    plain:
      "Lo mueven dos piezas: el saldo primario, que se decide en el presupuesto, " +
      "y los intereses de la deuda heredada, que nadie elige. Subir el saldo " +
      "primario lo mejora. Lo empeoran el envejecimiento, que añade gasto, y un " +
      "Euríbor más alto, que encarece la deuda poco a poco: cada año sólo se " +
      "renueva una séptima parte.",
    levers: ["sp", "r", "dem"],
    concept: "saldo público y espacio fiscal",
    synonyms: ["deficit", "superavit", "cuentas publicas", "presupuesto"],
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
    plain:
      "Cada año la deuda crece con los intereses y con lo que el Estado gasta de " +
      "más sin contarlos, y se diluye con lo que crece la economía. Sin tocar " +
      "nada, ese gasto de más aumenta con el envejecimiento y la deuda sube sola. " +
      "Un saldo primario mejor la frena; un Euríbor más alto o más envejecimiento " +
      "la empujan.",
    levers: ["sp", "r", "dem"],
    concept: "sostenibilidad fiscal a largo plazo",
    synonyms: ["deuda", "endeudamiento", "sostenibilidad"],
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
    plain:
      "Recortar el déficit (subir el saldo primario) frena la economía: cada " +
      "punto de ajuste acaba dejando el PIB un 1,4 % más abajo y el paro unos 0,7 " +
      "puntos más alto, casi entero en cinco años y mientras dure el ajuste. La " +
      "deuda baja; el paro es la factura. Ambas cifras vienen de la literatura, " +
      "no de estimarlas aquí.",
    levers: ["sp"],
    concept: "multiplicador fiscal y coste del ajuste",
    synonyms: ["ajuste", "recortes", "austeridad", "consolidacion"],
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
    plain:
      "Dependen de cuánta deuda arrastra el Estado y del interés medio que paga. " +
      "El Euríbor y la prima de riesgo lo suben poco a poco: cada año sólo se " +
      "renueva una séptima parte de la deuda. Mejorar el saldo primario baja la " +
      "deuda y, con los años, los intereses. Cuanto más pesan, menos presupuesto " +
      "queda por decidir.",
    levers: ["r", "prima", "sp"],
    concept: "espacio fiscal y carga de intereses",
    synonyms: ["margen", "espacio fiscal", "intereses"],
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
    plain:
      "Tiene dos piezas. Recortar el déficit frena el PIB y sube el paro poco a " +
      "poco, casi del todo en cinco años. El paro de fondo se mueve de golpe: lo " +
      "suben unas instituciones laborales más protectoras y más impuestos y " +
      "cotizaciones sobre el trabajo, y lo baja una productividad mayor.",
    levers: ["sp", "z", "lam"],
    concept: "ley de Okun y desempleo",
    synonyms: ["paro", "desempleo", "empleo", "parados"],
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
    plain:
      "Sólo la mueve el saldo primario: por cada punto de PIB que se recorta el " +
      "déficit, baja casi 0,15 puntos, y sube si se gasta más. En proporción a su " +
      "tamaño es la partida que más se recorta, más del doble que nóminas o " +
      "compras. El envejecimiento no la toca: sin mover el saldo primario, se " +
      "queda en su valor observado.",
    levers: ["sp", "dem"],
    concept: "inversión pública y contratación",
    synonyms: ["obra publica", "licitacion", "contratos", "inversion"],
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
    plain:
      "Estas compras sólo dependen del saldo primario: por cada punto de PIB que " +
      "se recorta el déficit, bajan un octavo de punto, y suben si se gasta más. " +
      "En proporción se recortan igual que nóminas o subvenciones, y menos de la " +
      "mitad que la inversión. Si esa palanca no se mueve, se quedan cada año en " +
      "su valor observado.",
    levers: ["sp"],
    concept: "consumo intermedio y contratación pública",
    synonyms: ["gasto corriente", "compras", "proveedores", "contratos"],
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
    plain:
      "Sólo las mueve el saldo primario: por cada punto de PIB que se recorta el " +
      "déficit, bajan unas tres centésimas de punto, y suben si se gasta más. Es " +
      "poco porque la partida es pequeña; en proporción caen igual que nóminas o " +
      "compras. El envejecimiento no las toca, y los datos no dicen qué empresas " +
      "o sectores las reciben.",
    levers: ["sp", "dem"],
    concept: "subvenciones y transferencias públicas",
    synonyms: ["ayudas", "subvenciones", "transferencias"],
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
    plain:
      "Sube con el paro (algo más de medio punto por cada punto de paro), así que " +
      "la mueve lo que cambia el empleo, como las instituciones laborales o la " +
      "productividad. Recortar el déficit la sube casi un punto por cada punto de " +
      "PIB, y algo más por el paro que provoca. La línea roja del 30 % es el " +
      "nivel de los picos tras 2013.",
    levers: ["z", "lam", "sp"],
    concept: "pobreza infantil y empleo de los hogares",
    synonyms: ["pobreza", "exclusion", "ninos", "menores", "arop"],
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
    plain:
      "Sólo la mueve la palanca del saldo primario: por cada punto de PIB que se " +
      "recorta el déficit, pierde nueve centésimas de punto, en la misma " +
      "proporción que nóminas o compras, y gana si se gasta más. El " +
      "envejecimiento encarece las pensiones y empeora el saldo, pero el motor no " +
      "recorta la educación por ello.",
    levers: ["sp", "dem"],
    concept: "gasto público en educación",
    synonyms: ["educacion", "colegios", "escuela", "ensenanza"],
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
    plain:
      "Cada año la deuda crece con los intereses que paga y con el resto del " +
      "déficit, y pesa menos cuanto más crece el PIB. Por eso sube con el " +
      "Euríbor, la prima de riesgo o el envejecimiento, que encarece el gasto, y " +
      "baja si se recorta el déficit. Los tipos actúan despacio: cada año sólo un " +
      "14 % de la deuda se renueva al tipo nuevo.",
    levers: ["sp", "dem", "r"],
    concept: "equidad intergeneracional y deuda",
    synonyms: ["herencia", "deuda", "generaciones", "futuro"],
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
    plain:
      "Sólo lo mueve la subida de pensiones y nóminas: el motor supone que cada " +
      "año suben igual que los precios, más los puntos que marque esa palanca (o " +
      "menos, si es negativa), y esa diferencia se acumula. Por eso la inflación " +
      "o una energía más cara no lo cambian. Con la palanca en cero, se queda en " +
      "100.",
    levers: ["idx", "pm"],
    concept: "revalorización de las pensiones e inflación",
    synonyms: ["pension", "jubilacion", "poder adquisitivo", "revalorizacion", "ipc"],
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
    plain:
      "Crece al ritmo de la proporción de mayores que proyecta Eurostat, y la " +
      "palanca del envejecimiento agranda o reduce esa subida. También sube si " +
      "las pensiones se revalorizan por encima de la inflación, y baja si la " +
      "economía crece más deprisa que las pensiones, por ejemplo con más " +
      "productividad.",
    levers: ["dem", "idx"],
    concept: "gasto en pensiones y envejecimiento",
    synonyms: ["coste de las pensiones", "gasto en pensiones", "sostenibilidad"],
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
    plain:
      "Sale de la proyección de población de Eurostat; el empleo, los tipos o las " +
      "pensiones del motor no la cambian. Sólo la toca la palanca del " +
      "envejecimiento, que agranda o reduce la subida prevista desde 2026 (en su " +
      "mínimo, la congela). Cuenta personas por edad, no cotizantes ni " +
      "pensionistas.",
    levers: ["dem"],
    concept: "tasa de dependencia demográfica",
    synonyms: ["cotizantes", "dependencia", "envejecimiento", "piramide"],
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
    plain:
      "El motor no calcula el paro juvenil aparte: lo fija en unas 2,3 veces el " +
      "paro general, como en los últimos cinco años. Sube con instituciones " +
      "laborales más protectoras o más impuestos y cotizaciones sobre el trabajo, " +
      "y baja con más productividad o si la economía se anima, por ejemplo con un " +
      "Euríbor más bajo.",
    levers: ["z", "tau", "lam"],
    concept: "desempleo juvenil en España",
    synonyms: ["paro juvenil", "empleo joven", "trabajo", "encontrar trabajo"],
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
    plain:
      "Lo que más la mueve son las instituciones laborales: si protegen más el " +
      "empleo, la temporalidad baja, aunque el paro suba. Además sube un cuarto " +
      "de punto por cada punto de paro; por eso más impuestos y cotizaciones " +
      "sobre el trabajo, que suben el paro, la suben sólo un poco.",
    levers: ["tau", "z"],
    concept: "temporalidad y dualidad del mercado laboral",
    synonyms: ["temporal", "contrato", "precariedad", "fijo"],
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
    plain:
      "El motor la liga a la parte del sueldo que se llevaría la hipoteca de una " +
      "vivienda media: por cada punto que sube esa parte, la sobrecarga gana casi " +
      "dos décimas. Un Euríbor más alto la sube porque encarece la cuota. Más " +
      "productividad sube los sueldos, pero el precio de la vivienda sube algo " +
      "más, así que no la alivia.",
    levers: ["r", "lam"],
    concept: "emancipación juvenil y coste de la vivienda",
    synonyms: ["emancipacion", "alquiler", "independizarse", "irse de casa"],
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
    plain:
      "En el motor el sueldo sube cada año lo mismo que los precios más lo que " +
      "crece la productividad, así que la inflación por sí sola no le quita poder " +
      "de compra: lo que decide es la productividad. Gana o pierde un poco según " +
      "la economía produzca más o menos de lo previsto; por eso la energía cara " +
      "lo frena algo.",
    levers: ["lam", "pm"],
    concept: "salarios reales y productividad",
    synonyms: ["sueldo real", "poder adquisitivo", "salario real"],
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
    plain:
      "Cada año el sueldo sube lo mismo que los precios más lo que crece la " +
      "productividad, y algo más o menos según la economía produzca por encima o " +
      "por debajo de lo previsto; esas subidas se acumulan. La energía cara lo " +
      "infla en euros durante años, al subir los precios, pero con él se compra " +
      "menos.",
    levers: ["lam", "pm"],
    concept: "evolución del salario medio",
    synonyms: ["sueldo", "salario", "nomina", "cuanto ganare"],
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
    plain:
      "El paro sube cuando el país produce menos de lo previsto (si el Estado " +
      "recorta el déficit, sube el Euríbor o se encarece la energía) y baja si " +
      "crecen más los países que nos compran. Y desde el primer año lo suben un " +
      "marco laboral más protector o más impuestos y cotizaciones sobre el " +
      "trabajo; más productividad lo baja.",
    levers: ["z", "lam", "sp"],
    concept: "determinantes del desempleo",
    synonyms: ["paro", "despido", "empleo", "perder el trabajo"],
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
    plain:
      "Más demanda de los países que nos compran o más déficit del Estado hacen " +
      "producir más al país; un Euríbor más alto o la energía cara, menos. Eso " +
      "mueve el crecimiento unos pocos años y luego se apaga, aunque el país " +
      "sigue produciendo más, o menos, que sin ello. Sólo la productividad lo " +
      "cambia de forma duradera.",
    levers: ["ext", "sp"],
    concept: "ciclo económico y trabajo autónomo",
    synonyms: ["actividad", "facturacion", "clientes", "negocio"],
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
    plain:
      "Si se encarecen la energía y lo que se importa, los precios de aquí suben " +
      "más deprisa, sobre todo los primeros años, y el efecto se va apagando; " +
      "pasados unos siete años suben incluso algo menos que sin el " +
      "encarecimiento, porque la economía produce menos. El motor no calcula los " +
      "costes de ningún negocio concreto.",
    levers: ["pm"],
    concept: "costes de insumos e inflación",
    synonyms: ["costes", "inflacion", "precios", "suministros"],
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
    plain:
      "Esta cifra no la calcula el motor: es el Euríbor que se fija con su " +
      "palanca, el mismo todos los años. El motor no predice qué hará el Banco " +
      "Central Europeo; sólo calcula qué pasa si el tipo es ese: encarece " +
      "hipotecas y deuda del Estado, endurece el crédito de los bancos y frena " +
      "algo la actividad y la inflación.",
    levers: ["r"],
    concept: "acceso a financiación de autónomos",
    synonyms: ["credito", "prestamo", "financiacion", "banco"],
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
    plain:
      "La parte de autónomos sube con el paro y baja cuando la economía crece " +
      "más. Por eso la suben un marco laboral más protector o más impuestos sobre " +
      "el trabajo, que elevan el paro, y la bajan más demanda de otros países o " +
      "más productividad. El motor no separa a quien emprende por elección de " +
      "quien no encuentra otro empleo.",
    levers: ["ext", "z", "tau"],
    concept: "autoempleo y mercado laboral",
    synonyms: ["autonomos", "autoempleo", "freelance", "cuenta propia"],
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

/** Crude Spanish plural stripping, enough that «bonos» reaches «bono».
 *
 *  Not a stemmer. A real one would need a dictionary, and the failure this
 *  fixes is almost always the plural: a reader asks about «los bonos» or «las
 *  pensiones» and the question is titled in the singular. */
const stem = (w: string): string => {
  if (w.length > 5 && w.endsWith("es")) return w.slice(0, -2);
  if (w.length > 4 && w.endsWith("s")) return w.slice(0, -1);
  return w;
};

const content = (s: string): string[] =>
  norm(s)
    .split(/[^a-z0-9ñ]+/)
    .filter((w) => w.length > 2 && !STOPWORDS.has(w))
    .map(stem);

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
    const inSyn = new Set(content((q.synonyms ?? []).join(" ")));
    const inConcept = new Set(content(q.concept ?? ""));
    const inMech = new Set(content(q.mechanism));
    let score = 0;
    for (const w of words) {
      // The title outranks the synonyms so that two questions sharing a word
      // are separated by where it appears, not by which comes first in the
      // array. Ties resolved by position are how one question ends up
      // answering everything.
      if (inText.has(w)) score += 4;
      else if (inSyn.has(w)) score += 3;
      else if (inConcept.has(w)) score += 2;
      else if (inMech.has(w)) score += 1;
    }
    if (score > (best?.score ?? 0)) best = { q, score };
  }
  // 3 = one solid hit on the question's own wording, or a concept hit plus a
  // mechanism one. Below that the match is coincidence.
  return best && best.score >= 3 ? best.q : null;
}
