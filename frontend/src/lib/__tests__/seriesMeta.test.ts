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
