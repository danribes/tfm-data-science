from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class FetchResult:
    values: Dict[int, float]       # year -> value
    source: str                    # "worldbank" | "eurostat" | "oecd"
    from_cache: bool
    fetched_at: Optional[float] = None
    error: Optional[str] = None

    @property
    def available(self) -> bool:
        return len(self.values) > 0 and self.error is None
