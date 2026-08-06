import time
from pathlib import Path
from typing import Dict

import yaml

from data.live.models import FetchResult
from data.live.cache import DiskCache
from data.live.country_list import iso3_to_iso2_map
from data.live import worldbank_client, eurostat_client, oecd_client

CATALOG_PATH = Path(__file__).parent / "indicator_catalog.yaml"


def load_catalog() -> dict:
    return yaml.safe_load(CATALOG_PATH.read_text())["indicators"]


def fetch_one(country_iso3: str, indicator_key: str, spec: dict, start_year: int, end_year: int,
              cache: DiskCache, force_refresh: bool = False) -> FetchResult:
    if not force_refresh:
        cached = cache.get(country_iso3, indicator_key)
        if cached is not None:
            return cached

    result = None
    for source in spec["sources"]:
        stype = source["type"]

        if stype == "worldbank":
            result = worldbank_client.fetch_indicator(country_iso3, source["code"], start_year, end_year)
        elif stype == "eurostat":
            iso2 = iso3_to_iso2_map().get(country_iso3)
            if iso2 is None:
                result = FetchResult(values={}, source="eurostat", from_cache=False, fetched_at=time.time(),
                                      error="no ISO2 code found for this country")
            else:
                result = eurostat_client.fetch_indicator(iso2, source["dataset_id"], source["dims"])
        elif stype == "oecd":
            result = oecd_client.fetch_indicator(country_iso3, source["agency"], source["dataflow_id"],
                                                  source["version"], source["dims"], source["dim_order"])
        else:
            result = FetchResult(values={}, source=stype, from_cache=False, fetched_at=time.time(),
                                  error=f"unknown source type: {stype}")

        if result.available:
            cache.set(country_iso3, indicator_key, result)
            return result

    # No source succeeded; return the last attempted source's failure so the error
    # reflects a real attempt (never fabricated), matching the single-source contract.
    return result


def build_country_panel(country_iso3: str, start_year: int = 2000, end_year: int = 2024,
                         cache: DiskCache = None, force_refresh: bool = False) -> Dict[str, FetchResult]:
    cache = cache or DiskCache()
    catalog = load_catalog()
    panel = {}
    for key, spec in catalog.items():
        panel[key] = fetch_one(country_iso3, key, spec, start_year, end_year, cache, force_refresh)
    return panel


def coverage_score(panel: Dict[str, FetchResult]) -> float:
    if not panel:
        return 0.0
    available = sum(1 for r in panel.values() if r.available)
    return available / len(panel)
