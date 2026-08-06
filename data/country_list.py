import json
from pathlib import Path
from typing import Dict, List

import requests

WORLD_BANK_BASE = "https://api.worldbank.org/v2"
COUNTRY_LIST_CACHE = Path("data_cache/_country_list.json")


def fetch_country_list(timeout: int = 30) -> List[dict]:
    resp = requests.get(f"{WORLD_BANK_BASE}/country", params={"format": "json", "per_page": 400}, timeout=timeout)
    resp.raise_for_status()
    payload = resp.json()
    countries = payload[1]
    # region.id == "NA" marks aggregates ("World", "OECD members", ...), not real countries
    return [
        {"iso3": c["id"], "iso2": c["iso2Code"], "name": c["name"], "region": c["region"]["value"]}
        for c in countries
        if c["region"]["id"] != "NA"
    ]


def load_country_list() -> List[dict]:
    if COUNTRY_LIST_CACHE.exists():
        return json.loads(COUNTRY_LIST_CACHE.read_text())
    countries = fetch_country_list()
    COUNTRY_LIST_CACHE.parent.mkdir(parents=True, exist_ok=True)
    COUNTRY_LIST_CACHE.write_text(json.dumps(countries))
    return countries


def iso3_to_iso2_map() -> Dict[str, str]:
    return {c["iso3"]: c["iso2"] for c in load_country_list()}
