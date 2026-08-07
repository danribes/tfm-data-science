import { useMemo } from "react";
import { create } from "zustand";
import {
  LEVER_IDS,
  LEVER_SPECS,
  isMoved,
  presetLevers,
  type LeverId,
  type Levers,
} from "../engine/levers";
import { BASE_LEVERS } from "../engine/vintage";
import { Y0, Y1, runScenario, type Scenario } from "../engine/spain";

export const HORIZON_YEARS = [2026, 2030, 2035, 2040, 2050];

interface ScenarioState {
  levers: Levers;
  horizon: number;
  setLever: (id: LeverId, value: number) => void;
  applyPreset: (presetId: string) => void;
  setHorizon: (year: number) => void;
  resetAll: () => void;
}

const clampHorizon = (y: number): number => Math.min(Y1, Math.max(Y0, Math.round(y)));

export const useScenarioStore = create<ScenarioState>()((set) => ({
  levers: { ...BASE_LEVERS },
  horizon: Y0,
  setLever: (id, value) => set((s) => ({ levers: { ...s.levers, [id]: value } })),
  applyPreset: (presetId) => set({ levers: presetLevers(presetId) }),
  setHorizon: (year) => set({ horizon: clampHorizon(year) }),
  resetAll: () => set({ levers: { ...BASE_LEVERS }, horizon: Y0 }),
}));

export const kIndex = (horizon: number): number => horizon - Y0;

/** Local recompute — spec §3: <16 ms, no network. */
export function useScenario(): Scenario {
  const levers = useScenarioStore((s) => s.levers);
  return useMemo(() => runScenario(levers), [levers]);
}

// ---- URL sync (v16 §E.3: replaceState, only non-base levers) ----

const spec = Object.fromEntries(LEVER_SPECS.map((s) => [s.id, s]));

export function stateToSearch(levers: Levers, horizon: number): string {
  const q = new URLSearchParams();
  q.set("h", String(horizon));
  for (const id of LEVER_IDS) {
    if (isMoved(levers, id)) q.set(id, String(levers[id]));
  }
  return q.toString();
}

export function searchToPatch(search: string): { levers: Partial<Levers>; horizon?: number } {
  const q = new URLSearchParams(search.startsWith("?") ? search.slice(1) : search);
  const levers: Partial<Levers> = {};
  for (const id of LEVER_IDS) {
    const raw = q.get(id);
    if (raw === null) continue;
    const v = Number.parseFloat(raw);
    if (!Number.isFinite(v)) continue;
    levers[id] = Math.min(spec[id].max, Math.max(spec[id].min, v));
  }
  const patch: { levers: Partial<Levers>; horizon?: number } = { levers };
  const h = q.get("h");
  if (h !== null && Number.isFinite(Number(h))) patch.horizon = clampHorizon(Number(h));
  return patch;
}

export function initFromUrl(): void {
  const patch = searchToPatch(window.location.search);
  useScenarioStore.setState((s) => ({
    levers: { ...s.levers, ...patch.levers },
    horizon: patch.horizon ?? s.horizon,
  }));
}

export function startUrlSync(): () => void {
  return useScenarioStore.subscribe((s) => {
    const search = stateToSearch(s.levers, s.horizon);
    window.history.replaceState(null, "", `${window.location.pathname}?${search}`);
  });
}
