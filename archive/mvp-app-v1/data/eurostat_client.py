import time
from typing import Dict

import requests

from data.models import FetchResult

EUROSTAT_BASE = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data"


def fetch_indicator(country_iso2: str, dataset_id: str, dims: Dict[str, str], timeout: int = 20) -> FetchResult:
    url = f"{EUROSTAT_BASE}/{dataset_id}"
    params = {**dims, "geo": country_iso2, "format": "JSON", "lang": "EN"}
    try:
        resp = requests.get(url, params=params, timeout=timeout)
        resp.raise_for_status()
        payload = resp.json()
    except Exception as exc:
        return FetchResult(values={}, source="eurostat", from_cache=False, fetched_at=time.time(), error=str(exc))

    try:
        time_dim = payload["dimension"]["time"]["category"]["index"]
        time_positions = sorted(time_dim.items(), key=lambda kv: kv[1])
        raw_values = payload["value"]
    except (KeyError, TypeError) as exc:
        return FetchResult(values={}, source="eurostat", from_cache=False, fetched_at=time.time(),
                            error=f"unexpected JSON-stat shape: {exc}")

    # Normalize raw_values: if it's a list (dense cube), convert to dict {index: value}
    if isinstance(raw_values, list):
        raw_values = {str(i): v for i, v in enumerate(raw_values)}

    values: Dict[int, float] = {}
    for year_str, position in time_positions:
        try:
            v = raw_values.get(str(position))
            if v is not None:
                values[int(year_str)] = float(v)
        except (KeyError, TypeError, ValueError, AttributeError):
            # Skip malformed entries; keep valid ones
            continue

    if not values:
        return FetchResult(values={}, source="eurostat", from_cache=False, fetched_at=time.time(),
                            error="no observations for this geo/dimension combination")

    return FetchResult(values=values, source="eurostat", from_cache=False, fetched_at=time.time(), error=None)
