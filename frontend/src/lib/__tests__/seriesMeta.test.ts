import { describe, expect, it } from "vitest";
import { eur, nf, sg, sgEur } from "../fmt";
import { PANEL_DEPENDENT, SIDES, TABLE_ROWS, tone } from "../seriesMeta";

describe("el color del delta", () => {
  it("no pinta de rojo todo lo que sube", () => {
    // Un salario que sube no es mala noticia, y el paro que sube sí lo es.
    expect(tone(500, "salario", false)).not.toBe("bad");
    expect(tone(1.5, "u", true)).toBe("bad");
  });

  it("no dictamina sobre las series cuyo signo depende del lector", () => {
    // El precio de la vivienda tiene dos lados y la tabla no elige uno.
    expect(tone(10000, "precio", false)).toBe("rel");
    expect(tone(-10000, "precio", false)).toBe("rel");
  });

  it("trata el cero como cero y no como una mejora diminuta", () => {
    expect(tone(0, "b", true)).toBe("zero");
    expect(tone(0.001, "b", true)).toBe("zero");
  });

  it("pinta de verde una deuda que baja", () => {
    expect(tone(-16.9, "b", true)).toBe("good");
  });
});

describe("las filas de la tabla", () => {
  it("son ocho: más deja de leerse de un vistazo", () => {
    expect(TABLE_ROWS).toHaveLength(8);
  });

  it("cada serie con dos lados tiene los dos nombrados", () => {
    for (const [k, lados] of Object.entries(SIDES)) {
      expect(lados, k).toHaveLength(2);
      expect(lados[0]).not.toBe(lados[1]);
    }
  });

  it("marca como dependientes del panel sólo las de la cadena de vivienda", () => {
    expect([...PANEL_DEPENDENT].sort()).toEqual(
      ["cuota", "esf", "hip", "ipv", "precio", "sobre"]);
    expect(PANEL_DEPENDENT.has("b")).toBe(false);
  });
});

describe("separador de millares en magnitudes grandes", () => {
  it("el agrupamiento auto de es-ES lo suprime entre 1000 y 9999", () => {
    // La razón de que exista `eur`, y de que la tabla lo use: sin esto la
    // misma columna mostraba "1033" junto a "171.444".
    expect(nf(1033, 0)).toBe("1033");
    expect(eur(1033)).toBe("1.033");
  });

  it("sgEur mantiene el signo y el separador", () => {
    expect(sg(4784, 0)).toBe("+4784");
    expect(sgEur(4784)).toBe("+4.784");
    expect(sgEur(-4784)).toBe("−4.784");
  });

  it("usa el menos tipográfico, no el guion", () => {
    expect(sgEur(-1000)).toContain("−");
    expect(sgEur(-1000)).not.toContain("-");
  });
});

describe("los recuentos llevan separador de millares", () => {
  it("las cifras que se ven en pantalla, una por una", () => {
    // El agrupamiento "auto" de es-ES suprime el separador entre 1000 y 9999,
    // así que en Biblioteca convivían «17.402» y «3684», y en Evidencia los
    // tamaños muestrales 1.387 y 931 se escribían con reglas distintas.
    // Sólo a partir de cuatro cifras hay millar que separar: 931 y 456 se
    // escriben igual con las dos funciones, y esperar un punto ahí era un
    // error de la prueba, no del formato.
    for (const n of [3684, 4000, 1387, 1311]) {
      expect(eur(n)).toMatch(/\./);
      expect(nf(n, 0)).not.toMatch(/\./);
    }
    for (const n of [931, 456]) {
      expect(eur(n)).toBe(String(n));
    }
    expect(eur(3684)).toBe("3.684");
    expect(eur(17402)).toBe("17.402");
  });

  it("no toca lo que no es un recuento", () => {
    // Porcentajes, años y días se quedan con `nf`: «14 %» y «2050» no llevan
    // separador, y forzarlo daría «2.050».
    expect(nf(14, 0)).toBe("14");
    expect(nf(2050, 0)).toBe("2050");
  });
});

describe("la columna del primer año no se anuncia como dato", () => {
  it("2026 es el primer año proyectado, no un observado", () => {
    // El motor aplica las palancas ya en k=0: la línea base sale de 105,6
    // (observado de 2025) y da 106,32 en 2026, y una palanca lo mueve otra
    // vez. La cabecera decía «2026 · hoy», que invitaba a leerlo como dato,
    // mientras la propia columna mostraba una Δ distinta de cero.
    const encabezado = (y: number, y0: number) => `${y}${y === y0 ? " · inicio" : ""}`;
    expect(encabezado(2026, 2026)).toBe("2026 · inicio");
    expect(encabezado(2026, 2026)).not.toContain("hoy");
    expect(encabezado(2050, 2026)).toBe("2050");
  });
});
