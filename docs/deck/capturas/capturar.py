from playwright.sync_api import sync_playwright
import os
S = os.environ["SHOT"]
B = "https://danribes.github.io/tfm-data-science/"

TOMAS = [
    ("01-portada",   "",            ".portada",                      None),
    ("02-tabla",     "?lam=1.4",    "El futuro, en números",         None),
    ("03-banda",     "",            "El margen del precio",          None),
    ("04-capas",     "",            "Cómo se ha calculado",          None),
    ("05-analogos",  "",            "España entre los demás",        None),
    ("06-pensiones", "?idx=1",      "El futuro, en números",         None),
    ("07-euribor",   "?r=4.8&h=2035", "El futuro, en números",       None),
]

with sync_playwright() as pw:
    b = pw.chromium.launch(args=["--no-sandbox","--disable-gpu","--disable-dev-shm-usage"])
    pg = b.new_page(viewport={"width":1500,"height":1100}, device_scale_factor=2)
    for nombre, query, ancla, _ in TOMAS:
        pg.goto(B + query, wait_until="networkidle")
        pg.wait_for_timeout(11000)
        if ancla.startswith("."):
            el = pg.query_selector(ancla)
        else:
            el = pg.evaluate_handle(
                "(t) => { const h = [...document.querySelectorAll('h4')].find(x => x.textContent.includes(t)); return h ? h.closest('.card') : null; }",
                ancla).as_element()
        if not el:
            print(f"  {nombre}: NO ENCONTRADO ({ancla})"); continue
        el.scroll_into_view_if_needed(); pg.wait_for_timeout(900)
        el.screenshot(path=f"{S}/{nombre}.png")
        print(f"  {nombre}: ok")
    b.close()
