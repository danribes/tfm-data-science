from playwright.sync_api import sync_playwright
from PIL import Image
import os
S = os.environ["SHOT"]
with sync_playwright() as pw:
    b = pw.chromium.launch(args=["--no-sandbox","--disable-gpu","--disable-dev-shm-usage"])
    pg = b.new_page(viewport={"width":1500,"height":1150}, device_scale_factor=2)
    pg.goto("https://danribes.github.io/tfm-data-science/", wait_until="networkidle")
    pg.wait_for_timeout(12000)
    # el corte exacto: donde empieza la tabla dentro de la tarjeta
    m = pg.evaluate("""() => {
        const h = [...document.querySelectorAll('h4')].find(x => x.textContent.includes('El margen del precio'));
        const card = h.closest('.card'); const tab = card.querySelector('.tscroll');
        const rc = card.getBoundingClientRect(), rt = tab.getBoundingClientRect();
        return {alto: rc.height, corte: rt.top - rc.top};
    }""")
    el = pg.evaluate_handle("() => [...document.querySelectorAll('h4')].find(x => x.textContent.includes('El margen del precio')).closest('.card')").as_element()
    el.scroll_into_view_if_needed(); pg.wait_for_timeout(800)
    el.screenshot(path=f"{S}/03-banda.png")
    b.close()
im = Image.open(f"{S}/03-banda.png"); w, h = im.size
frac = m["corte"] / m["alto"]
im.crop((0, 0, w, int(h * frac) - 8)).save(f"{S}/03-banda.png")
print(f"  corte en {frac:.3f} -> {Image.open(f'{S}/03-banda.png').size}")
