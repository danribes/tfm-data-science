import { describe, expect, it } from "vitest";
import { enCorto } from "../enCorto";

const BASE = {
  persona: "10", series: "ujuv", companion: "u",
  value: 21.5, baseValue: 23.4, today: 24.1, year: 2050, firstYear: 2026,
  companionValue: 9.3, companionBase: 10.1, moved: true,
  contributions: [
    { lever_name: "Tipo de interés · Euríbor 12m", delta: -1.0, share: 0.54 },
    { lever_name: "Indexación pensiones/nóminas", delta: 0.0, share: 0.0 },
    { lever_name: "Instituciones laborales", delta: -0.6, share: 0.33 },
  ],
};

describe("enCorto — the answer told the way you would tell a friend", () => {
  it("says what happens, where it stands, who pushes it, the context, the caveat, and ends on the joke", () => {
    const t = enCorto(BASE);
    const order = [
      "«Paro juvenil (menores de 25)» baja hasta 21,5 % en 2050, −1,9 puntos frente a no tocar nada (que daría 23,4 %), y eso, para ti, es buena noticia.",
      "Para situarte: hoy está en 24,1 %.",
      "Lo que más empuja es «Tipo de interés · Euríbor 12m», con el 54 % del cambio; le sigue «Instituciones laborales».",
      "Para ponerlo en contexto, «Paro» queda en 9,3 % (−0,8 puntos).",
      "no una bola de cristal.",
      "Si en 2050 las cosas quedan así, igual hasta te independizas",
    ].map((s) => t.indexOf(s));
    expect(order.every((i) => i >= 0), t).toBe(true);
    expect(order).toEqual([...order].sort((a, b) => a - b));
    expect(t.trim().endsWith("el casero también ha visto el escenario.")).toBe(true);
  });

  it("reads good and bad news from the side of whoever asks", () => {
    // A dearer house: bad news for the buyer, not for the bank's collateral.
    const house = { ...BASE, series: "precio", companion: undefined, value: 200000, baseValue: 190000, today: 171444 };
    expect(enCorto({ ...house, persona: "03" })).toContain("para ti, es mala noticia");
    expect(enCorto({ ...house, persona: "02" })).toContain("para ti, es buena noticia");
  });

  it("says so when no moved lever reaches the figure", () => {
    const t = enCorto({ ...BASE, contributions: [{ lever_name: "Prima de riesgo · spread ES–DE", delta: 0, share: 0 }] });
    expect(t).toContain("Ninguna de las palancas que has movido llega de verdad a esta cifra.");
  });

  it("with nothing moved it describes the base, and the joke is the no-change one", () => {
    const t = enCorto({ ...BASE, value: 23.4, moved: false, contributions: undefined });
    expect(t).toMatch(/^Resumiendo: sin tocar ninguna palanca/);
    expect(t.trim().endsWith("y quizá también el wifi del vecino.")).toBe(true);
  });
});
