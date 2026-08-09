import { nf } from "../lib/fmt";
import type { PersonaModule } from "./registry";

export const p07: PersonaModule = {
  id: "07",
  chains: [
    { a: "saldo primario", u: "presión presupuestaria", t: "inversión pública P51G", k: "p51", d: 2, un: "%PIB" },
    { a: "gasto total", u: "discrecionalidad", t: "consumo intermedio P2", k: "p2", d: 1, un: "%PIB" },
    { a: "subvenciones", u: "transferencias", t: "subvenciones D3", k: "d3", d: 1, un: "%PIB" },
  ],
  narr: (R, k, y) =>
    `En ${y} la inversión pública (P51G) se proyecta en el ${nf(R.p51[k], 2)} %PIB ` +
    `y el consumo intermedio (P2) en el ${nf(R.p2[k], 1)} %PIB. ` +
    `Las subvenciones (D3) suponen un ${nf(R.d3[k], 1)} %PIB, partidas donde la trazabilidad y la contratación pública resultan determinantes.`,
  cite: "gov_10a_exp.csv",
};
