import { nf } from "../lib/fmt";
import type { PersonaModule } from "./registry";

export const p08: PersonaModule = {
  id: "08",
  chains: [
    { a: "saldo primario", u: "presión fiscal", t: "gasto en educación", k: "edu", d: 2, un: "%PIB" },
    { a: "empleo", u: "renta familiar", t: "pobreza infantil AROP", k: "arop", d: 1, un: "%" },
    { a: "demografía", u: "dependencia 65+", t: "deuda heredada", k: "b", d: 1, un: "%PIB" },
  ],
  narr: (R, k, y) =>
    `En ${y} el riesgo de pobreza o exclusión infantil (AROP <16) se sitúa en el ${nf(R.arop[k], 1)} % ` +
    `y el gasto público en educación en el ${nf(R.edu[k], 2)} %PIB. ` +
    `La tasa de dependencia alcanza ${nf(R.dep[k], 1)} personas mayores por cada 100 en edad de trabajar, ` +
    `con una carga de deuda heredada de ${nf(R.b[k], 1)} %PIB.`,
  cite: "gold_pobreza_infantil.csv",
};
