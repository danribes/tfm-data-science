/** Texto de pasaje listo para leer.
 *
 *  Los pasajes salen de extraer texto de PDF, y el extractor conserva los
 *  guiones con los que el libro partía una palabra al final de renglón. En
 *  pantalla eso se lee «unemploy- ment», «infla- ción», «rela- tion»: la
 *  palabra correcta está rota por un salto de línea que ya no existe.
 *
 *  Unirla no cambia lo que dice la fuente, lo restituye: el libro pone
 *  «unemployment». Se hace sólo con el patrón inequívoco —minúscula, guion,
 *  espacio, minúscula— para no tocar los compuestos legítimos («coste-
 *  beneficio» no aparece así) ni los guiones de rango o de diálogo.
 */
export function limpiarPasaje(texto: string): string {
  return texto
    .replace(/([a-záéíóúñü])-\s+([a-záéíóúñü])/g, "$1$2")
    .replace(/\s+/g, " ")
    .trim();
}

/** Marca como fragmento un pasaje que empieza a media palabra.
 *
 *  El corpus se trocea por tamaño, no por frase, así que un pasaje puede
 *  empezar en «ose a point on the Phillips curve» o en «h of the real
 *  quantity». Sin marca eso se lee como una errata del sistema; con puntos
 *  suspensivos se lee como lo que es, el recorte de una página. No se altera
 *  el texto: se le antepone la señal.
 */
export function marcarFragmento(texto: string): string {
  return /^[a-záéíóúñü]/.test(texto) ? `…${texto}` : texto;
}
