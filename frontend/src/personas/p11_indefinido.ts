import { nf } from "../lib/fmt";
import type { PersonaModule } from "./registry";

export const p11: PersonaModule = {
  id: "11",
  chains: [
    { a: "productividad λ", u: "negociación salarial", t: "salario real acumulado", k: "wrealIdx", d: 1, un: "índice" },
    { a: "inflación IPCA", u: "listón de precios", t: "salario medio", k: "salario", d: 0, un: "€/año" },
    { a: "instituciones z", u: "mercado laboral", t: "paro total", k: "u", d: 1, un: "%" },
  ],
  narr: (R, k, y) =>
    `En ${y} el salario real acumulado se sitúa en un índice de ${nf(R.wrealIdx[k], 1)} (base 100 en 2026) ` +
    `con un salario medio de ${nf(R.salario[k], 0)} €/año. ` +
    `La inflación proyectada del ${nf(R.pi[k], 1)} % y un paro general del ${nf(R.u[k], 1)} % definen la evolución de la renta del trabajo.`,
  cite: "ine_salarios.csv",
};
