import json
import time
from pathlib import Path
from typing import Optional

from data.live.models import FetchResult


class DiskCache:
    def __init__(self, cache_dir: str = "data_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, country_iso3: str, indicator_key: str) -> Path:
        return self.cache_dir / country_iso3 / f"{indicator_key}.json"

    def get(self, country_iso3: str, indicator_key: str) -> Optional[FetchResult]:
        path = self._path(country_iso3, indicator_key)
        if not path.exists():
            return None
        raw = json.loads(path.read_text())
        return FetchResult(
            values={int(k): v for k, v in raw["values"].items()},
            source=raw["source"],
            from_cache=True,
            fetched_at=raw["fetched_at"],
            error=None,
        )

    def set(self, country_iso3: str, indicator_key: str, result: FetchResult) -> None:
        if not result.available:
            return
        path = self._path(country_iso3, indicator_key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({
            "values": result.values,
            "source": result.source,
            "fetched_at": result.fetched_at or time.time(),
        }))
