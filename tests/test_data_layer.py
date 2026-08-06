"""Data-layer tests: gold-slice shape checks (Task 1), ported MVP client tests
(Task 2, appended below), refresh_vintage (Task 14, appended below)."""
import csv
import json
from pathlib import Path

import pytest


GOLD = Path(__file__).resolve().parents[1] / "data" / "gold"

GOLD_FILES = [
    "gold_escenarios_deuda.csv", "gold_escenarios_deuda_mc.csv",
    "gold_cuota_teorica.csv", "gold_projections.csv", "gold_ccaa_trimestral.csv",
    "gold_asequibilidad_ccaa.csv", "gold_pobreza_infantil.csv",
    "gold_bienestar_pais.csv", "gold_fiscal_historico.csv",
    "kpis_perfiles.json", "manifest.csv", "provenance_vintage_manifest.csv",
    "VINTAGE",
]


def test_gold_slice_files_committed():
    for name in GOLD_FILES:
        assert (GOLD / name).exists(), f"missing {name}"
    # excluded from phase 1 (spec §3.1): no consumer yet
    assert not (GOLD / "gold_century_fiscal.csv").exists()
    assert not (GOLD / "gold_panel_anual.csv").exists()


def test_vintage_stamp():
    assert (GOLD / "VINTAGE").read_text(encoding="utf-8").strip() == "2026-07-31"


def test_kpis_shape():
    kp = json.loads((GOLD / "kpis_perfiles.json").read_text(encoding="utf-8"))
    assert set(kp) == {"vintage", "fuentes", "kpi", "series"}
    assert kp["vintage"] == "2026-07-31"
    assert len(kp["kpi"]) == 42
    assert len(kp["series"]) == 21
    assert kp["kpi"]["euribor12m"]["valor"] == 2.8
    assert kp["kpi"]["cuota_hipoteca_mediana"]["valor"] == 745


def test_central_scenario_rows():
    rows = [r for r in csv.DictReader((GOLD / "gold_escenarios_deuda.csv").open(encoding="utf-8"))
            if r["escenario"] == "central"]
    years = sorted(int(float(r["year"])) for r in rows)
    assert years[0] == 2024 and years[-1] == 2050 and len(years) == 27
    row_2026 = next(r for r in rows if int(float(r["year"])) == 2026)
    # extract L868: central,2026,106.32,-1.35,2.68,3.3,0.45
    assert row_2026["deuda"] == "106.32"


def test_mc_and_cuota_rows():
    mc = [r for r in csv.DictReader((GOLD / "gold_escenarios_deuda_mc.csv").open(encoding="utf-8"))
          if r["escenario"] == "central"]
    mc_years = {int(float(r["year"])) for r in mc}
    assert {2030, 2050, 2070} <= mc_years
    cuota = list(csv.DictReader((GOLD / "gold_cuota_teorica.csv").open(encoding="utf-8")))
    assert len(cuota) == 17
    navarra = next(r for r in cuota if r["ccaa"].startswith("Navarra"))
    assert navarra["cuota_mensual"] == "744.89"     # extract L932


# ---- ported from archive/mvp-app-v1/tests/test_data_layer.py (30 tests) ----
from data.live.cache import DiskCache
from data.live.models import FetchResult


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
from data.live.country_list import fetch_country_list


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
    with patch("data.live.country_list.requests.get", return_value=mock):
        countries = fetch_country_list()
    assert countries == [{"iso3": "ESP", "iso2": "ES", "name": "Spain", "region": "Europe & Central Asia"}]


from data.live import worldbank_client


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
    with patch("data.live.worldbank_client.requests.get", return_value=_mock_response(payload)):
        result = worldbank_client.fetch_indicator("ESP", "GC.DOD.TOTL.GD.ZS", 2021, 2022)
    assert result.available
    assert result.values == {2022: 100.5}


def test_worldbank_client_returns_na_sentinel_when_indicator_missing():
    payload = {"message": [{"id": "175", "value": "The indicator was not found."}]}
    with patch("data.live.worldbank_client.requests.get", return_value=_mock_response(payload)):
        result = worldbank_client.fetch_indicator("ESP", "BOGUS.CODE", 2021, 2022)
    assert not result.available
    assert result.error is not None


def test_worldbank_client_handles_network_error():
    with patch("data.live.worldbank_client.requests.get", side_effect=ConnectionError("boom")):
        result = worldbank_client.fetch_indicator("ESP", "GC.DOD.TOTL.GD.ZS", 2021, 2022)
    assert not result.available
    assert "boom" in result.error


