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


from data import worldbank_client


def _mock_response(payload):
    mock = MagicMock()
    mock.json.return_value = payload
    mock.raise_for_status = MagicMock()
    return mock


def test_worldbank_client_parses_valid_payload():
    payload = [
        {"page": 1, "pages": 1, "total": 2},
        [{"date": "2022", "value": 100.5}, {"date": "2021", "value": None}],
    ]
    with patch("data.worldbank_client.requests.get", return_value=_mock_response(payload)):
        result = worldbank_client.fetch_indicator("ESP", "GC.DOD.TOTL.GD.ZS", 2021, 2022)
    assert result.available
    assert result.values == {2022: 100.5}


def test_worldbank_client_returns_na_sentinel_when_indicator_missing():
    payload = {"message": [{"id": "175", "value": "The indicator was not found."}]}
    with patch("data.worldbank_client.requests.get", return_value=_mock_response(payload)):
        result = worldbank_client.fetch_indicator("ESP", "BOGUS.CODE", 2021, 2022)
    assert not result.available
    assert result.error is not None


def test_worldbank_client_handles_network_error():
    with patch("data.worldbank_client.requests.get", side_effect=ConnectionError("boom")):
        result = worldbank_client.fetch_indicator("ESP", "GC.DOD.TOTL.GD.ZS", 2021, 2022)
    assert not result.available
    assert "boom" in result.error


def test_worldbank_client_skips_malformed_rows():
    payload = [
        {"page": 1, "pages": 1, "total": 2},
        [{"value": 100.5}, {"date": "2021", "value": 85.3}],  # first row missing "date"
    ]
    with patch("data.worldbank_client.requests.get", return_value=_mock_response(payload)):
        result = worldbank_client.fetch_indicator("ESP", "GC.DOD.TOTL.GD.ZS", 2021, 2022)
    assert result.available
    assert result.values == {2021: 85.3}  # only valid row parsed, malformed row skipped
