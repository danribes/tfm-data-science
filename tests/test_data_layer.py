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


from data import eurostat_client


def test_eurostat_client_parses_jsonstat_payload():
    payload = {
        "dimension": {"time": {"category": {"index": {"2021": 0, "2022": 1}}}},
        "value": {"0": 100.0, "1": 180.6},
    }
    with patch("data.eurostat_client.requests.get", return_value=_mock_response(payload)):
        result = eurostat_client.fetch_indicator("ES", "prc_hpi_a", {"unit": "I15_A_AVG"})
    assert result.available
    assert result.values == {2021: 100.0, 2022: 180.6}


def test_eurostat_client_returns_na_when_no_observations():
    payload = {"dimension": {"time": {"category": {"index": {}}}}, "value": {}}
    with patch("data.eurostat_client.requests.get", return_value=_mock_response(payload)):
        result = eurostat_client.fetch_indicator("ZZ", "prc_hpi_a", {"unit": "I15_A_AVG"})
    assert not result.available


def test_eurostat_client_skips_malformed_values():
    payload = {
        "dimension": {"time": {"category": {"index": {"2021": 0, "2022": 1}}}},
        "value": {"0": "not_a_number", "1": 150.5},  # first value malformed, second valid
    }
    with patch("data.eurostat_client.requests.get", return_value=_mock_response(payload)):
        result = eurostat_client.fetch_indicator("ES", "prc_hpi_a", {"unit": "I15_A_AVG"})
    assert result.available
    assert result.values == {2022: 150.5}  # only valid value parsed, malformed value skipped


def test_eurostat_client_handles_dense_cube_list_form():
    # JSON-stat 2.0 permits dense-cube form where value is a list instead of dict
    payload = {
        "dimension": {"time": {"category": {"index": {"2021": 0, "2022": 1}}}},
        "value": [100.0, 180.6],  # dense form: list instead of dict
    }
    with patch("data.eurostat_client.requests.get", return_value=_mock_response(payload)):
        result = eurostat_client.fetch_indicator("ES", "prc_hpi_a", {"unit": "I15_A_AVG"})
    assert result.available
    assert result.values == {2021: 100.0, 2022: 180.6}  # dense list parsed correctly


def test_worldbank_client_skips_non_dict_observations():
    payload = [
        {"page": 1, "pages": 1, "total": 2},
        ["not_a_dict", {"date": "2021", "value": 85.3}],  # first element non-dict, second valid
    ]
    with patch("data.worldbank_client.requests.get", return_value=_mock_response(payload)):
        result = worldbank_client.fetch_indicator("ESP", "GC.DOD.TOTL.GD.ZS", 2021, 2022)
    assert result.available
    assert result.values == {2021: 85.3}  # only valid observation parsed, non-dict skipped


from data import oecd_client


def test_oecd_client_parses_sdmx_payload():
    payload = {
        "data": {
            "structures": [{"dimensions": {"observation": [{"values": [{"id": "2021"}, {"id": "2022"}]}]}}],
            "dataSets": [{"series": {"0:0:0:0:0:0:0:0": {"observations": {"0": [1234.5], "1": [1300.0]}}}}],
        }
    }
    with patch("data.oecd_client.requests.get", return_value=_mock_response(payload)):
        result = oecd_client.fetch_indicator(
            "ESP", "OECD.EDU.IMEP", "DSD_EAG_UOE_FIN@DF_UOE_INDIC_FIN_PERSTUD", "3.2",
            {"MEASURE": "FIN_PERSTUD"}, ["MEASURE"],
        )
    assert result.available
    assert result.values == {2021: 1234.5, 2022: 1300.0}


def test_oecd_client_returns_na_when_no_series():
    payload = {
        "data": {
            "structures": [{"dimensions": {"observation": [{"values": []}]}}],
            "dataSets": [{"series": {}}],
        }
    }
    with patch("data.oecd_client.requests.get", return_value=_mock_response(payload)):
        result = oecd_client.fetch_indicator(
            "ZZZ", "OECD.EDU.IMEP", "DSD_EAG_UOE_FIN@DF_UOE_INDIC_FIN_PERSTUD", "3.2",
            {"MEASURE": "FIN_PERSTUD"}, ["MEASURE"],
        )
    assert not result.available


def test_oecd_client_skips_malformed_observations():
    # One malformed observation (invalid index) and one valid observation
    payload = {
        "data": {
            "structures": [{"dimensions": {"observation": [{"values": [{"id": "2021"}, {"id": "2022"}]}]}}],
            "dataSets": [{"series": {"0:0:0:0:0:0:0:0": {"observations": {"999": [1234.5], "1": [1300.0]}}}}],  # 999 is invalid index
        }
    }
    with patch("data.oecd_client.requests.get", return_value=_mock_response(payload)):
        result = oecd_client.fetch_indicator(
            "ESP", "OECD.EDU.IMEP", "DSD_EAG_UOE_FIN@DF_UOE_INDIC_FIN_PERSTUD", "3.2",
            {"MEASURE": "FIN_PERSTUD"}, ["MEASURE"],
        )
    assert result.available
    assert result.values == {2022: 1300.0}  # only valid observation parsed, malformed skipped
