import { describe, expect, it } from "vitest";
import { enCorto } from "../enCorto";

const BASE = {
  persona: "10", series: "ujuv", companion: "u",
  value: 21.5, baseValue: 23.4, today: 24.1, year: 2050, firstYear: 2026,
  companionValue: 9.3, companionBase: 10.1, moved: true,
  contributions: [
    { lever_id: "r", lever_name: "Tipo de interés · Euríbor 12m", delta: -1.0, share: 0.54 },
    { lever_id: "idx", lever_name: "Indexación pensiones/nóminas", delta: 0.0, share: 0.0 },
    { lever_id: "tau", lever_name: "Presión fiscal · cuña laboral", delta: -0.6, share: 0.33 },
  ],
};

/** Spoken, not printed: the three things the paragraph must never carry. */
function spokenOnly(t: string) {
  expect(t, "quotation marks").not.toMatch(/[«»"]/);
  expect(t, "brackets").not.toMatch(/[()[\]]/);
  expect(t, "exact decimals").not.toMatch(/\d,\d/);
}

describe("enCorto — the answer told the way you would tell a friend", () => {
  it("says what happens, where it stands, who pushes it, the context, the caveat, and ends on the joke", () => {
    const t = enCorto(BASE);
    spokenOnly(t);
    const order = [
      "el paro de los menores de 25 baja y en 2050 se queda en algo menos del 22 %, unos dos puntos menos que si no tocaras nada, y eso, para ti, es buena noticia.",
      "Para situarte, hoy está cerca del 24 %.",
      "Lo que más empuja es el Euríbor, que explica más o menos la mitad del cambio, y le siguen los impuestos sobre el trabajo.",
      "Para ponerlo en contexto, el paro baja y se queda cerca del 9 %.",
      "no una bola de cristal.",
      "Si en 2050 las cosas quedan así, igual hasta te independizas",
    ].map((s) => t.indexOf(s));
    expect(order.every((i) => i >= 0), t).toBe(true);
    expect(order).toEqual([...order].sort((a, b) => a - b));
    expect(t.trim().endsWith("el casero también ha visto el escenario.")).toBe(true);
  });

  it("reads the example from the page in words: plural subject, a deficit, no numbers to parse", () => {
    const t = enCorto({
      persona: "06", series: "int", companion: "saldo", value: 7.3, baseValue: 7.3, today: 2.68,
      year: 2050, firstYear: 2026, companionValue: -14.7, companionBase: -14.7, moved: false,
    });
    spokenOnly(t);
    expect(t).toContain("en 2050 los intereses de la deuda se quedan cerca del 7 % del PIB");
    expect(t).toContain("hoy están cerca del 3 % del PIB");
    expect(t).toContain("el saldo público apenas se mueve y se queda en un déficit de cerca del 15 % del PIB");
  });

  it("says an index against 2026, with the same rounding in both sentences", () => {
    const t = enCorto({
      persona: "09", series: "nomreal", value: 82.5, baseValue: 100, today: 100,
      year: 2050, firstYear: 2026, moved: true,
    });
    spokenOnly(t);
    expect(t).toContain("se queda un 18 % por debajo de lo que era en 2026, unos 18 puntos menos");
    expect(t).not.toContain("Para situarte");
  });

  it("reads good and bad news from the side of whoever asks", () => {
    const house = { ...BASE, series: "precio", companion: undefined, value: 251000, baseValue: 240500, today: 171444 };
    expect(enCorto({ ...house, persona: "03" })).toContain("para ti, es mala noticia");
    expect(enCorto({ ...house, persona: "02" })).toContain("para ti, es buena noticia");
    spokenOnly(enCorto({ ...house, persona: "03" }));
  });

  it("says so when no moved lever reaches the figure", () => {
    const t = enCorto({ ...BASE, contributions: [{ lever_id: "prima", lever_name: "Prima de riesgo · spread ES–DE", delta: 0, share: 0 }] });
    expect(t).toContain("Ninguna de las palancas que has movido llega de verdad a esta cifra.");
  });

  it("with nothing moved it describes the base, and the joke is the no-change one", () => {
    const t = enCorto({ ...BASE, value: 23.4, moved: false, contributions: undefined });
    expect(t).toMatch(/^Resumiendo: sin tocar ninguna palanca/);
    expect(t.trim().endsWith("y quizá también el wifi del vecino.")).toBe(true);
  });
});

describe("enCorto — every question of every profile speaks", () => {
  it("no quotes, brackets or decimals for any series, on the engine's own numbers", async () => {
    const { PERSONA_QUESTIONS } = await import("../questions");
    const { baseline, runScenario } = await import("../../engine/spain");
    const { seriesOf } = await import("../../engine/derived");
    const { BASE_LEVERS } = await import("../../engine/vintage");
    const base = baseline();
    const scn = runScenario({ ...BASE_LEVERS, r: BASE_LEVERS.r + 1.5, sp: 1, idx: -0.5 });
    for (const [pid, qs] of Object.entries(PERSONA_QUESTIONS)) {
      for (const q of qs) {
        for (const k of [0, 24]) {
          const t = enCorto({
            persona: pid, series: q.series, companion: q.companion,
            value: seriesOf(scn, q.series)[k], baseValue: seriesOf(base, q.series)[k],
            today: seriesOf(base, q.series)[0], year: 2026 + k, firstYear: 2026,
            companionValue: q.companion ? seriesOf(scn, q.companion)[k] : undefined,
            companionBase: q.companion ? seriesOf(base, q.companion)[k] : undefined,
            moved: true,
          });
          expect(t, `${pid}/${q.id}`).not.toMatch(/[«»"()[\]]|\d,\d|la cifra de /);
        }
      }
    }
  });
});