def test_worldbank_client_skips_malformed_rows():
    payload = [
        {"page": 1, "pages": 1, "total": 2},
        [{"value": 100.5}, {"date": "2021", "value": 85.3}],  # first row missing "date"
    ]
    with patch("data.live.worldbank_client.requests.get", return_value=_mock_response(payload)):
        result = worldbank_client.fetch_indicator("ESP", "GC.DOD.TOTL.GD.ZS", 2021, 2022)
    assert result.available
    assert result.values == {2021: 85.3}  # only valid row parsed, malformed row skipped


from data.live import eurostat_client


def test_eurostat_client_parses_jsonstat_payload():
    payload = {
        "dimension": {"time": {"category": {"index": {"2021": 0, "2022": 1}}}},
        "value": {"0": 100.0, "1": 180.6},
    }
    with patch("data.live.eurostat_client.requests.get", return_value=_mock_response(payload)):
        result = eurostat_client.fetch_indicator("ES", "prc_hpi_a", {"unit": "I15_A_AVG"})
    assert result.available
    assert result.values == {2021: 100.0, 2022: 180.6}


def test_eurostat_client_returns_na_when_no_observations():
    payload = {"dimension": {"time": {"category": {"index": {}}}}, "value": {}}
    with patch("data.live.eurostat_client.requests.get", return_value=_mock_response(payload)):
        result = eurostat_client.fetch_indicator("ZZ", "prc_hpi_a", {"unit": "I15_A_AVG"})
    assert not result.available


def test_eurostat_client_skips_malformed_values():
    payload = {
        "dimension": {"time": {"category": {"index": {"2021": 0, "2022": 1}}}},
        "value": {"0": "not_a_number", "1": 150.5},  # first value malformed, second valid
    }
    with patch("data.live.eurostat_client.requests.get", return_value=_mock_response(payload)):
        result = eurostat_client.fetch_indicator("ES", "prc_hpi_a", {"unit": "I15_A_AVG"})
    assert result.available
    assert result.values == {2022: 150.5}  # only valid value parsed, malformed value skipped


def test_eurostat_client_handles_dense_cube_list_form():
    # JSON-stat 2.0 permits dense-cube form where value is a list instead of dict
    payload = {
        "dimension": {"time": {"category": {"index": {"2021": 0, "2022": 1}}}},
        "value": [100.0, 180.6],  # dense form: list instead of dict
    }
    with patch("data.live.eurostat_client.requests.get", return_value=_mock_response(payload)):
        result = eurostat_client.fetch_indicator("ES", "prc_hpi_a", {"unit": "I15_A_AVG"})
    assert result.available
    assert result.values == {2021: 100.0, 2022: 180.6}  # dense list parsed correctly


def test_worldbank_client_skips_non_dict_observations():
    payload = [
        {"page": 1, "pages": 1, "total": 2},
        ["not_a_dict", {"date": "2021", "value": 85.3}],  # first element non-dict, second valid
    ]
    with patch("data.live.worldbank_client.requests.get", return_value=_mock_response(payload)):
        result = worldbank_client.fetch_indicator("ESP", "GC.DOD.TOTL.GD.ZS", 2021, 2022)
    assert result.available
    assert result.values == {2021: 85.3}  # only valid observation parsed, non-dict skipped


from data.live import oecd_client


def test_oecd_client_parses_sdmx_payload():
    payload = {
        "data": {
            "structures": [{"dimensions": {"observation": [{"values": [{"id": "2021"}, {"id": "2022"}]}]}}],
            "dataSets": [{"series": {"0:0:0:0:0:0:0:0": {"observations": {"0": [1234.5], "1": [1300.0]}}}}],
        }
    }
    with patch("data.live.oecd_client.requests.get", return_value=_mock_response(payload)):
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
    with patch("data.live.oecd_client.requests.get", return_value=_mock_response(payload)):
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
    with patch("data.live.oecd_client.requests.get", return_value=_mock_response(payload)):
        result = oecd_client.fetch_indicator(
            "ESP", "OECD.EDU.IMEP", "DSD_EAG_UOE_FIN@DF_UOE_INDIC_FIN_PERSTUD", "3.2",
            {"MEASURE": "FIN_PERSTUD"}, ["MEASURE"],
        )
    assert result.available
    assert result.values == {2022: 1300.0}  # only valid observation parsed, malformed skipped


