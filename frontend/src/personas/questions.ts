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

export const PERSONA_QUESTIONS: Record<string, PersonaQuestion[]> = { "03": Q03 };

export const questionsFor = (id: string): PersonaQuestion[] =>
  PERSONA_QUESTIONS[id] ?? [];
