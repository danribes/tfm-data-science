import { nf, sg } from "../lib/fmt";
import { useRollup } from "../lib/motion";
import type { Scenario } from "../engine/spain";
import type { PersonaRedOut } from "../api/types";
import { Gauge, dialDomain } from "./Gauge";
import { Stamp } from "./Stamp";

/** Display format per engine series (decimals, unit suffix). */
export const SERIES_FORMAT: Record<string, { dec: number; unit: string }> = {
  lvl: { dec: 2, unit: "%" }, u: { dec: 1, unit: "%" }, pi: { dec: 1, unit: "%" },
  g: { dec: 1, unit: "%" }, gnom: { dec: 1, unit: "%" }, wnom: { dec: 1, unit: "%" },
  wreal: { dec: 1, unit: "%" }, wrealIdx: { dec: 1, unit: "" }, b: { dec: 1, unit: "%PIB" },
  ief: { dec: 2, unit: "%" }, int: { dec: 1, unit: "%PIB" }, pb: { dec: 1, unit: "%PIB" },
  saldo: { dec: 1, unit: "%PIB" }, ipv: { dec: 1, unit: "% a/a" }, precio: { dec: 0, unit: "€" },
  cuota: { dec: 0, unit: "€/mes" }, salmes: { dec: 0, unit: "€/mes" }, salario: { dec: 0, unit: "€/año" },
  esf: { dec: 1, unit: "%" }, pens: { dec: 2, unit: "%PIB" }, dep: { dec: 1, unit: "/100" },
  arop: { dec: 1, unit: "%" }, edu: { dec: 2, unit: "%PIB" }, d1: { dec: 2, unit: "%PIB" },
  nomreal: { dec: 1, unit: "" }, p2: { dec: 2, unit: "%PIB" }, d3: { dec: 2, unit: "%PIB" },
  p51: { dec: 2, unit: "%PIB" }, gtot: { dec: 1, unit: "%PIB" }, bls: { dec: 0, unit: "% neto" },
  temp: { dec: 1, unit: "%" }, ujuv: { dec: 1, unit: "%" }, auton: { dec: 1, unit: "%" },
  hip: { dec: 0, unit: "/año" }, sobre: { dec: 1, unit: "%" }, bono: { dec: 2, unit: "%" },
  spread: { dec: 0, unit: "pb" }, r: { dec: 2, unit: "%" }, deficitAbs: { dec: 1, unit: "%PIB" },
  vida: { dec: 1, unit: "años" }, ipvreal: { dec: 1, unit: "% a/a" },
};

/** Series where a positive delta is bad (red). Everything else: positive = good (green). */
export const UP_IS_BAD = new Set([
  "b", "u", "pi", "cuota", "esf", "int", "bono", "spread", "r", "arop", "dep",
  "pens", "sobre", "temp", "ujuv", "bls", "deficitAbs",
]);

interface TileProps {
  out: { k: string; lab: string };
  scn: Scenario;
  base: Scenario;
  k: number;
  fresh: boolean;
  year: number;
  red?: PersonaRedOut;
}

/** One tile = one component so useRollup (a hook) can animate its figure (spec §5). */
function KpiTile({ out, scn, base, k, fresh, year, red }: TileProps) {
  const key = out.k as keyof Scenario;
  const fmtSpec = SERIES_FORMAT[out.k] ?? { dec: 1, unit: "" };
  const value = scn[key][k];
  const baseValue = base[key][k];
  const shown = useRollup(value); // ~180 ms roll-up on change; exact on first render
  const delta = value - baseValue;
  const [lo, hi] = dialDomain([...base[key], ...scn[key]], red?.thr ?? undefined);
  const deltaClass =
    Math.abs(delta) <= 1e-9 ? "" : (delta > 0) === UP_IS_BAD.has(out.k) ? "bad" : "good";
  return (
    <div className="out">
      <span className="o-seal"><Stamp fresh={fresh} year={year} /></span>
      <div className="o-label">{out.lab}</div>
      <div className="o-val">{nf(shown, fmtSpec.dec)} <small>{fmtSpec.unit}</small></div>
      <div className={`o-delta ${deltaClass}`}>{sg(delta, fmtSpec.dec)} vs base</div>
      <Gauge
        value={value}
        lo={lo}
        hi={hi}
        base={baseValue}
        red={red?.thr ?? undefined}
        redCmp={(red?.cmp as "gt" | "lt") ?? "gt"}
      />
    </div>
  );
}

export function KpiRow({
  outs,
  scn,
  base,
  k,
  fresh,
  year,
  personaReds,
}: {
  outs: { k: string; lab: string }[];
  scn: Scenario;
  base: Scenario;
  k: number;
  fresh: boolean;
  year: number;
  personaReds?: PersonaRedOut[];
}) {
  return (
    <div className="outs">
      {outs.map((o) => (
        <KpiTile
          key={o.k}
          out={o}
          scn={scn}
          base={base}
          k={k}
          fresh={fresh}
          year={year}
          red={personaReds?.find((r) => r.k === o.k)}
        />
      ))}
    </div>
  );
}
