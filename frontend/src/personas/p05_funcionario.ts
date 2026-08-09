import { nf } from "../lib/fmt";
import type { PersonaModule } from "./registry";

export const p05: PersonaModule = {
  id: "05",
  chains: [
    { a: "saldo primario sp", u: "consolidación fiscal", t: "masa salarial D1", k: "d1", d: 1, un: "%PIB" },
    { a: "indexación ι", u: "nómina pública", t: "poder de compra", k: "nomreal", d: 1, un: "índice" },
    { a: "inflación IPCA", u: "ipc", t: "saldo público", k: "saldo", d: 1, un: "%PIB" },
  ],
  narr: (R, k, y) =>
    `En ${y} la masa salarial del sector público representa el ${nf(R.d1[k], 1)} %PIB, ` +
    `con un poder de compra acumulado de la nómina de ${nf(R.nomreal[k], 1)} respecto a 2026. ` +
    `El saldo público se sitúa en el ${nf(R.saldo[k], 1)} %PIB bajo una inflación del ${nf(R.pi[k], 1)} %.`,
  cite: "gov_10a_exp.csv",
};
