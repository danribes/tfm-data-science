import { describe, expect, it } from "vitest";
import { PERSONA_QUESTIONS, matchQuestion, questionsFor } from "../questions";
import { SHIPPED_IDS } from "../registry";
import { ALL_SERIES_KEYS } from "../../engine/derived";
import { LEVER_SPECS } from "../../engine/levers";
import { SERIES_FORMAT } from "../../components/KpiRow";
import { seriesLabel, TABLE_ROWS } from "../../lib/seriesMeta";

const LEVER_IDS = new Set(LEVER_SPECS.map((s) => s.id));

describe("persona question sets", () => {
  it("every shipped persona has one", () => {
    for (const id of SHIPPED_IDS) {
      expect(questionsFor(id).length, `persona ${id}`).toBeGreaterThan(0);
    }
  });

  it.each(Object.entries(PERSONA_QUESTIONS))("%s is answerable", (pid, questions) => {
    const ids = new Set(questions.map((q) => q.id));
    expect(ids.size, `${pid}: duplicate question id`).toBe(questions.length);

    for (const q of questions) {
      // A series the engine does not produce renders an empty chart and a NaN
      // headline, which reads as a real answer rather than a missing one.
      expect(ALL_SERIES_KEYS, `${pid}/${q.id}: series`).toContain(q.series);
      if (q.companion) {
        expect(ALL_SERIES_KEYS, `${pid}/${q.id}: companion`).toContain(q.companion);
      }
      // Without a format entry the value prints unitless and to the wrong
      // number of decimals.
      expect(SERIES_FORMAT[q.series], `${pid}/${q.id}: no SERIES_FORMAT`).toBeDefined();

      // A lever id that does not exist cannot be highlighted, and the reader
      // is told to reach for a control that is not there.
      for (const lever of q.levers) {
        expect(LEVER_IDS, `${pid}/${q.id}: lever ${lever}`).toContain(lever);
      }
      expect(q.levers.length, `${pid}/${q.id}: no levers`).toBeGreaterThan(0);

      // AnswerPanel skips a follow-up whose id is unknown, so a typo here is
      // a chip that silently disappears rather than an error.
      for (const f of q.followUps) {
        expect(ids, `${pid}/${q.id}: followUp ${f}`).toContain(f);
        expect(f, `${pid}/${q.id}: follows itself`).not.toBe(q.id);
      }
      expect(q.mechanism.length, `${pid}/${q.id}: mechanism too short`).toBeGreaterThan(40);
      expect(q.text.endsWith("?"), `${pid}/${q.id}: not a question`).toBe(true);
    }
  });
});

describe("matchQuestion", () => {
  const q01 = questionsFor("01");

  it("resolves an unaccented paraphrase to the right question", () => {
    expect(matchQuestion("cuanto llega la deuda publica", q01)?.id).toBe("deuda");
    expect(matchQuestion("que cupon me pagara el bono", q01)?.id).toBe("cupon");
    expect(matchQuestion("cuanto se va en intereses", q01)?.id).toBe("intereses");
  });

  it("refuses questions this profile cannot answer", () => {
    // Each of these used to answer the bond-coupon question, because a
    // stopword like «cuando» or «que» appears in some mechanism sentence and
    // a single hit was enough to win.
    for (const q of [
      "cuando bajara el paro",
      "que pasa con las pensiones",
      "cuanto costara una vivienda",
      "habra recesion en españa",
    ]) {
      expect(matchQuestion(q, q01), q).toBeNull();
    }
  });

  it("ignores stopword-only input", () => {
    expect(matchQuestion("que pasa con esto", q01)).toBeNull();
    expect(matchQuestion("   ", q01)).toBeNull();
  });

  it("does not let the mechanism outvote the question's own wording", () => {
    // «deuda» is in the deuda question's title and in the cupon question's
    // mechanism; the title has to win.
    expect(matchQuestion("deuda publica", q01)?.id).toBe("deuda");
  });
});

