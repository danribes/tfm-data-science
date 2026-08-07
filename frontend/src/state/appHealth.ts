import { create } from "zustand";
import { api } from "../api/client";
import { baseline } from "../engine/spain";

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

/** Spec §3 cross-check: POST /scenario at base once, compare b at 2026/2035/2050 (idx 0/9/24). */
export async function crossCheckEngine(): Promise<void> {
  try {
    const res = await api.scenario({ levers: {}, horizon: 2050 });
    const local = baseline();
    const mismatch = [0, 9, 24].some(
      (i) => Math.abs((res.scenario.b?.[i] ?? Number.NaN) - local.b[i]) > 1e-6,
    );
    useAppHealth.getState().setEngineMismatch(mismatch);
  } catch {
    // API down is handled by the blocking screen; a failed cross-check is not a mismatch.
  }
}
