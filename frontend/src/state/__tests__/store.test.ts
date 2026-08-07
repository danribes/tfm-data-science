import { beforeEach, describe, expect, it } from "vitest";
import { BASE_LEVERS } from "../../engine/vintage";
import {
  HORIZON_YEARS,
  initFromUrl,
  kIndex,
  searchToPatch,
  stateToSearch,
  useScenarioStore,
} from "../scenarioStore";

describe("scenarioStore — lever vector + horizon (v16 state shape)", () => {
  beforeEach(() => {
    useScenarioStore.getState().resetAll();
    window.history.replaceState(null, "", "/");
  });

  it("boots base levers, horizon 2026", () => {
    const s = useScenarioStore.getState();
    expect(s.levers).toEqual({ ...BASE_LEVERS });
    expect(s.horizon).toBe(2026);
    expect(kIndex(s.horizon)).toBe(0);
  });

  it("setLever / resetAll", () => {
    useScenarioStore.getState().setLever("r", 4.8);
    expect(useScenarioStore.getState().levers.r).toBe(4.8);
    useScenarioStore.getState().resetAll();
    expect(useScenarioStore.getState().levers).toEqual({ ...BASE_LEVERS });
  });

  it("applyPreset replaces whole vector (S7: r 4.8, pm 50, prima 150)", () => {
    useScenarioStore.getState().setLever("z", -1.0);
    useScenarioStore.getState().applyPreset("S7");
    const L = useScenarioStore.getState().levers;
    expect(L).toEqual({ ...BASE_LEVERS, r: 4.8, pm: 50.0, prima: 150.0 });
    expect(L.z).toBe(0.0); // preset resets levers outside its set
  });

  it("setHorizon clamps [2026, 2050]; HORIZON_YEARS are rail buttons", () => {
    useScenarioStore.getState().setHorizon(2035);
    expect(useScenarioStore.getState().horizon).toBe(2035);
    useScenarioStore.getState().setHorizon(2099);
    expect(useScenarioStore.getState().horizon).toBe(2050);
    expect(HORIZON_YEARS).toEqual([2026, 2030, 2035, 2040, 2050]);
  });

  it("URL round-trip: stateToSearch / searchToPatch", () => {
    expect(stateToSearch({ ...BASE_LEVERS }, 2026)).toBe("h=2026");

    const search = stateToSearch({ ...BASE_LEVERS, r: 4.8, sp: 1.0 }, 2035);
    expect(search).toBe("h=2035&r=4.8&sp=1");

    const patch = searchToPatch(`?${search}`);
    expect(patch.horizon).toBe(2035);
    expect(patch.levers).toEqual({ r: 4.8, sp: 1.0 });
  });

  it("searchToPatch clamps to LEVER_SPECS range and drops unknown keys", () => {
    const patch = searchToPatch("?h=2032&r=99&foo=bar&z=-1.0");
    expect(patch.levers.r).toBe(6.0); // clamped to LEVER_SPECS max
    expect(patch.levers.z).toBe(-1.0);
    expect((patch.levers as Record<string, unknown>).foo).toBeUndefined();
  });

  it("initFromUrl applies the current location.search to the store", () => {
    window.history.replaceState(null, "", "/?h=2035&r=4.8");
    initFromUrl();
    expect(useScenarioStore.getState().levers.r).toBe(4.8);
    expect(useScenarioStore.getState().horizon).toBe(2035);
  });
});