def test_oecd_client_handles_missing_observations_key():
    # Series exists but has no "observations" key
    payload = {
        "data": {
            "structures": [{"dimensions": {"observation": [{"values": [{"id": "2021"}, {"id": "2022"}]}]}}],
            "dataSets": [{"series": {"0:0:0:0:0:0:0:0": {}}}],  # series entry missing "observations" key
        }
    }
    with patch("data.live.oecd_client.requests.get", return_value=_mock_response(payload)):
        result = oecd_client.fetch_indicator(
            "ESP", "OECD.EDU.IMEP", "DSD_EAG_UOE_FIN@DF_UOE_INDIC_FIN_PERSTUD", "3.2",
            {"MEASURE": "FIN_PERSTUD"}, ["MEASURE"],
        )
    assert not result.available
    assert "unexpected SDMX-JSON shape" in result.error


def test_oecd_client_handles_non_dict_observations():
    # Series exists but observations is a list instead of dict
    payload = {
        "data": {
            "structures": [{"dimensions": {"observation": [{"values": [{"id": "2021"}, {"id": "2022"}]}]}}],
            "dataSets": [{"series": {"0:0:0:0:0:0:0:0": {"observations": [1234.5, 1300.0]}}}],  # observations is a list, not dict
        }
    }
    with patch("data.live.oecd_client.requests.get", return_value=_mock_response(payload)):
        result = oecd_client.fetch_indicator(
            "ESP", "OECD.EDU.IMEP", "DSD_EAG_UOE_FIN@DF_UOE_INDIC_FIN_PERSTUD", "3.2",
            {"MEASURE": "FIN_PERSTUD"}, ["MEASURE"],
        )
    assert not result.available
    assert "unexpected SDMX-JSON shape" in result.error


from data.live.panel_builder import coverage_score, fetch_one, load_catalog


def test_coverage_score_computes_fraction_available():
    panel = {
        "a": FetchResult(values={2022: 1.0}, source="worldbank", from_cache=False, fetched_at=0.0),
        "b": FetchResult(values={}, source="worldbank", from_cache=False, fetched_at=0.0, error="no data"),
    }
    assert coverage_score(panel) == 0.5


def test_load_catalog_has_expected_keys():
    catalog = load_catalog()
    assert "debt_gdp" in catalog
    assert "government_revenue_gdp" in catalog
    assert catalog["debt_gdp"]["sources"][0]["type"] == "worldbank"


def test_fetch_one_uses_cache_before_network(tmp_path):
    from data.live.cache import DiskCache
    cache = DiskCache(cache_dir=str(tmp_path))
    cached_result = FetchResult(values={2022: 42.0}, source="worldbank", from_cache=False, fetched_at=0.0)
    cache.set("ESP", "debt_gdp", cached_result)

    spec = {"sources": [{"type": "worldbank", "code": "GC.DOD.TOTL.GD.ZS"}]}
    with patch("data.live.worldbank_client.requests.get", side_effect=AssertionError("should not hit network")):
        result = fetch_one("ESP", "debt_gdp", spec, 2000, 2024, cache)
    assert result.values == {2022: 42.0}
    assert result.from_cache is True


# --- Finding 1: routing-branch coverage ---------------------------------------


def test_fetch_one_dispatches_to_eurostat_client(tmp_path):
    from data.live.cache import DiskCache
    cache = DiskCache(cache_dir=str(tmp_path))
    spec = {"sources": [{"type": "eurostat", "dataset_id": "gov_10a_exp", "dims": {"unit": "PC_GDP"}}]}
    available = FetchResult(values={2022: 7.0}, source="eurostat", from_cache=False, fetched_at=0.0)
    with patch("data.live.panel_builder.iso3_to_iso2_map", return_value={"ESP": "ES"}), \
         patch("data.live.eurostat_client.fetch_indicator", return_value=available) as mock_fetch:
        result = fetch_one("ESP", "public_wage_bill_gdp", spec, 2000, 2024, cache)
    mock_fetch.assert_called_once_with("ES", "gov_10a_exp", {"unit": "PC_GDP"})
    assert result.values == {2022: 7.0}


def test_fetch_one_dispatches_to_oecd_client(tmp_path):
    from data.live.cache import DiskCache
    cache = DiskCache(cache_dir=str(tmp_path))
    spec = {
        "sources": [{
            "type": "oecd", "agency": "OECD.EDU.IMEP", "dataflow_id": "DSD_X", "version": "3.2",
            "dims": {"MEASURE": "FIN_PERSTUD"}, "dim_order": ["MEASURE"],
        }]
    }
    available = FetchResult(values={2022: 9.0}, source="oecd", from_cache=False, fetched_at=0.0)
    with patch("data.live.oecd_client.fetch_indicator", return_value=available) as mock_fetch:
        result = fetch_one("ESP", "edu_spend_per_student", spec, 2000, 2024, cache)
    mock_fetch.assert_called_once_with(
        "ESP", "OECD.EDU.IMEP", "DSD_X", "3.2", {"MEASURE": "FIN_PERSTUD"}, ["MEASURE"],
    )
    assert result.values == {2022: 9.0}


