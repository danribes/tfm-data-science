import { SERIES_KEYS, type Scenario, type SeriesKey } from "./spain";

export type DerivedKey = "ipvreal";
export type AnySeriesKey = SeriesKey | DerivedKey;

/** v16 front-derived series: real house-price growth = nominal IPV − HICP (handoff note 3). */
export function ipvreal(scn: Scenario): number[] {
  return scn.ipv.map((v, i) => v - scn.pi[i]);
}

export function seriesOf(scn: Scenario, key: AnySeriesKey): number[] {
  return key === "ipvreal" ? ipvreal(scn) : scn[key];
}

export const ALL_SERIES_KEYS: AnySeriesKey[] = [...SERIES_KEYS, "ipvreal"];
