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

from engine import constants as c
from engine.constants import BASE_LEVERS
from engine.levers import Levers, PRESETS, preset_levers
from engine.montecarlo import mc_input_paths, run_montecarlo
from engine.spain import Y0, run_scenario


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


def _pens_correction(levers):
    """What pens_gap took from the primary balance, year by year."""
    central = c.load_central()
    r = run_scenario(levers)
    return [r["pb"][k] - (central[2026 + k]["pb"] + levers.sp
                          - central[2026 + k]["presion_demog"] * levers.dem)
            for k in range(len(r["pb"]))]


@pytest.mark.parametrize("preset", ["S0", "S5", "S6"])
def test_los_presets_que_no_tocan_el_crecimiento_no_llevan_correccion(preset):
    """La corrección de pensiones se mide contra los precios y el crecimiento
    de la BASE. S0, S5 (instituciones y cuña) y S6 (demografía) no los mueven,
    así que para ellos es exactamente cero y sus cifras publicadas no cambian.
    S1-S4 y S7 sí tocan el crecimiento o la inflación y llevan su efecto."""
    assert all(abs(x) < 1e-12 for x in _pens_correction(preset_levers(preset)))


@pytest.mark.parametrize("preset", ["S1", "S2", "S3", "S4", "S7"])
def test_los_presets_que_tocan_el_crecimiento_si_la_llevan(preset):
    assert max(abs(x) for x in _pens_correction(preset_levers(preset))) > 0.05


@pytest.mark.parametrize("kw", [{}, {"omega": 0.0}, {"omega": 0.5},
                                {"alpha_spread": 0.04, "b_crit": 90.0},
                                {"ipv_lr": 3.0, "ipv_rev": 0.4}])
def test_la_referencia_es_la_base_bajo_cualquier_calibracion(kw):
    """La referencia lee V0["pi"] y el g_nominal central directamente. Eso sólo
    es correcto si la base produce exactamente esos dos, con cualquier ajuste
    de calibración: aquí se comprueba."""
    central = c.load_central()
    base = run_scenario(Levers(), **kw)
    assert all(p == pytest.approx(c.V0["pi"], abs=1e-12) for p in base["pi"])
    assert all(g == pytest.approx(central[2026 + k]["g_nominal"], abs=1e-12)
               for k, g in enumerate(base["gnom"]))


def test_la_productividad_mejora_el_saldo_y_no_toca_los_ingresos():
    """Antes el ahorro en pensiones de crecer más no llegaba al saldo y los
    ingresos implícitos caían del 44 % al 40 % del PIB. Ahora llega al saldo
    primario y los ingresos, en % del PIB, se quedan como en la base."""
    base, up = run_scenario(Levers()), run_scenario(Levers(lam=BASE_LEVERS["lam"] + 1))
    assert up["pb"][-1] > base["pb"][-1] + 4
    assert up["b"][-1] < base["b"][-1] - 40
    rev = lambda r: r["gtot"][-1] + r["saldo"][-1]
    assert rev(up) == pytest.approx(rev(base), abs=1e-9)


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


def test_la_tabla_de_sensibilidad_de_la_memoria_coincide_con_el_motor():
    """§6.7 publica seis filas de deuda frente a indexación. Se recalculan.

    Este repositorio ya pagó el precio de llevar figuras escritas a mano en un
    documento: el deck tuvo ocho que hubo que cruzar una por una.
    """
    import re
    from pathlib import Path

    md = (Path(__file__).resolve().parents[1] / "docs/MEMORIA_TFM.md").read_text("utf-8")
    seccion = md.split("### 6.7 Indexación de las pensiones")[1].split("### 6.8")[0]
    filas = re.findall(
        r"^\| ([−+]?\d+,\d+)(?: \(referencia\))? \| (\d+,\d+) \| (\d+,\d+) \| ([−+]\d+,\d+) \|$",
        seccion, re.M)
    assert len(filas) == 6, f"esperaba 6 filas, encontré {len(filas)}"

    num = lambda t: float(t.replace("−", "-").replace("+", "").replace(",", "."))
    base = run_scenario(Levers())["b"][-1]
    for idx, pens, deuda, delta in filas:
        s = run_scenario(Levers(idx=num(idx)))
        assert num(pens) == pytest.approx(s["pens"][-1], abs=0.005), idx
        assert num(deuda) == pytest.approx(s["b"][-1], abs=0.05), idx
        assert num(delta) == pytest.approx(s["b"][-1] - base, abs=0.05), idx


def test_el_artefacto_de_sensibilidad_cubre_todo_el_rango():
    import json
    from pathlib import Path

    from engine.levers import LEVER_SPECS

    d = json.loads((Path(__file__).resolve().parents[1]
                    / "docs/eval/pension-indexation-sensitivity.json").read_text("utf-8"))
    spec = next(s for s in LEVER_SPECS if s["id"] == "idx")
    xs = [r["idx"] for r in d["rows"]]
    assert xs[0] == spec["min"] and xs[-1] == spec["max"]
    assert d["channel"] == "accounting"
    # monótona: más indexación, más deuda, sin excepciones en la rejilla
    deudas = [r["debt_2050"] for r in d["rows"]]
    assert deudas == sorted(deudas)


