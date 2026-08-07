import { nf, sg } from "../lib/fmt";
import type { PersonaModule } from "./registry";

export const p06: PersonaModule = {
  id: "06",
  chains: [
    { a: "saldo primario", u: "bola de nieve r−g", t: "senda de deuda", k: "b", d: 1, un: "%PIB" },
    { a: "palanca de gasto", u: "multiplicador 1,4", t: "paro", k: "u", d: 1, un: "%" },
    { a: "tipos", u: "refinanciación", t: "espacio fiscal", k: "int", d: 1, un: "%PIB" },
  ],
  narr: (R, k, y) =>
    `Ninguna palanca sale gratis y el tablero lo enseña: con este escenario la deuda de ${y} queda en ${nf(R.b[k], 1)} %PIB, ` +
    `el saldo en ${nf(R.saldo[k], 1)} y los intereses en ${nf(R.int[k], 1)} puntos de PIB, mientras el paro se sitúa en ${nf(R.u[k], 1)} % ` +
    `y el PIB crece al ${sg(R.g[k], 1)} %. Consolidar desplaza la mediana pero no borra la banda; sostener el gasto apuntala el PIB de hoy y empina la senda. ` +
    `La elección «correcta» no aparece en ninguna columna del CSV.`,
  cite: "gold_escenarios_deuda.csv",
};
