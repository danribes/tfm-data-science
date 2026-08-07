import { describe, expect, it } from "vitest";
import { api, ApiError } from "../client";
import { server } from "../../test/msw/server";
import { http, HttpResponse } from "msw";

describe("typed API client against MSW", () => {
  it("GET /health carries vintage and the no-advice flag", async () => {
    const h = await api.health();
    expect(h.vintage).toBe("2026-07-31");
    expect(h.computed_not_advice).toBe(true);
    expect(h.engine_version).toBe("1.0.0");
  });

  it("GET /presets returns the 8 v16 presets with Spanish labels verbatim", async () => {
    const p = await api.presets();
    expect(p.presets).toHaveLength(8);
    expect(p.presets[1]).toEqual({ id: "S1", nm: "S1 tipos +200 pb", set: { r: 4.8 } });
    expect(p.presets[7].set).toEqual({ r: 4.8, pm: 50.0, prima: 150.0 });
  });

  it("GET /redlines returns the 9 v12 lines", async () => {
    const r = await api.redlines();
    expect(r.redlines).toHaveLength(9);
    expect(r.redlines.find((x) => x.id === "deuda_105")).toMatchObject({ series: "b", threshold: 105.0, cmp: "gt" });
  });

  it("GET /personas returns cards 01/02/03/06 with outs and reds", async () => {
    const pe = await api.personas();
    expect(pe.personas.map((c) => c.id)).toEqual(["01", "02", "03", "06"]);
    const p02 = pe.personas[1];
    expect(p02.pill).toBe("🏦 Banca");
    expect(p02.reds[0].k).toBe("ipvreal");
    expect(p02.outs).toHaveLength(5);
  });

  it("POST /scenario echoes full 2026–2050 series regardless of horizon (handoff note 4)", async () => {
    const s = await api.scenario({ levers: { r: 4.8 }, horizon: 2035 });
    expect(s.years).toHaveLength(25);
    expect(s.scenario.b).toHaveLength(25);
    expect(s.horizon).toBe(2035);
  });

  it("POST /scenario/montecarlo returns 5 percentile bands", async () => {
    const mc = await api.montecarlo({ seed: 42, n_paths: 4000, horizon: 2070 });
    expect(Object.keys(mc.percentiles).sort()).toEqual(["p25", "p5", "p50", "p75", "p95"].sort());
    expect(mc.percentiles.p50).toHaveLength(mc.years.length);
    // fixture pins: p50 @2030=113.3, @2050=231.2999
    expect(mc.percentiles.p50[mc.years.indexOf(2030)]).toBeCloseTo(113.3, 4);
    expect(mc.percentiles.p50[mc.years.indexOf(2050)]).toBeCloseTo(231.2999, 4);
  });

  it("network/HTTP failure surfaces as ApiError", async () => {
    server.use(http.get("http://localhost:8000/constants", () => HttpResponse.error()));
    await expect(api.constants()).rejects.toThrowError(ApiError);
    await expect(api.constants()).rejects.toThrow(/\/constants/);
  });
});
