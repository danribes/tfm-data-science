import { Y0 } from "../engine/spain";

/** Cuántos años de «qué pasó después» pide la interfaz.
 *
 *  El endpoint `/scenario/analog` deriva DOS cosas del año pedido: sobre qué
 *  foto del escenario busca países parecidos, y cuántos años posteriores
 *  devuelve. En el estado de entrada ese año es Y0, así que el recorrido sale
 *  de UN año: la trayectoria trae un solo punto y el gráfico no puede dibujar
 *  una línea con él. Es lo que se veía en el Laboratorio —«Trayectoria (1
 *  años)» con un único dato—.
 *
 *  La causa de fondo es que un mismo parámetro significa dos cosas, y eso se
 *  arregla en el contrato de la API, no aquí. Mientras tanto la interfaz no
 *  pide un recorrido que no sirve para nada: un año que el lector haya elegido
 *  por encima del suelo se respeta.
 */
export const RECORRIDO_MIN = 10;

export function anioDeConsulta(horizon: number): number {
  return Math.max(horizon, Y0 + RECORRIDO_MIN);
}
