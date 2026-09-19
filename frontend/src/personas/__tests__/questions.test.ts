import { describe, expect, it } from "vitest";
import { PERSONA_QUESTIONS, questionsFor } from "../questions";
import { SHIPPED_IDS } from "../registry";
import { ALL_SERIES_KEYS } from "../../engine/derived";
import { LEVER_SPECS } from "../../engine/levers";
import { SERIES_FORMAT } from "../../components/KpiRow";

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
