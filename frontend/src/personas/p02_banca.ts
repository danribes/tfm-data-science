import { eur, nf, sg } from "../lib/fmt";
import type { PersonaModule } from "./registry";

export const p02: PersonaModule = {
  id: "02",
  chains: [
    { a: "Euríbor", u: "cuota nueva", t: "esfuerzo del hogar", k: "esf", d: 1, un: "%" },
    { a: "IPV", u: "LTV efectivo", t: "severidad si impago", k: "ipv", d: 1, un: "% a/a" },
    { a: "paro", u: "mora", t: "pérdida esperada", k: "u", d: 1, un: "%" },
  ],
  narr: (R, k, y) =>
    `El margen lo marca un Euríbor al ${nf(R.r[k], 2)} % y el riesgo lo marcan el empleo (paro ${nf(R.u[k], 1)} %) ` +
    `y un colateral que se mueve al ${sg(R.ipv[k], 1)} % anual. En ${y} la cuota mediana teórica sale a ${eur(R.cuota[k])} €/mes ` +
    `y el esfuerzo sobre la nómina media a ${nf(R.esf[k], 1)} %. Hueco declarado: la serie de mora bancaria (NPL, Banco de España) sigue sin conectar — data/README.md.`,
  cite: "gold_cuota_teorica.csv",
};
