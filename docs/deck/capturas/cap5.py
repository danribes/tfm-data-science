from playwright.sync_api import sync_playwright
import os
S = os.environ["SHOT"]
B = "https://danribes.github.io/tfm-data-science/"
with sync_playwright() as pw:
    b = pw.chromium.launch(args=["--no-sandbox","--disable-gpu","--disable-dev-shm-usage"])
    pg = b.new_page(viewport={"width":1500,"height":1150}, device_scale_factor=2)
    for nombre, q in (("02-tabla", "?lam=1.4"), ("06-pensiones", "?idx=1"), ("07-euribor", "?r=4.8&h=2035")):
        pg.goto(B + q, wait_until="networkidle"); pg.wait_for_timeout(11000)
        el = pg.query_selector("table.projtable")
        el.scroll_into_view_if_needed(); pg.wait_for_timeout(700)
        el.screenshot(path=f"{S}/{nombre}.png")
        from PIL import Image
        w, h = Image.open(f"{S}/{nombre}.png").size
        print(f"  {nombre}: {w}x{h} ratio {w/h:.2f}")
    # la banda: sólo el gráfico y su tabla, sin los tres pies largos
    pg.goto(B, wait_until="networkidle"); pg.wait_for_timeout(11000)
    el = pg.evaluate_handle("() => { const h = [...document.querySelectorAll('h4')].find(x => x.textContent.includes('El margen del precio')); return h.closest('.card').querySelector('.recharts-wrapper')?.parentElement; }").as_element()
    if el:
        el.scroll_into_view_if_needed(); pg.wait_for_timeout(700)
        el.screenshot(path=f"{S}/03-banda.png")
        from PIL import Image
        w, h = Image.open(f"{S}/03-banda.png").size
        print(f"  03-banda: {w}x{h} ratio {w/h:.2f}")
    b.close()
