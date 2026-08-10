import { QueryClient, keepPreviousData, useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import type { Levers } from "../engine/levers";
import { api } from "./client";

export const queryClient = new QueryClient({
  defaultOptions: { queries: { staleTime: Infinity, retry: 1, refetchOnWindowFocus: false } },
});

const STATIC = { staleTime: Infinity } as const;
// Health retries hard on purpose: the deployed API sleeps on the free tier
// and takes ~1 min to wake. Giving up after three attempts would show every
// cold visitor the API-down screen for a server that was merely waking.
export const useHealth = () =>
  useQuery({
    queryKey: ["health"], queryFn: api.health, ...STATIC,
    // Two minutes of patience in production, milliseconds in tests: the
    // API-down screen is still a real state the suite has to be able to reach.
    retry: import.meta.env.MODE === "test" ? 2 : 24,
    retryDelay: (attempt) =>
      import.meta.env.MODE === "test" ? 5 : Math.min(1500 * (attempt + 1), 5000),
  });
export const useVintage = () => useQuery({ queryKey: ["vintage"], queryFn: api.vintage, ...STATIC });
export const useConstants = () => useQuery({ queryKey: ["constants"], queryFn: api.constants, ...STATIC });
export const usePersonas = () => useQuery({ queryKey: ["personas"], queryFn: api.personas, ...STATIC });
export const usePresets = () => useQuery({ queryKey: ["presets"], queryFn: api.presets, ...STATIC });
export const useRedlines = () => useQuery({ queryKey: ["redlines"], queryFn: api.redlines, ...STATIC });

/** Debounced value: trails `value` by `ms` (spec §3: MC debounced 400 ms). */
export function useDebounced<T>(value: T, ms: number): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const t = setTimeout(() => setDebounced(value), ms);
    return () => clearTimeout(t);
  }, [value, ms]);
  return debounced;
}

/** Monte Carlo fan — server-side by design (handoff note 1). Cancel-previous via query key + signal. */
export function useMonteCarlo(levers: Levers, enabled: boolean) {
  const debouncedLevers = useDebounced(levers, 400);
  return useQuery({
    queryKey: ["montecarlo", debouncedLevers],
    queryFn: ({ signal }) =>
      api.montecarlo({ levers: debouncedLevers, seed: 42, n_paths: 4000, horizon: 2070 }, signal),
    enabled,
    staleTime: Infinity,
    placeholderData: keepPreviousData,
  });
}

export function useSensitivity(levers?: Levers) {
  const debouncedLevers = useDebounced(levers, 400);
  return useQuery({
    queryKey: ["sensitivity", debouncedLevers],
    queryFn: ({ signal }) =>
      api.sensitivity(debouncedLevers ? { levers: debouncedLevers } : undefined, signal),
    staleTime: Infinity,
    placeholderData: keepPreviousData,
  });
}

/** Narrated explanation of the current scenario.
 *
 *  Debounced at 400 ms like the Monte Carlo fan, for the same reason and one
 *  more: dragging a slider must not fire one billed LLM call per pixel. The
 *  query key is the lever vector, so React Query serves a repeat of any
 *  scenario the user has already seen from cache with no request at all. */
export function useExplain(levers: Levers, horizon: number, enabled = true) {
  const debouncedLevers = useDebounced(levers, 400);
  const debouncedHorizon = useDebounced(horizon, 400);
  return useQuery({
    queryKey: ["explain", debouncedLevers, debouncedHorizon],
    queryFn: ({ signal }) =>
      api.explain({ levers: debouncedLevers, horizon: debouncedHorizon }, signal),
    enabled,
    staleTime: Infinity,
    placeholderData: keepPreviousData,
  });
}
