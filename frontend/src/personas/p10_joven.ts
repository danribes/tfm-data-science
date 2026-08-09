import { eur, nf } from "../lib/fmt";
import type { PersonaModule } from "./registry";

export const p10: PersonaModule = {
  id: "10",
  chains: [
    { a: "instituciones z", u: "contratación", t: "paro juvenil <25", k: "ujuv", d: 1, un: "%" },
    { a: "cuña fiscal τ", u: "coste laboral", t: "temporalidad", k: "temp", d: 1, un: "%" },
    { a: "precio vivienda IPV", u: "cuota", t: "sobrecarga coste vivienda", k: "sobre", d: 1, un: "%" },
  ],
  narr: (R, k, y) =>
    `En ${y} el paro juvenil (<25 años) se proyecta en el ${nf(R.ujuv[k], 1)} % con una tasa de temporalidad del ${nf(R.temp[k], 1)} %. ` +
    `El salario medio mensual alcanza ${eur(R.salario[k])} €/mes, mientras que la sobrecarga por coste de vivienda ` +
    `afecta al ${nf(R.sobre[k], 1)} % de los jóvenes emancipados.`,
  cite: "eurostat_une_rt_m_es.csv",
};
