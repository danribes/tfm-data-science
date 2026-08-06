"""
Builds the offline training panel for the fiscal-stress model: joins the World
Bank macro panel (2003-2015, the WGI annual-coverage window) for countries
present in the Reinhart-Rogoff-Trebesch "Global Crises Data by Country"
dataset. The debt-distress label is derived from that dataset's
Domestic_Debt_In_Default and sovereign external debt default/restructuring
columns.

Run once, offline: `python scripts/build_training_panel.py`
Writes: data_cache/training_panel.csv

Not imported by the app -- development-time tooling only.
"""
import csv
import io
from pathlib import Path

import openpyxl
import requests

from data.cache import DiskCache
from data.panel_builder import fetch_one, load_catalog
from data.country_list import load_country_list

CRISIS_DATA_URL = (
    "https://www.hbs.edu/behavioral-finance-and-financial-stability/"
    "Documents/ChartData/MapCharts/20160923_global_crisis_data.xlsx"
)
TRAIN_START_YEAR = 2003
TRAIN_END_YEAR = 2015
OUTPUT_PATH = Path("data_cache/training_panel.csv")
FEATURES = [
    "debt_gdp", "gdp_growth", "inflation", "unemployment",
    "real_interest_rate", "net_lending_borrowing", "corruption_control",
]


def download_crisis_labels(timeout: int = 30) -> dict:
    """Returns {(iso3, year): label}; label=1 if that country-year is flagged as a
    domestic or external sovereign debt default/restructuring in the
    Reinhart-Rogoff-Trebesch dataset, else 0."""
    resp = requests.get(CRISIS_DATA_URL, timeout=timeout)
    resp.raise_for_status()
    wb = openpyxl.load_workbook(io.BytesIO(resp.content), read_only=True, data_only=True)
    ws = wb["Sheet1"]

    labels = {}
    for row in ws.iter_rows(min_row=2, values_only=True):
        iso3, year = row[1], row[3]
        if iso3 is None or year is None:
            continue
        domestic_default = row[16]
        external_default = row[18]
        is_distress = 1 if (domestic_default == 1 or external_default == 1) else 0
        if TRAIN_START_YEAR <= year <= TRAIN_END_YEAR:
            labels[(iso3, int(year))] = is_distress
    return labels


def build_training_panel() -> None:
    labels = download_crisis_labels()
    label_countries = {iso3 for (iso3, _year) in labels}
    wb_countries = {c["iso3"] for c in load_country_list()}
    target_countries = sorted(label_countries & wb_countries)

    catalog = load_catalog()
    cache = DiskCache()

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["country_iso3", "year", "label", *FEATURES])

        for iso3 in target_countries:
            panel = {key: fetch_one(iso3, key, catalog[key], TRAIN_START_YEAR, TRAIN_END_YEAR, cache)
                      for key in FEATURES}
            for year in range(TRAIN_START_YEAR, TRAIN_END_YEAR + 1):
                label = labels.get((iso3, year))
                if label is None:
                    continue
                row_values = [panel[k].values.get(year) for k in FEATURES]
                if any(v is None for v in row_values):
                    continue
                writer.writerow([iso3, year, label, *row_values])

    print(f"wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    build_training_panel()
