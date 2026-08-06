from data.cache import DiskCache
from data.models import FetchResult


def test_disk_cache_round_trip(tmp_path):
    cache = DiskCache(cache_dir=str(tmp_path))
    result = FetchResult(values={2022: 50.0}, source="worldbank", from_cache=False, fetched_at=1700000000.0)
    cache.set("ESP", "debt_gdp", result)
    loaded = cache.get("ESP", "debt_gdp")
    assert loaded is not None
    assert loaded.values == {2022: 50.0}
    assert loaded.from_cache is True


def test_disk_cache_miss_returns_none(tmp_path):
    cache = DiskCache(cache_dir=str(tmp_path))
    assert cache.get("ESP", "debt_gdp") is None


from unittest.mock import patch, MagicMock
from data.country_list import fetch_country_list


def test_fetch_country_list_filters_aggregates():
    payload = [
        {"page": 1},
        [
            {"id": "ESP", "iso2Code": "ES", "name": "Spain", "region": {"id": "ECS", "value": "Europe & Central Asia"}},
            {"id": "WLD", "iso2Code": "1W", "name": "World", "region": {"id": "NA", "value": "Aggregates"}},
        ],
    ]
    mock = MagicMock()
    mock.json.return_value = payload
    mock.raise_for_status = MagicMock()
    with patch("data.country_list.requests.get", return_value=mock):
        countries = fetch_country_list()
    assert countries == [{"iso3": "ESP", "iso2": "ES", "name": "Spain", "region": "Europe & Central Asia"}]
