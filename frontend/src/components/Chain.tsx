import { nf, sg } from "../lib/fmt";
import type { Scenario, SeriesKey } from "../engine/spain";

export interface ChainSpec {
  a: string;
  u: string;
  t: string;
  k: SeriesKey;
  d: number;
  un: string;
}

const EPS = 1e-9;

export function Chain({
  specs,
  scn,
  base,
  k,
}: {
  specs: ChainSpec[];
  scn: Scenario;
  base: Scenario;
  k: number;
}) {
  return (
    <div className="chain">
      {specs.map((c) => {
        const value = scn[c.k][k];
        const delta = value - base[c.k][k];
        const dir = delta > EPS ? "up" : delta < -EPS ? "dn" : "flat";
        return (
          <div className="ch" key={c.k + c.t}>
            <span className="a">{c.a}</span>
            <span className="arr">→</span>
            <span className="u">{c.u}</span>
            <span className="arr">→</span>
            {c.t}
            <span className={`d ${dir}`}>
              {nf(value, c.d)} {c.un} ({sg(delta, c.d)})
            </span>
          </div>
        );
      })}
    </div>
  );
}