describe("matchQuestion — real phrasings readers use", () => {
  const q01 = questionsFor("01");

  it("answers the bond yield asked in plural, with the ordinary word", () => {
    // Reported verbatim: «bonos» did not reach «bono» and «rendimiento»
    // appeared in no question text, so the natural phrasing was refused.
    expect(matchQuestion("cuando van a bajar los rendimientos de los bonos a 10 años?", q01)?.id)
      .toBe("cupon");
  });

  it("matches plurals against singular titles", () => {
    expect(matchQuestion("cuanto pagamos de intereses", q01)?.id).toBe("intereses");
    // «pension» alone is in both titles, so it cannot separate them; «coste»
    // is what makes this the gasto question rather than the poder one.
    expect(matchQuestion("coste de las pensiones", questionsFor("09"))?.id).toBe("gasto");
    expect(matchQuestion("cuantos autonomos habra", questionsFor("12"))?.id).toBe("cuota");
  });

  it("answers the factual part of an advice-shaped question", () => {
    // «me conviene comprar bonos» is advice, which this app never gives. The
    // yield path plus its mechanism is the factual half, and the disclaimer is
    // already on every page; refusing outright would withhold what it does know.
    expect(matchQuestion("me conviene comprar bonos ahora", q01)?.id).toBe("cupon");
  });

  it("still refuses what the profile cannot answer", () => {
    for (const q of ["cuando bajara el paro", "cuanto costara una vivienda"]) {
      expect(matchQuestion(q, q01), q).toBeNull();
    }
  });
});

describe("una pregunta que enuncia un supuesto lo aplica", () => {
  // PERSONA_QUESTIONS va indexado por perfil; aquí interesan todas juntas.
  const TODAS = Object.values(PERSONA_QUESTIONS).flat();

  it("«¿Y si el Euríbor sube al 4,8 %?» trae ese 4,8", () => {
    // Sin esto, la aplicación dejaba la palanca en 2,80 y contestaba con el
    // caso base: el titular decía 49,1 % debajo de una pregunta sobre una
    // subida de tipos. Una pregunta que no aplica su propia premisa no es un
    // escenario, es un titular.
    const q = TODAS.find((x) => x.id === "euribor")!;
    expect(q.apply).toEqual({ r: 4.8 });
    expect(q.text).toContain("4,8");
  });

  it("el valor aplicado coincide con el que cita el enunciado", () => {
    for (const q of TODAS) {
      if (!q.apply) continue;
      for (const valor of Object.values(q.apply)) {
        const escrito = String(valor).replace(".", ",");
        expect(q.text, q.id).toContain(escrito);
      }
    }
  });

  it("las preguntas cualitativas no inventan una premisa", () => {
    // «¿Y si se dispara la prima?» no cita cifra: elegirla por el lector sería
    // inventarle el supuesto. Se quedan sin `apply` a propósito.
    for (const id of ["prima-riesgo", "demanda-externa", "salarios"]) {
      const q = TODAS.find((x) => x.id === id);
      if (q) expect(q.apply, id).toBeUndefined();
    }
  });
});

describe("toda serie que se pinta tiene nombre legible", () => {
  const TODAS_S = Object.values(PERSONA_QUESTIONS).flat();

  // El encabezado del panel de respuesta escribe el nombre de la serie
  // acompañante. Sin entrada en SERIES_LABEL escribía la clave: «· dep».
  it("ninguna clave de pregunta cae al identificador crudo", () => {
    const sin: string[] = [];
    for (const q of TODAS_S) {
      for (const k of [q.series, q.companion]) {
        if (k && seriesLabel(k) === k) sin.push(`${q.id}:${k}`);
      }
    }
    expect(sin).toEqual([]);
  });

  it("la tabla y el panel llaman igual a las mismas ocho series", () => {
    for (const fila of TABLE_ROWS) {
      expect(seriesLabel(fila.k)).toBe(fila.lab);
    }
  });
});
