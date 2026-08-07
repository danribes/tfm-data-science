import { eur, nf } from "../lib/fmt";
import type { PersonaModule } from "./registry";

export const p03: PersonaModule = {
  id: "03",
  chains: [
    { a: "Euríbor", u: "cuota", t: "esfuerzo sobre la nómina", k: "esf", d: 1, un: "%" },
    { a: "IPV", u: "entrada 20 %", t: "años de ahorro previo", k: "precio", d: 0, un: "€" },
    { a: "salarios", u: "WS: π+λ+φ·holgura", t: "renta disponible", k: "salmes", d: 0, un: "€/mes" },
  ],
  narr: (R, k, y) =>
    `En ${y} el precio mediano sale a ${eur(R.precio[k])} € — entrada del 20 %: ${eur(R.precio[k] * 0.2)} € — ` +
    `y la cuota a ${eur(R.cuota[k])} €/mes contra un salario bruto de ${eur(R.salmes[k])} €/mes. ` +
    `El esfuerzo queda en ${nf(R.esf[k], 1)} % frente a la regla prudencial del 35 %. ` +
    `Las dos ramas cuelgan de la misma palanca: el tipo mueve la cuota por arriba y el precio por abajo.`,
  cite: "gold_cuota_teorica.csv",
};
