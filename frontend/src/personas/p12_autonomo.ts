import { nf, sg } from "../lib/fmt";
import type { PersonaModule } from "./registry";

export const p12: PersonaModule = {
  id: "12",
  chains: [
    { a: "demanda externa Y*", u: "actividad", t: "crecimiento PIB real", k: "g", d: 1, un: "% a/a" },
    { a: "precios energía pm", u: "inputs", t: "inflación IPCA", k: "pi", d: 1, un: "%" },
    { a: "Euríbor r", u: "financiación", t: "cuota autoempleo", k: "auton", d: 1, un: "% ocupados" },
  ],
  narr: (R, k, y) =>
    `En ${y} el PIB real se mueve al ${sg(R.g[k], 1)} % anual y la cuota de autoempleo representa el ${nf(R.auton[k], 1)} % del empleo total. ` +
    `Las condiciones de coste e insumos se ven condicionadas por una inflación del ${nf(R.pi[k], 1)} % ` +
    `y un Euríbor del ${nf(R.r[k], 2)} %.`,
  cite: "wb_self_employment.csv",
};
