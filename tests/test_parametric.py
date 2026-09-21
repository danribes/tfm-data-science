"""La banda paramétrica: que mida lo que dice medir.

Dos propiedades aquí no son detalles de implementación sino la diferencia
entre una banda honesta y una decorativa, y ninguna de las dos se ve mirando
el gráfico:

  · el parámetro se sortea una vez por trayectoria y se mantiene. Si se
    resortease cada año, la banda saldría mucho más estrecha y seguiría
    pareciendo perfectamente razonable en pantalla.

  · IPV_REV se trunca a (0,1) por rechazo. Un recorte al borde daría una
    banda parecida en el centro y masa apilada justo en las colas, que es
    donde se lee.
"""
import numpy as np
import pytest

from engine.levers import Levers
from engine.parametric import ESTIMATED, _draw, parametric_band
from engine.spain import Y0, run_scenario


def test_la_banda_contiene_la_proyeccion_puntual():
    b = parametric_band(n_draws=300, seed=7)
    for i, y in enumerate(b.years):
        assert b.percentiles["p5"][i] <= b.point[i] <= b.percentiles["p95"][i], y


def test_los_percentiles_van_en_orden():
    b = parametric_band(n_draws=300, seed=7)
    for i in range(len(b.years)):
        fila = [b.percentiles[f"p{p}"][i] for p in (5, 25, 50, 75, 95)]
        assert fila == sorted(fila)


def test_la_banda_nace_cerrada_y_se_abre():
    """2026 está anclado en el dato observado: ahí no hay incertidumbre que
    sortear. La banda debe abrirse de forma monótona a partir de ahí."""
    b = parametric_band(n_draws=300, seed=7)
    anchos = [b.percentiles["p95"][i] - b.percentiles["p5"][i]
              for i in range(len(b.years))]
    assert anchos[0] == pytest.approx(0.0, abs=1e-6)
    assert all(a <= s + 1e-9 for a, s in zip(anchos, anchos[1:]))
    assert anchos[-1] > 0.0


def test_misma_semilla_mismo_resultado():
    a = parametric_band(n_draws=200, seed=11)
    b = parametric_band(n_draws=200, seed=11)
    assert a.percentiles == b.percentiles


def test_semillas_distintas_no_dan_lo_mismo():
    a = parametric_band(n_draws=200, seed=11)
    b = parametric_band(n_draws=200, seed=12)
    assert a.percentiles != b.percentiles


def test_sin_sorteos_devuelve_la_proyeccion_de_parametros_fijos():
    """El modo de comparación: la conducta anterior sigue disponible."""
    b = parametric_band(n_draws=0)
    assert b.percentiles["p50"] == []
    assert b.point == pytest.approx(run_scenario(Levers())["precio"])


def test_el_punto_es_el_del_motor_sin_tocar():
    """La banda no debe desplazar la proyección publicada: el centro sigue
    siendo la corrida con los valores puntuales, no la mediana de los sorteos."""
    lv = Levers(lam=1.4)
    b = parametric_band(lv, n_draws=200, seed=3)
    assert b.point == pytest.approx(run_scenario(lv)["precio"])


def test_el_parametro_se_mantiene_durante_toda_la_trayectoria():
    """Si se resortease cada año en vez de una vez por trayectoria, el
    promediado interno estrecharía la banda. Se comprueba contra la anchura
    que producen parámetros fijos en los extremos del intervalo estimado:
    la banda sorteada debe quedar por debajo de ese rango, pero del mismo
    orden de magnitud, no diez veces menor."""
    b = parametric_band(n_draws=1500, seed=5)
    lr, rev = b.params["IPV_LR"], b.params["IPV_REV"]
    alto = run_scenario(Levers(), ipv_lr=lr["ci_high"], ipv_rev=rev["ci_low"])["precio"][-1]
    bajo = run_scenario(Levers(), ipv_lr=lr["ci_low"], ipv_rev=rev["ci_high"])["precio"][-1]
    extremos = alto - bajo
    assert 0.35 * extremos < b.width(2050) < extremos


