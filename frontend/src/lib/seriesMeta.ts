import type { SeriesKey } from "../engine/spain";

/** Metadatos de serie que la tabla necesita y que hasta ahora sólo existían
 *  del lado de Python.
 *
 *  Tres cosas, y ninguna es cosmética:
 *
 *  · `SIDES` — series cuyo signo depende de quién pregunte. Un precio de
 *    vivienda que sube es buena noticia para quien ya tiene piso y mala para
 *    quien quiere comprarlo, así que pintarlo de rojo o de verde es tomar
 *    partido por un lector. Van en azul y sin veredicto.
 *
 *  · `PANEL_DEPENDENT` — las seis series que dependen de los dos parámetros
 *    estimados. Verificado contra el motor, no escrito a mano: son las que
 *    cambian al sustituir IPV_LR/IPV_REV por sus valores heredados.
 *
 *  · `TABLE_ROWS` — ocho filas. Con más, la tabla deja de leerse de un vistazo.
 */
export const SIDES: Record<string, [string, string]> = {
  precio: ["quien ya tiene piso", "quien quiere comprar"],
  ipv: ["quien ya tiene piso", "quien quiere comprar"],
  salario: ["quien cobra un sueldo", "quien paga nóminas"],
  salmes: ["quien cobra un sueldo", "quien paga nóminas"],
  wrealIdx: ["quien cobra un sueldo", "quien paga nóminas"],
  pens: ["quien cobra una pensión", "quien la paga con sus impuestos"],
};

export const PANEL_DEPENDENT = new Set(["ipv", "precio", "cuota", "esf", "hip", "sobre"]);

export const TABLE_ROWS: { k: SeriesKey; lab: string; plain: string }[] = [
  { k: "b", lab: "Deuda pública",
    plain: "Todo lo que debe el Estado, comparado con lo que produce el país en un año." },
  { k: "u", lab: "Paro",
    plain: "De cada cien personas que quieren trabajar, cuántas no encuentran empleo." },
  { k: "pi", lab: "IPCA",
    plain: "La inflación: cuánto suben los precios en un año. Se mide igual en toda la eurozona para poder comparar." },
  { k: "saldo", lab: "Saldo público",
    plain: "Lo que ingresa el Estado menos lo que gasta, intereses incluidos. En negativo es déficit." },
  { k: "precio", lab: "Precio vivienda",
    plain: "Lo que cuesta comprar una vivienda media." },
  { k: "cuota", lab: "Cuota hipotecaria",
    plain: "Lo que se paga cada mes por una hipoteca media a 25 años." },
  { k: "salario", lab: "Salario medio",
    plain: "Lo que cobra al año, de media, una persona asalariada." },
  { k: "esf", lab: "Esfuerzo vivienda",
    plain: "Qué parte del sueldo se va en pagar la hipoteca." },
];

/** Los años de la tabla. El primero es el dato observado y se marca como tal:
 *  aterrizar en él con todos los deltas a 0,0 es la primera impresión que hay
 *  que evitar. */
export const TABLE_YEARS = [2026, 2030, 2040, 2050];

/** Verde/rojo sólo cuando el signo del bienestar es de la serie y no del
 *  lector. Devuelve la clase CSS. */
export function tone(delta: number, key: string, upIsBad: boolean): string {
  if (Math.abs(delta) < 5e-3) return "zero";
  if (key in SIDES) return "rel";
  return (delta > 0) === upIsBad ? "bad" : "good";
}
