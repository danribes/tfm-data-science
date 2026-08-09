import { nf, sg } from "../lib/fmt";
import type { PersonaModule } from "./registry";

export const p04: PersonaModule = {
  id: "04",
  chains: [
    { a: "demanda externa Y*", u: "demanda total", t: "PIB real", k: "g", d: 1, un: "% a/a" },
    { a: "Euríbor r", u: "coste de capital", t: "inversión privada", k: "r", d: 2, un: "%" },
    { a: "precios energía pm", u: "coste de insumos", t: "IPCA", k: "pi", d: 1, un: "%" },
  ],
  narr: (R, k, y) =>
    `En ${y} el PIB real crece al ${sg(R.g[k], 1)} % anual con un tipo de interés de referencia del ${nf(R.r[k], 2)} %. ` +
    `La inflación IPCA se proyecta en el ${nf(R.pi[k], 1)} % y la tasa de desempleo general en el ${nf(R.u[k], 1)} %, ` +
    `configurando el escenario macro para el nacimiento de nuevas empresas.`,
  cite: "eurostat_gdp_q_es.csv",
};
