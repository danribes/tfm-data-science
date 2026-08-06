import time
from typing import Dict

import requests

from data.live.models import FetchResult

WORLD_BANK_BASE = "https://api.worldbank.org/v2"


def fetch_indicator(country_iso3: str, wb_code: str, start_year: int, end_year: int, timeout: int = 20) -> FetchResult:
    url = f"{WORLD_BANK_BASE}/country/{country_iso3}/indicator/{wb_code}"
    params = {"format": "json", "per_page": 1000, "date": f"{start_year}:{end_year}"}
    try:
        resp = requests.get(url, params=params, timeout=timeout)
        resp.raise_for_status()
        payload = resp.json()
    except Exception as exc:
        return FetchResult(values={}, source="worldbank", from_cache=False, fetched_at=time.time(), error=str(exc))

    if not isinstance(payload, list) or len(payload) < 2 or payload[1] is None:
        return FetchResult(values={}, source="worldbank", from_cache=False, fetched_at=time.time(),
                            error="no data returned for this country/indicator")

    values: Dict[int, float] = {}
    for row in payload[1]:
        try:
            if row.get("value") is not None:
                values[int(row["date"])] = float(row["value"])
        except (KeyError, TypeError, ValueError, AttributeError):
            # Skip malformed rows; if all rows are malformed, we'll hit the error path below
            continue

    if not values:
        return FetchResult(values={}, source="worldbank", from_cache=False, fetched_at=time.time(),
                            error="indicator has no non-null observations for this country")

    return FetchResult(values=values, source="worldbank", from_cache=False, fetched_at=time.time(), error=None)
