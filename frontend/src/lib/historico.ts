/** Spain's record general-government spending: 51,4 % of GDP in 2020, the
 *  COVID year. From the frozen vintage, data/gold/kpis_perfiles.json ·
 *  gasto_total_pib_hist (Eurostat gov_10a_exp). A test reads the gold file
 *  and fails if this and the data ever disagree. */
export const GTOT_RECORD = { value: 51.4, year: 2020 };

/** First year the scenario's total spending passes the record, or null if
 *  it never does. Spending now grows with pensions and interest, so on the
 *  base scenario this is 2038. */
export function recordCrossing(years: number[], gtot: number[]): number | null {
  const k = gtot.findIndex((v) => v > GTOT_RECORD.value);
  return k >= 0 ? years[k] : null;
}
