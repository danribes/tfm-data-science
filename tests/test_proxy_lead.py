"""Test del barrido de proxies adelantados."""
import pathlib
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
GOLD = ROOT / "storage" / "gold"


def test_proxy_scan():
    d = pd.read_csv(GOLD / "gold_proxy_lead_scan.csv")
    assert len(d) >= 8
    assert {"proxy", "r", "lead", "n"} <= set(d.columns)
    # los dos hallazgos robustos deben estar presentes con su firma
    m = d.set_index("proxy")
    assert abs(m.loc["hipotecas_yoy", "r"]) > 0.6, "hipotecas debe liderar con r>0.6"
    assert m.loc["hipotecas_yoy", "n"] >= 70
    assert abs(m.loc["aceleracion_poblacion", "r"]) > 0.5, "aceleración población r>0.5"
    assert m.loc["aceleracion_poblacion", "lead"] >= 8, "su valor está en el adelanto largo"