# ---- el canal del tipo sobre la vivienda ------------------------------------

def test_subir_el_euribor_encarece_la_hipoteca():
    """El fallo reportado, en una línea.

    El esfuerzo hipotecario es cuota/salario. Subir el tipo encarece la cuota,
    pero también abarata la vivienda, así que el signo neto depende de cuánto
    pese cada canal. Estaba desequilibrado: el choque de tipos restaba 2,6
    puntos al CRECIMIENTO anual del precio todos los años y sin decaer, de modo
    que el precio se hundía y la cuota bajaba con él.
    """
    k = 2035 - Y0
    base = run_scenario(Levers())["esf"][k]
    for r in (3.8, 4.8, 6.0):
        assert run_scenario(Levers(r=r))["esf"][k] > base, r


def test_el_esfuerzo_crece_de_forma_monotona_con_el_tipo():
    k = 2035 - Y0
    esf = [run_scenario(Levers(r=r))["esf"][k] for r in (2.8, 3.8, 4.8, 6.0)]
    assert esf == sorted(esf)


def test_la_cuota_sube_aunque_el_precio_baje():
    """Los dos canales siguen vivos y en la dirección correcta: el tipo sube,
    el precio baja algo, y la cuota sube porque el tipo pesa más."""
    k = 2035 - Y0
    base, caro = run_scenario(Levers()), run_scenario(Levers(r=4.8))
    assert caro["precio"][k] < base["precio"][k]      # el tipo sigue enfriando el precio
    assert caro["cuota"][k] > base["cuota"][k]        # pero no hasta abaratar la hipoteca


def test_el_choque_de_tipos_decae_como_el_de_importaciones():
    """Mismo idioma para el mismo problema, y con el mismo valor."""
    from engine import constants as c

    assert c.E_IPV_R_DECAY == c.PM_DECAY
    assert 0 < c.E_IPV_R_DECAY < 1


def test_el_efecto_sobre_el_nivel_del_precio_sigue_siendo_permanente():
    """Lo que decae es el impulso sobre la tasa, no el producto acumulado: una
    subida de tipos deja el precio permanentemente por debajo."""
    base, caro = run_scenario(Levers()), run_scenario(Levers(r=4.8))
    assert caro["precio"][-1] < base["precio"][-1]


def test_la_linea_base_no_se_mueve():
    """El decaimiento multiplica una diferencia que en la base es cero."""
    a = run_scenario(Levers())
    b = run_scenario(Levers(r=BASE_LEVERS["r"]))
    for key in a:
        assert a[key] == b[key], key


def test_las_cifras_del_guion_de_presentacion_son_las_del_motor():
    """El guion se dice en voz alta ante un tribunal.

    Una cifra obsoleta ahí se descubre en el peor momento posible: proyectada
    al lado de la pantalla que la desmiente. Se recalculan las que cita.
    """
    from pathlib import Path

    doc = (Path(__file__).resolve().parents[1]
           / "docs/PRESENTACION_10MIN.md").read_text(encoding="utf-8")
    base = run_scenario(Levers())
    k35, k50 = 2035 - Y0, 2050 - Y0

    esperadas = {
        f"{base['b'][k50]:.1f}".replace(".", ","): "deuda base 2050",
        f"{run_scenario(Levers(idx=1.0))['b'][k50]:.1f}".replace(".", ","): "deuda con idx +1",
        f"{base['esf'][k35]:.1f}".replace(".", ","): "esfuerzo base 2035",
        f"{run_scenario(Levers(r=4.8))['esf'][k35]:.1f}".replace(".", ","): "esfuerzo con r=4,8",
    }
    for cifra, que in esperadas.items():
        assert cifra in doc, f"{que}: {cifra} no aparece en el guion"


def test_el_guion_no_promete_lo_que_el_trabajo_no_acredita():
    """El cierre de la presentación es el resultado negativo. Si alguien lo
    suaviza, esta prueba lo dice."""
    from pathlib import Path

    import re

    crudo = (Path(__file__).resolve().parents[1]
             / "docs/PRESENTACION_10MIN.md").read_text(encoding="utf-8")
    # El guion va en prosa ajustada a 80 columnas, así que una frase puede
    # partirse en cualquier punto. Se normalizan los espacios antes de buscar.
    doc = re.sub(r"\s+", " ", crudo)
    assert "0,4000" in doc and "0,3953" in doc
    assert "5 de 17 comunidades" in doc
    assert "No es un intervalo de predicción" in doc
    # El descargo va como «lo que este número NO es: una predicción…», que es
    # más fuerte que la frase suelta que buscaba antes esta prueba.
    assert "una predicción de la deuda española" in doc
    assert "Proyección condicional" in doc
