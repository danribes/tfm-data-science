from playwright.sync_api import sync_playwright
import os
S = os.environ["SHOT"]
B = "https://danribes.github.io/tfm-data-science/"

with sync_playwright() as pw:
    b = pw.chromium.launch(args=["--no-sandbox","--disable-gpu","--disable-dev-shm-usage"])
    pg = b.new_page(viewport={"width":1500,"height":1150}, device_scale_factor=2)

    # Consulta, con una pregunta real respondida
    pg.goto(B + "consulta", wait_until="networkidle"); pg.wait_for_timeout(9000)
    try:
        pg.fill(".consulta-input", "¿qué es el saldo primario?")
        pg.get_by_role("button", name="Preguntar", exact=False).first.click()
        pg.wait_for_timeout(30000)
        pg.evaluate("() => { const d = document.querySelector('details.consulta-passages'); if (d) d.open = true; }")
        pg.wait_for_timeout(1200)
        el = pg.query_selector(".consulta-thread") or pg.query_selector(".consulta")
        if el:
            el.screenshot(path=f"{S}/08-consulta.png"); print("  08-consulta: ok")
    except Exception as e:
        print("  08-consulta:", type(e).__name__)

    # Predicción: el veredicto del modelo profundo
    pg.goto(B + "prediccion", wait_until="networkidle"); pg.wait_for_timeout(11000)
    el = pg.evaluate_handle("() => document.querySelector('.card')").as_element()
    if el:
        el.screenshot(path=f"{S}/09-prediccion.png"); print("  09-prediccion: ok")

    # Laboratorio: el presupuesto
    pg.goto(B + "laboratorio", wait_until="networkidle"); pg.wait_for_timeout(11000)
    el = pg.evaluate_handle("() => { const h = [...document.querySelectorAll('h4')].find(x => x.textContent.includes('Presupuesto del escenario')); return h ? h.closest('.card') : null; }").as_element()
    if el:
        el.scroll_into_view_if_needed(); pg.wait_for_timeout(900)
        el.screenshot(path=f"{S}/10-presupuesto.png"); print("  10-presupuesto: ok")
    b.close()
