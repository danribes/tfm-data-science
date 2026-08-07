import { QueryClientProvider } from "@tanstack/react-query";
import { act, renderHook } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { API_BASE } from "../client";
import { queryClient, useMonteCarlo } from "../hooks";
import { BASE_LEVERS } from "../../engine/vintage";
import { server } from "../../test/msw/server";
import { MOCK_VINTAGE, mockPercentiles } from "../../test/msw/fixtures";

// NOTE: this suite uses vi.useFakeTimers(), so RTL's `waitFor` (which polls via
// real setTimeout/setInterval and only special-cases Jest's fake timers) would
// hang forever. Every assertion below is driven by explicit, act-wrapped
// `vi.advanceTimersByTimeAsync()` calls instead.

const META = { vintage: MOCK_VINTAGE, computed_not_advice: true };
const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
);

describe("useMonteCarlo — debounce + cancel-previous (deferred from Task 6)", () => {
  beforeEach(() => {
    queryClient.clear();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("debounces lever changes by 400 ms before firing the request", async () => {
    let requestCount = 0;
    server.use(
      http.post(`${API_BASE}/scenario/montecarlo`, () => {
        requestCount += 1;
        const years = [2026, 2030, 2050, 2070];
        return HttpResponse.json({
          ...META, years, percentiles: mockPercentiles(years), n_paths: 4000, seed: 42,
        });
      }),
    );

    const { rerender } = renderHook(({ levers }) => useMonteCarlo(levers, true), {
      initialProps: { levers: BASE_LEVERS },
      wrapper,
    });

    // The initial mount's debounced value equals the first `value` synchronously
    // (useState(value) seeds immediately), so the first request fires right away —
    // let it settle before probing the delay behaviour on a subsequent change.
    await act(async () => {
      await vi.advanceTimersByTimeAsync(50);
    });
    expect(requestCount).toBe(1);

    // Move a lever: the debounced value must NOT update — and no new request must
    // fire — until 400 ms have elapsed.
    rerender({ levers: { ...BASE_LEVERS, r: BASE_LEVERS.r + 1 } });
    await act(async () => {
      await vi.advanceTimersByTimeAsync(399);
    });
    expect(requestCount).toBe(1);

    await act(async () => {
      await vi.advanceTimersByTimeAsync(1);
    });
    expect(requestCount).toBe(2);
  });

  it("aborts a superseded in-flight request instead of letting it race the new one", async () => {
    const signals: AbortSignal[] = [];
    let releaseFirst: (() => void) | undefined;
    const firstGate = new Promise<void>((resolve) => { releaseFirst = resolve; });
    let requestCount = 0;

    server.use(
      http.post(`${API_BASE}/scenario/montecarlo`, async ({ request }) => {
        requestCount += 1;
        signals.push(request.signal);
        if (requestCount === 1) await firstGate; // hold the first request open
        const years = [2026, 2030, 2050, 2070];
        return HttpResponse.json({
          ...META, years, percentiles: mockPercentiles(years), n_paths: 4000, seed: 42,
        });
      }),
    );

    const { rerender } = renderHook(({ levers }) => useMonteCarlo(levers, true), {
      initialProps: { levers: BASE_LEVERS },
      wrapper,
    });

    // First request fires on mount (debounced value === initial value already).
    await act(async () => {
      await vi.advanceTimersByTimeAsync(10);
    });
    expect(signals.length).toBe(1);
    expect(signals[0].aborted).toBe(false);

    // Move a lever and let the debounce elapse — this switches the query's
    // observer to a new (different) queryKey while request #1 is still pending,
    // which must abort request #1's signal rather than race it.
    rerender({ levers: { ...BASE_LEVERS, r: BASE_LEVERS.r + 1 } });
    await act(async () => {
      await vi.advanceTimersByTimeAsync(400);
    });

    expect(signals.length).toBe(2);
    expect(signals[0].aborted).toBe(true);

    releaseFirst?.();
  });
});
