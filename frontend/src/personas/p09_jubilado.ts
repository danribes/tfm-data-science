import { nf } from "../lib/fmt";
import type { PersonaModule } from "./registry";

export const p09: PersonaModule = {
  id: "09",
  chains: [
    { a: "indexación ι", u: "revalorización", t: "poder de compra real", k: "nomreal", d: 1, un: "índice" },
    { a: "demografía", u: "tasa dependencia", t: "gasto pensiones", k: "pens", d: 1, un: "%PIB" },
    { a: "inflación IPCA", u: "coste vida", t: "poder adquisitivo", k: "pi", d: 1, un: "%" },
  ],
  narr: (R, k, y) =>
    `Para ${y}, el gasto total en pensiones se proyecta en el ${nf(R.pens[k], 1)} %PIB bajo una inflación del ${nf(R.pi[k], 1)} %. ` +
    `El índice de poder de compra de la nómina se sitúa en ${nf(R.nomreal[k], 1)} (base 100 en 2026), ` +
    `en un contexto demográfico con ${nf(R.dep[k], 1)} personas mayores por cada 100 cotizantes en edad laboral.`,
  cite: "gold_projections.csv",
};