def test_fetch_one_missing_iso2_degrades_without_exception(tmp_path):
    from data.live.cache import DiskCache
    cache = DiskCache(cache_dir=str(tmp_path))
    spec = {"sources": [{"type": "eurostat", "dataset_id": "gov_10a_exp", "dims": {"unit": "PC_GDP"}}]}
    with patch("data.live.panel_builder.iso3_to_iso2_map", return_value={}):
        result = fetch_one("ZZZ", "public_wage_bill_gdp", spec, 2000, 2024, cache)
    assert not result.available
    assert "no ISO2 code found" in result.error


def test_fetch_one_unknown_source_type_degrades_without_exception(tmp_path):
    from data.live.cache import DiskCache
    cache = DiskCache(cache_dir=str(tmp_path))
    spec = {"sources": [{"type": "imf", "code": "XX"}]}
    result = fetch_one("ESP", "made_up", spec, 2000, 2024, cache)
    assert not result.available
    assert "unknown source type: imf" in result.error


def test_fetch_one_calls_cache_set_when_result_available():
    mock_cache = MagicMock()
    mock_cache.get.return_value = None
    spec = {"sources": [{"type": "worldbank", "code": "GC.DOD.TOTL.GD.ZS"}]}
    available = FetchResult(values={2022: 1.0}, source="worldbank", from_cache=False, fetched_at=0.0)
    with patch("data.live.worldbank_client.fetch_indicator", return_value=available):
        result = fetch_one("ESP", "debt_gdp", spec, 2000, 2024, mock_cache)
    mock_cache.set.assert_called_once_with("ESP", "debt_gdp", available)
    assert result is available


def test_fetch_one_does_not_call_cache_set_when_result_unavailable():
    mock_cache = MagicMock()
    mock_cache.get.return_value = None
    spec = {"sources": [{"type": "worldbank", "code": "BOGUS.CODE"}]}
    unavailable = FetchResult(values={}, source="worldbank", from_cache=False, fetched_at=0.0, error="no data")
    with patch("data.live.worldbank_client.fetch_indicator", return_value=unavailable):
        result = fetch_one("ESP", "debt_gdp", spec, 2000, 2024, mock_cache)
    mock_cache.set.assert_not_called()
    assert result is unavailable


# --- Finding 2: guarded country-list fetch --------------------------------------


def test_load_country_list_network_failure_no_cache_returns_empty(tmp_path):
    from data.live import country_list
    fake_cache_path = tmp_path / "_country_list.json"
    with patch.object(country_list, "COUNTRY_LIST_CACHE", fake_cache_path), \
         patch("data.live.country_list.requests.get", side_effect=ConnectionError("boom")):
        assert country_list.iso3_to_iso2_map() == {}


def test_fetch_one_eurostat_degrades_when_country_list_fetch_fails(tmp_path):
    from data.live import country_list
    from data.live.cache import DiskCache
    fake_cache_path = tmp_path / "_country_list.json"
    cache = DiskCache(cache_dir=str(tmp_path / "data_cache"))
    spec = {"sources": [{"type": "eurostat", "dataset_id": "gov_10a_exp", "dims": {"unit": "PC_GDP"}}]}
    with patch.object(country_list, "COUNTRY_LIST_CACHE", fake_cache_path), \
         patch("data.live.country_list.requests.get", side_effect=ConnectionError("boom")):
        result = fetch_one("ZZZ", "public_wage_bill_gdp", spec, 2000, 2024, cache)
    assert not result.available
    assert "no ISO2 code found" in result.error


# --- Finding 3: source fallback iteration ---------------------------------------


