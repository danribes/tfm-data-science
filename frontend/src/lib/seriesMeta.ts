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
    plain: "Lo que cobra al año una persona asalariada típica: la mitad cobra más y la mitad menos." },
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

/** Nombre legible de cada serie.
 *
 *  Existía repartido: el motor lo lleva persona a persona en `outs[].lab`, la
 *  tabla en `TABLE_ROWS`, el esquema presupuestario en `fiscalFlows`. Lo que
 *  no había era un sitio donde buscarlo por clave, así que el panel de
 *  respuesta escribía el identificador crudo en su encabezado: «Para leerlo
 *  bien · dep», «· p51», «· nomreal».
 *
 *  Las ocho filas de la tabla se toman de `TABLE_ROWS` en vez de repetirse,
 *  para que no puedan decir cosas distintas en dos sitios de la misma página.
 */
export const SERIES_LABEL: Record<string, string> = {
  // partidas de gasto — mismo texto que el esquema presupuestario
  pens: "Pensiones", d1: "Salarios públicos", p2: "Consumo intermedio",
  edu: "Educación", p51: "Inversión pública", d3: "Subvenciones",
  int: "Intereses", gtot: "Gasto total AAPP",
  // el resto, en llano para el lector. Varias difieren a propósito de las
  // etiquetas cortas que el motor conserva en outs[].lab (g, dep, arop, bono,
  // spread, ujuv, ipv, sobre).
  g: "Crecimiento del PIB real", dep: "Dependencia de los mayores (65+)",
  arop: "Pobreza infantil (menores de 16)",
  auton: "Autoempleo", bono: "Interés del bono español a 10 años",
  spread: "Prima de riesgo (España–Alemania)",
  r: "Euríbor 12m", temp: "Temporalidad", ujuv: "Paro juvenil (menores de 25)",
  wrealIdx: "Salario real acumulado", nomreal: "Poder de compra de la nómina",
  ipv: "Subida anual del precio de la vivienda", ipvreal: "Precio vivienda real a/a",
  sobre: "Sobrecarga por gastos de vivienda", hip: "Nueva producción hipotecaria",
  bls: "BLS endurecimiento", vida: "Esperanza de vida",
  salmes: "Salario mensual", pb: "Saldo primario",
  // las seis que el Laboratorio enseñaba sólo por su clave
  lvl: "Nivel del PIB frente a la base", gnom: "PIB nominal",
  wnom: "Salario nominal a/a", wreal: "Salario real a/a",
  ief: "Tipo medio que paga la deuda", deficitAbs: "Déficit público (tamaño)",
  ...Object.fromEntries(TABLE_ROWS.map((r) => [r.k, r.lab])),
};

/** El nombre si se conoce; si no, la clave, que es lo que había antes y al
 *  menos no miente sobre qué serie se está pintando. */
export const seriesLabel = (k: string): string => SERIES_LABEL[k] ?? k;

/** Líneas en llano de las series que salen como cifra de cabecera o como
 *  gráfico de compañía en las preguntas de los perfiles y no están en la
 *  tabla. Cada una dice lo que mide la serie tal como la calcula el motor o
 *  la publica su fuente, no lo que sugiere su nombre:
 *
 *  · ujuv   Eurostat une_rt_m, Y_LT25, PC_ACT — no es el paro a secas.
 *  · temp   Eurostat lfsi_pt_q, EMP_TEMP sobre asalariados de 15-64.
 *  · arop   Eurostat ilc_li02 (MED_EI): renta equivalente < 60 % de la mediana,
 *           menores de 16. Es AROP, no AROPE: no incluye la exclusión social.
 *  · sobre  Eurostat ilc_lvho07a: coste de la vivienda > 40 % de la renta.
 *  · auton  Banco Mundial SL.EMP.SELF.ZS, sobre el empleo total.
 *  · dep    ratio de dependencia de Eurostat: 65+ por cada 100 de 15-64.
 *  · bono   el motor lo construye como Euríbor + prima de plazo + prima.
 *  · salmes el salario anual MEDIANO de INE EAES 2024 entre 14 pagas
 *           (24 497 / 14 = 1 749,79); la media sería 29 540. De ahí «típica».
 *  · nomreal y wrealIdx valen 100 en 2026: el motor sólo los mueve de k > 0. */
const EXTRA_PLAIN: Record<string, string> = {
  ujuv: "De cada cien jóvenes menores de 25 años que quieren trabajar, cuántos no encuentran empleo.",
  temp: "De cada cien asalariados de 15 a 64 años, cuántos tienen un contrato temporal.",
  auton: "De cada cien personas con empleo, cuántas trabajan por su cuenta.",
  arop: "De cada cien menores de 16 años, cuántos viven en hogares cuya renta, ajustada según cuántos adultos y niños viven en ellos, no llega al 60 % de la renta mediana del país.",
  sobre: "De cada cien personas, cuántas viven en hogares que gastan en la vivienda más del 40 % de lo que ingresan.",
  dep: "Por cada cien personas en edad de trabajar (de 15 a 64 años), cuántas tienen 65 o más.",
  g: "Cuánto crece en un año lo que produce el país, descontada la subida de precios.",
  ipv: "Cuánto sube, o baja, en un año el precio de la vivienda. Es lo que mide el Índice de Precios de Vivienda (IPV) del INE.",
  r: "El tipo al que se prestan dinero los bancos europeos a un año. De él dependen la mayoría de las hipotecas variables.",
  bono: "El interés que paga España cada año por pedir prestado a diez años: el Euríbor, un extra por prestar a más plazo y la prima de riesgo.",
  spread: "El sobrecoste que paga España frente a Alemania por pedir prestado a diez años, en puntos básicos: 100 pb son 1 punto.",
  salmes: "Lo que cobra al mes una persona asalariada típica —la mitad cobra más y la mitad menos—, repartiendo el sueldo del año en 14 pagas.",
  wrealIdx: "Lo que compra el sueldo comparado con 2026, que vale 100. Por encima de 100, el sueldo ha subido más que los precios.",
  nomreal: "Lo que compra una pensión o una nómina pública comparado con 2026, que vale 100. Por debajo de 100, compra menos que ahora.",
  pens: "Lo que cuestan las pensiones, comparado con lo que produce el país en un año.",
  d1: "Lo que cuestan las nóminas de los empleados públicos, comparado con lo que produce el país en un año.",
  edu: "Lo que gasta el Estado en educación, comparado con lo que produce el país en un año.",
  p2: "Lo que compra el Estado para funcionar —material, suministros, servicios contratados—, comparado con lo que produce el país en un año.",
  p51: "Lo que invierte el Estado en carreteras, edificios, equipos y otras obras, comparado con lo que produce el país en un año.",
  d3: "Las ayudas que da el Estado a las empresas, comparadas con lo que produce el país en un año.",
  int: "Lo que paga el Estado cada año en intereses de su deuda, comparado con lo que produce el país en un año.",
};

/** La línea en llano de las ocho series de la tabla y de las de
 *  EXTRA_PLAIN; `undefined` para el resto, que es mejor que inventarse una
 *  definición. */
export const seriesPlain = (k: string): string | undefined =>
  TABLE_ROWS.find((r) => r.k === k)?.plain ?? EXTRA_PLAIN[k];
