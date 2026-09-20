import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { api } from "../../api/client";
import type { ScenarioResponse } from "../../api/types";
import { baseline, YEARS } from "../../engine/spain";
import { crossCheckEngine, useAppHealth } from "../appHealth";

function response(): ScenarioResponse {
  return {
    vintage: "2026-07-31", computed_not_advice: true, horizon: 2050,
    years: [...YEARS], scenario: structuredClone(baseline()),
    baseline: structuredClone(baseline()), deltas: {}, personas: {}, redlines: [],
  };
}

describe("API/browser model agreement", () => {
  beforeEach(() => useAppHealth.setState({ engineMismatch: false }));
  afterEach(() => vi.restoreAllMocks());

  it("accepts matching outputs for all series and years", async () => {
    vi.spyOn(api, "scenario").mockResolvedValue(response());
    await crossCheckEngine();
    expect(useAppHealth.getState().engineMismatch).toBe(false);
  });

  it("detects housing drift even when the debt trajectory agrees", async () => {
    const remote = response();
    remote.scenario.ipv[1] += 0.1;
    vi.spyOn(api, "scenario").mockResolvedValue(remote);
    await crossCheckEngine();
    expect(useAppHealth.getState().engineMismatch).toBe(true);
  });

  it.each(["missing", "nan", "year"])("rejects malformed comparison data: %s", async (kind) => {
    const remote = response();
    if (kind === "missing") delete remote.scenario.int;
    if (kind === "nan") remote.scenario.int[2] = Number.NaN;
    if (kind === "year") remote.years[1] += 1;
    vi.spyOn(api, "scenario").mockResolvedValue(remote);
    await crossCheckEngine();
    expect(useAppHealth.getState().engineMismatch).toBe(true);
  });
});
