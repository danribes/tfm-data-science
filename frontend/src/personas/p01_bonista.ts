import { nf } from "../lib/fmt";
import type { PersonaModule } from "./registry";

export const p01: PersonaModule = {
  id: "01",
  chains: [
    { a: "tipo BCE", u: "Euríbor", t: "coste de refinanciación", k: "int", d: 1, un: "%PIB" },
    { a: "saldo primario", u: "emisión neta", t: "senda de deuda", k: "b", d: 1, un: "%PIB" },
    { a: "prima de riesgo", u: "spread", t: "cupón exigido", k: "bono", d: 2, un: "%" },
  ],
  narr: (R, k, y) =>
    `Con las palancas de hoy el cupón a 10 años sale a ${nf(R.bono[k], 2)} % y el spread a ${nf(R.spread[k], 0)} pb. ` +
    `En ${y} la identidad de deuda deja el saldo en ${nf(R.b[k], 1)} %PIB con ${nf(R.int[k], 1)} puntos de PIB en intereses — gasto que nadie elige. ` +
    `La banda p5–p95 del Monte Carlo heredado sigue debajo: lo que un acreedor mira no es la mediana, es la anchura.`,
  cite: "gold_escenarios_deuda.csv",
};