def test_fetch_one_falls_back_to_second_source_when_primary_unavailable(tmp_path):
    from data.live.cache import DiskCache
    cache = DiskCache(cache_dir=str(tmp_path))
    spec = {
        "sources": [
            {"type": "worldbank", "code": "BOGUS.CODE"},
            {
                "type": "oecd", "agency": "OECD.EDU.IMEP", "dataflow_id": "DSD_X", "version": "3.2",
                "dims": {"MEASURE": "FIN_PERSTUD"}, "dim_order": ["MEASURE"],
            },
        ]
    }
    unavailable = FetchResult(values={}, source="worldbank", from_cache=False, fetched_at=0.0, error="no data")
    available = FetchResult(values={2022: 5.0}, source="oecd", from_cache=False, fetched_at=0.0)
    with patch("data.live.worldbank_client.fetch_indicator", return_value=unavailable), \
         patch("data.live.oecd_client.fetch_indicator", return_value=available):
        result = fetch_one("ESP", "fallback_key", spec, 2000, 2024, cache)
    assert result.values == {2022: 5.0}
    assert result.source == "oecd"
    cached = cache.get("ESP", "fallback_key")
    assert cached is not None
    assert cached.values == {2022: 5.0}


def test_fetch_one_does_not_call_fallback_when_primary_available(tmp_path):
    from data.live.cache import DiskCache
    cache = DiskCache(cache_dir=str(tmp_path))
    spec = {
        "sources": [
            {"type": "worldbank", "code": "GC.DOD.TOTL.GD.ZS"},
            {
                "type": "oecd", "agency": "OECD.EDU.IMEP", "dataflow_id": "DSD_X", "version": "3.2",
                "dims": {"MEASURE": "FIN_PERSTUD"}, "dim_order": ["MEASURE"],
            },
        ]
    }
    available = FetchResult(values={2022: 10.0}, source="worldbank", from_cache=False, fetched_at=0.0)
    with patch("data.live.worldbank_client.fetch_indicator", return_value=available), \
         patch("data.live.oecd_client.fetch_indicator", side_effect=AssertionError("fallback should not be called")):
        result = fetch_one("ESP", "no_fallback_key", spec, 2000, 2024, cache)
    assert result.values == {2022: 10.0}
    assert result.source == "worldbank"


# ---- Task 14: refresh_vintage ----

def test_refresh_vintage_writes_new_dir_and_records_failures(tmp_path):
    from scripts.refresh_vintage import refresh

    manifest = tmp_path / "manifest.csv"
    manifest.write_text(
        "source,url,fetched,bytes,raw_file,processed_file\n"
        "SrcOK,https://example.org/ok.json,2026-07-31,10,ok.json,ok.csv\n"
        "SrcFail,https://example.org/fail.json,2026-07-31,10,fail.json,fail.csv\n")

    class FakeResp:
        content = b"{}"
        def raise_for_status(self):
            pass

    def fake_fetch(url, timeout):
        if "fail" in url:
            raise RuntimeError("boom")
        return FakeResp()

    out_dir = refresh(manifest_path=manifest, out_root=tmp_path / "vintages",
                      fetch=fake_fetch, today="2099-01-01")
    assert out_dir == tmp_path / "vintages" / "2099-01-01"
    assert (out_dir / "raw" / "ok.json").read_bytes() == b"{}"
    rows = list(csv.DictReader((out_dir / "manifest.csv").open()))
    assert rows[0]["status"] == "ok" and rows[0]["bytes"] == "2"
    assert rows[1]["status"].startswith("error:")        # recorded, never fabricated
    assert not (out_dir / "raw" / "fail.json").exists()
    # the committed vintage is untouched
    assert (GOLD / "VINTAGE").read_text(encoding="utf-8").strip() == "2026-07-31"


def test_refresh_vintage_sanitizes_traversal_in_source_and_rejects_bad_today(tmp_path):
    from scripts.refresh_vintage import refresh

    manifest = tmp_path / "manifest.csv"
    manifest.write_text(
        "source,url,fetched,bytes,raw_file,processed_file\n"
        "../../evil,https://example.org/evil.json,2026-07-31,10,,evil.csv\n")

    class FakeResp:
        content = b"{}"
        def raise_for_status(self):
            pass

    def fake_fetch(url, timeout):
        return FakeResp()

    out_root = tmp_path / "vintages"
    out_dir = refresh(manifest_path=manifest, out_root=out_root,
                      fetch=fake_fetch, today="2099-01-02")
    # empty raw_file + a slash-bearing source must never escape out_root
    written = list(out_dir.rglob("*"))
    assert any(p.is_file() for p in written)  # something was actually written
    for path in written:
        if path.is_file():
            assert path.resolve().is_relative_to(out_root.resolve())

    # a caller-contract violation (malformed `today`) must raise, not fabricate a path
    with pytest.raises(ValueError):
        refresh(manifest_path=manifest, out_root=out_root,
                fetch=fake_fetch, today="../../gold")
