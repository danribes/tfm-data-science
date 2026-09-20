import { create } from "zustand";
import { api } from "../api/client";
import { baseline, SERIES_KEYS, YEARS } from "../engine/spain";

export const STALE_LIMIT_DAYS = 90;

export function staleDays(vintage: string, now: Date = new Date()): number {
  const v = new Date(`${vintage}T00:00:00Z`);
  return Math.floor((now.getTime() - v.getTime()) / 86_400_000);
}

interface AppHealth {
  engineMismatch: boolean;
  extraWarnings: string[];
  setEngineMismatch: (v: boolean) => void;
  addWarning: (text: string) => void;
}
export const useAppHealth = create<AppHealth>()((set) => ({
  engineMismatch: false,
  extraWarnings: [],
  setEngineMismatch: (v) => set({ engineMismatch: v }),
  addWarning: (text) => set((s) => ({ extraWarnings: [...s.extraWarnings, text] })),
}));

/** Compare every baseline series/year: debt alone cannot detect housing or fiscal drift. */
export async function crossCheckEngine(): Promise<void> {
  try {
    const res = await api.scenario({ levers: {}, horizon: 2050 });
    const local = baseline();
    const mismatch = res.years.length !== YEARS.length
      || res.years.some((year, i) => year !== YEARS[i])
      || SERIES_KEYS.some((key) => {
        const remote = res.scenario[key];
        return !Array.isArray(remote) || remote.length !== YEARS.length
          || remote.some((value, i) => !Number.isFinite(value)
            || Math.abs(value - local[key][i]) > 1e-6);
      });
    useAppHealth.getState().setEngineMismatch(mismatch);
  } catch {
    // API down is handled by the blocking screen; a failed cross-check is not a mismatch.
  }
}
