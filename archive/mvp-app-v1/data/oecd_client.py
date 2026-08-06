import time
from typing import Dict, List

import requests

from data.models import FetchResult

OECD_BASE = "https://sdmx.oecd.org/public/rest/data"


def fetch_indicator(country_iso3: str, agency: str, dataflow_id: str, version: str,
                     dims: Dict[str, str], dim_order: List[str], timeout: int = 20) -> FetchResult:
    key = ".".join([country_iso3] + [dims[d] for d in dim_order])
    url = f"{OECD_BASE}/{agency},{dataflow_id},{version}/{key}"
    params = {"format": "jsondata"}
    try:
        resp = requests.get(url, params=params, timeout=timeout)
        resp.raise_for_status()
        payload = resp.json()
    except Exception as exc:
        return FetchResult(values={}, source="oecd", from_cache=False, fetched_at=time.time(), error=str(exc))

    try:
        structures = payload["data"]["structures"][0]
        time_values = [v["id"] for v in structures["dimensions"]["observation"][0]["values"]]
        datasets = payload["data"]["dataSets"][0]
        series = datasets["series"]
        if not series:
            return FetchResult(values={}, source="oecd", from_cache=False, fetched_at=time.time(),
                                error="no series returned for this country/dimension combination")
        series_key = next(iter(series))
        observations = series[series_key]["observations"]
        if not isinstance(observations, dict):
            raise TypeError("observations must be a dict")
    except (KeyError, IndexError, TypeError, AttributeError) as exc:
        return FetchResult(values={}, source="oecd", from_cache=False, fetched_at=time.time(),
                            error=f"unexpected SDMX-JSON shape: {exc}")

    values: Dict[int, float] = {}
    for idx_str, obs in observations.items():
        try:
            year = int(time_values[int(idx_str)])
            if obs and obs[0] is not None:
                values[year] = float(obs[0])
        except (KeyError, TypeError, ValueError, AttributeError, IndexError):
            # Skip malformed observations; keep valid ones
            continue

    if not values:
        return FetchResult(values={}, source="oecd", from_cache=False, fetched_at=time.time(),
                            error="series present but all observations null")

    return FetchResult(values=values, source="oecd", from_cache=False, fetched_at=time.time(), error=None)
