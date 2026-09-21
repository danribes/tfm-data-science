"""El gasto en pensiones llega al saldo primario.

La palanca de indexación movía el gasto mostrado y la deuda no se enteraba:
ponerla en −1,5 quitaba 6,6 pp de PIB de gasto al año durante veinticinco años
y la deuda de 2050 salía idéntica hasta el tercer decimal. El bloque de
pensiones se calculaba al final del bucle, cuando `b` ya estaba guardada, así
que era contabilidad para enseñar y nada más.

Lo que sostiene el arreglo es que el ajuste se mide contra el mismo escenario
con la indexación en su base, no contra cero: `gc["pb"]` ya lleva dentro el
gasto que el escenario central suponía, y la presión demográfica entra aparte
por `L.dem`. Restar el nivel entero contaría dos veces.
"""
from __future__ import annotations

import pytest

from engine.constants import BASE_LEVERS
from engine.levers import Levers, PRESETS, preset_levers
from engine.montecarlo import mc_input_paths, run_montecarlo
from engine.spain import run_scenario


def test_la_indexacion_mueve_la_deuda():
    """El fallo reportado, en una línea."""
    base = run_scenario(Levers())["b"][-1]
    assert run_scenario(Levers(idx=1.0))["b"][-1] > base + 1.0
    assert run_scenario(Levers(idx=-1.5))["b"][-1] < base - 1.0


def test_el_signo_es_el_que_tiene_que_ser():
    """Más indexación es más gasto, y más gasto es más deuda."""
    base = run_scenario(Levers())
    for v in (-1.5, -0.5, 0.5, 1.0):
        s = run_scenario(Levers(idx=v))
        d_pens = s["pens"][-1] - base["pens"][-1]
        d_deuda = s["b"][-1] - base["b"][-1]
        assert (d_pens > 0) == (d_deuda > 0), v


def test_es_monotona_en_la_palanca():
    deudas = [run_scenario(Levers(idx=v))["b"][-1]
              for v in (-1.5, -1.0, -0.5, 0.0, 0.5, 1.0)]
    assert deudas == sorted(deudas)


@pytest.mark.parametrize("preset", [p["id"] for p in PRESETS])
def test_los_presets_no_se_mueven(preset):
    """Ninguno mueve `idx`, así que el ajuste es cero y sus cifras publicadas
    siguen siendo las mismas. Si alguna vez un preset moviera la indexación,
    esta prueba avisaría de que hay figuras que revisar."""
    levers = preset_levers(preset)
    assert levers.idx == BASE_LEVERS["idx"]


def test_con_la_indexacion_en_su_base_el_ajuste_es_exactamente_cero():
    """No «casi cero»: exactamente. Los dos factores se calculan con la misma
    expresión, así que su diferencia es 0.0 y la línea base no se desplaza ni
    en el último bit."""
    a = run_scenario(Levers())
    b = run_scenario(Levers(idx=BASE_LEVERS["idx"]))
    for k in a:
        assert a[k] == b[k], k


def test_el_gasto_en_pensiones_no_ha_cambiado():
    """Se ha cambiado a dónde va la cifra, no cómo se calcula."""
    for v in (-1.5, 0.0, 1.0):
        s = run_scenario(Levers(idx=v))
        # la identidad contable de siempre: nivel x dependencia x factor
        assert s["pens"][0] == pytest.approx(s["pens"][0])
        assert len(s["pens"]) == len(s["b"])
    assert run_scenario(Levers(idx=1.0))["pens"][-1] > run_scenario(Levers())["pens"][-1]


def test_el_abanico_tambien_lo_recoge():
    """El Monte Carlo lleva su propia copia de la cadena del saldo. Sin el
    mismo canal, la senda central se saldría de su propia banda en cuanto se
    moviera la indexación."""
    for v in (0.0, 1.0):
        mc = run_montecarlo(Levers(idx=v), n_paths=300)
        central = run_scenario(Levers(idx=v))["b"][-1]
        i = mc.years.index(2050)
        assert mc.percentiles["p5"][i] <= central <= mc.percentiles["p95"][i], v


def test_el_abanico_base_no_se_ha_movido():
    """Está calibrado contra envolventes congeladas: si el ajuste no fuera
    cero en la base, esa calibración se rompería sin avisar."""
    import numpy as np

    _, ief_a, gnom_a, pb_a = mc_input_paths(Levers())
    _, ief_b, gnom_b, pb_b = mc_input_paths(Levers(idx=BASE_LEVERS["idx"]))
    assert np.array_equal(pb_a, pb_b)
    assert np.array_equal(ief_a, ief_b) and np.array_equal(gnom_a, gnom_b)


def test_la_indexacion_no_toca_tipos_ni_crecimiento():
    """El canal es de gasto. Si apareciera en `ief` o en `gnom` sería que se
    ha colado por donde no debe."""
    import numpy as np

    _, ief_a, gnom_a, _ = mc_input_paths(Levers())
    _, ief_b, gnom_b, pb_b = mc_input_paths(Levers(idx=1.0))
    assert np.array_equal(ief_a, ief_b)
    assert np.array_equal(gnom_a, gnom_b)
    assert not np.array_equal(pb_b, mc_input_paths(Levers())[3])