def test_ipv_rev_se_queda_dentro_de_cero_uno():
    """Es una fracción que revierte por año: fuera de (0,1) no significa nada."""
    rng = np.random.default_rng(0)
    # se estrecha el dominio a propósito para forzar el rechazo a trabajar
    spec = {"value": 0.05, "se": 0.10}
    out = _draw(rng, spec, 4000, low=0.0, high=1.0)
    assert out.min() > 0.0 and out.max() < 1.0


def test_el_truncamiento_no_amontona_masa_en_el_borde():
    """Un recorte al borde pasaría las cotas y fallaría aquí: dejaría un pico
    de repetidos exactamente en 0 y en 1."""
    rng = np.random.default_rng(0)
    out = _draw(rng, {"value": 0.05, "se": 0.10}, 4000, low=0.0, high=1.0)
    assert (out < 1e-6).sum() == 0
    assert len(np.unique(out)) == len(out)


def test_solo_se_sortean_parametros_realmente_estimados():
    """PB_PERSIST está estimado pero el motor no lo usa, y el resto de
    constantes son calibración. Sortear una calibración sería inventar una
    distribución que nadie ha estimado."""
    from engine import constants as c

    assert set(ESTIMATED) == {"IPV_LR", "IPV_REV"}
    for nombre in ESTIMATED:
        fila = c.load_estimated().get(nombre)
        assert fila and float(fila["se"]) > 0.0


def test_la_banda_responde_a_las_palancas():
    """La banda acompaña al escenario, no es un adorno fijo alrededor del
    punto. `r` es la palanca que más mueve el precio (−307 k€ en 2050 en su
    máximo, vía coste hipotecario), así que es la que mejor lo comprueba."""
    base = parametric_band(Levers(), n_draws=300, seed=9)
    caro = parametric_band(Levers(r=6.0), n_draws=300, seed=9)
    assert caro.point[-1] < base.point[-1]
    assert caro.percentiles["p50"][-1] < base.percentiles["p50"][-1]
    assert caro.percentiles["p95"][-1] < base.percentiles["p95"][-1]


def test_recorte_por_ultimo_anio():
    b = parametric_band(n_draws=100, seed=1, last_year=2040)
    assert b.years[0] == Y0 and b.years[-1] == 2040
    assert len(b.point) == len(b.years) == len(b.percentiles["p50"])


def test_n_draws_negativo_es_un_error():
    with pytest.raises(ValueError):
        parametric_band(n_draws=-1)


def test_la_tabla_de_la_memoria_coincide_con_el_motor():
    """Las cifras de §6.6 salen del motor, no de una copia a mano.

    Este repositorio ya ha pagado el precio de tener figuras escritas a mano
    en un documento: el deck llevó ocho que hubo que cruzar una por una. Esta
    prueba lee la tabla publicada y la vuelve a calcular.
    """
    import re
    from pathlib import Path

    md = (Path(__file__).resolve().parents[1] / "docs/MEMORIA_TFM.md").read_text("utf-8")
    seccion = md.split("### 6.6 Incertidumbre paramétrica")[1].split("### 6.7")[0]
    filas = re.findall(
        r"^\| (20\d\d) \| ([\d.]+) € \| ([\d.]+) € \| ([\d.]+) € \| ([\d.]+) € \| ([\d,]+) % \|$",
        seccion, re.M)
    assert len(filas) == 4, f"esperaba 4 filas, encontré {len(filas)}"

    num = lambda t: float(t.replace(".", ""))                       # noqa: E731
    b = parametric_band()                       # los valores publicados: 4.000, semilla 42
    for anio, p5, punto, p95, ancho, rel in filas:
        i = b.years.index(int(anio))
        assert num(p5) == pytest.approx(b.percentiles["p5"][i], abs=1.0), anio
        assert num(punto) == pytest.approx(b.point[i], abs=1.0), anio
        assert num(p95) == pytest.approx(b.percentiles["p95"][i], abs=1.0), anio
        assert num(ancho) == pytest.approx(b.width(int(anio)), abs=1.0), anio
        esperado = b.width(int(anio)) / b.point[i] * 100
        assert float(rel.replace(",", ".")) == pytest.approx(esperado, abs=0.05), anio
