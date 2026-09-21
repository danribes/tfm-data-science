import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

/** Ninguna versión interna del motor debe llegar a la pantalla.
 *
 *  «v16» es el nombre de un prototipo anterior de este repositorio. Al lector
 *  no le dice nada, y peor: la ficha llegó a afirmar «la calibración v16 usaba
 *  3,00» para un parámetro que el motor ya no toma de ahí, porque ahora usa la
 *  estimación del panel. Era arqueología interna presentada como procedencia.
 *
 *  Los comentarios del código sí pueden nombrarla —ahí documenta de dónde se
 *  portó cada constante y es útil para quien mantiene esto—, así que se quitan
 *  antes de mirar.
 */
//: vitest corre con la raíz del frontend como cwd.
const RAIZ = join(process.cwd(), "src");

function fuentes(dir: string, out: string[] = []): string[] {
  for (const nombre of readdirSync(dir)) {
    const ruta = join(dir, nombre);
    if (statSync(ruta).isDirectory()) {
      if (nombre === "__tests__" || nombre === "test" || nombre === "node_modules") continue;
      fuentes(ruta, out);
    } else if (/\.tsx?$/.test(nombre)) {
      out.push(ruta);
    }
  }
  return out;
}

/** Quita comentarios de bloque y de línea. Aproximado a propósito: para esto
 *  basta, y un analizador completo sería más código que la comprobación. */
function sinComentarios(src: string): string {
  return src.replace(/\/\*[\s\S]*?\*\//g, "").replace(/\/\/[^\n]*/g, "");
}

describe("la interfaz no nombra versiones internas del motor", () => {
  const archivos = fuentes(RAIZ);

  it("encuentra los fuentes que debe revisar", () => {
    expect(archivos.length).toBeGreaterThan(40);
  });

  it("no queda ningún «v16» fuera de los comentarios", () => {
    // Sin delimitadores de palabra a propósito: `\bv16\b` no casa con
    // "build_v16.py" —el guion bajo es carácter de palabra— y esa cadena
    // seguía publicándose en «Datos y método» con el guardián en verde.
    const culpables = archivos
      .map((f) => [f, sinComentarios(readFileSync(f, "utf8"))] as const)
      .filter(([, src]) => /v16/i.test(src))
      .map(([f]) => f.replace(RAIZ + "/", ""));
    expect(culpables).toEqual([]);
  });

  it("no queda ninguna referencia de planificación interna", () => {
    // "AC-V6" y "phase 3 contests" venían en la procedencia de las 34
    // constantes que se publican en «Datos y método».
    const culpables = archivos
      .map((f) => [f, sinComentarios(readFileSync(f, "utf8"))] as const)
      .filter(([, src]) => /AC-V\d|phase \d contests/i.test(src))
      .map(([f]) => f.replace(RAIZ + "/", ""));
    expect(culpables).toEqual([]);
  });
});
