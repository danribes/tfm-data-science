import { useCallback, useRef } from "react";
import { nf } from "../lib/fmt";
import { LEVER_SPECS, isMoved, type LeverId } from "../engine/levers";
import { VINTAGE } from "../engine/vintage";
import { HORIZON_YEARS, useScenarioStore } from "../state/scenarioStore";
import { PresetBar } from "./PresetBar";

const THROTTLE_MS = 60;

/** Throttle with BOTH edges, per lever id, keyed so two levers moved in the
 *  same window never clobber each other's pending value. The trailing flush
 *  is load-bearing: a leading-only throttle would drop the last change of a
 *  drag whenever it landed inside the window, leaving the slider showing one
 *  value while the engine computed another.
 *
 *  Why: `startUrlSync` (Task 7) subscribes to the whole store with no
 *  selector and no debounce, so every `setLever` call fires a synchronous
 *  `history.replaceState`. A native range input's onChange fires on every
 *  pointer-move pixel while dragging, which would otherwise thrash the URL
 *  bar. The first change in a burst commits immediately (so the store and
 *  the readout update in the same tick a user — or a test — expects), and
 *  any changes that land inside the window collapse into one trailing
 *  commit once it elapses, so a full drag gesture reduces to a handful of
 *  writes instead of one per pixel. */
function useThrottledLeverSet(setLever: (id: LeverId, value: number) => void, wait = THROTTLE_MS) {
  const entries = useRef(
    new Map<LeverId, { last: number; timer: ReturnType<typeof setTimeout> | null; pending: number | null }>()
  );
  return useCallback(
    (id: LeverId, value: number) => {
      const map = entries.current;
      let entry = map.get(id);
      if (!entry) {
        entry = { last: 0, timer: null, pending: null };
        map.set(id, entry);
      }
      const now = Date.now();
      if (now - entry.last >= wait) {
        entry.last = now;
        entry.pending = null;
        setLever(id, value);
      } else {
        entry.pending = value;
        if (entry.timer === null) {
          const delay = wait - (now - entry.last);
          entry.timer = setTimeout(() => {
            entry!.timer = null;
            if (entry!.pending !== null) {
              entry!.last = Date.now();
              setLever(id, entry!.pending);
              entry!.pending = null;
            }
          }, delay);
        }
      }
    },
    [setLever, wait]
  );
}

export function LeverRail({ hotIds = [] }: { hotIds?: string[] }) {
  const levers = useScenarioStore((s) => s.levers);
  const horizon = useScenarioStore((s) => s.horizon);
  const setLever = useScenarioStore((s) => s.setLever);
  const setHorizon = useScenarioStore((s) => s.setHorizon);
  const resetAll = useScenarioStore((s) => s.resetAll);
  const commitLever = useThrottledLeverSet(setLever);
  return (
    <aside className="rail" aria-label="Palancas del escenario">
      <h4 style={{ margin: 0, fontSize: 12 }}>Palancas · variables independientes</h4>
      <PresetBar />
      <div className="levers">
        {LEVER_SPECS.map((s) => (
          <div className={hotIds.includes(s.id) ? "lev hot" : "lev"} id={`lev-${s.id}`} key={s.id}>
            <div className="l1">
              <span className="sym">{s.sym}</span>
              <span className="nm">{s.nm}</span>
              <span className={isMoved(levers, s.id) ? "vv moved" : "vv"}>
                {nf(levers[s.id], s.dec)} {s.unit}
              </span>
            </div>
            <input
              type="range"
              aria-label={s.nm}
              min={s.min}
              max={s.max}
              step={s.step}
              value={levers[s.id]}
              onChange={(e) => commitLever(s.id, Number.parseFloat(e.target.value))}
            />
            <div className="src">{s.src}</div>
          </div>
        ))}
      </div>
      <div className="horiz" role="group" aria-label="Horizonte">
        {HORIZON_YEARS.map((y) => (
          <button
            key={y}
            type="button"
            className={y === horizon ? "hb on" : "hb"}
            onClick={() => setHorizon(y)}
          >
            {y}
          </button>
        ))}
      </div>
      <button type="button" className="ps" onClick={resetAll}>
        ↺ volver a base
      </button>
      <div className="src" style={{ whiteSpace: "normal" }}>
        Motor v16 · constantes congeladas del vintage {VINTAGE} · el escenario te sigue entre páginas
      </div>
    </aside>
  );
}
