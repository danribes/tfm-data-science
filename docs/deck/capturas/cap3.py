from playwright.sync_api import sync_playwright
import os
S = os.environ["SHOT"]
with sync_playwright() as pw:
    b = pw.chromium.launch(args=["--no-sandbox","--disable-gpu","--disable-dev-shm-usage"])
    pg = b.new_page(viewport={"width":1500,"height":1150}, device_scale_factor=2)
    pg.goto("https://danribes.github.io/tfm-data-science/prediccion", wait_until="networkidle")
    pg.wait_for_timeout(12000)
    tarjetas = pg.evaluate("() => [...document.querySelectorAll('.card')].map((c,i) => i + ': ' + (c.querySelector('h3,h4')?.textContent || c.innerText.slice(0,45)).trim())")
    for t in tarjetas: print("  ", t[:80])
    # la que lleva el veredicto / la tabla MASE
    idx = pg.evaluate("() => [...document.querySelectorAll('.card')].findIndex(c => /MASE|veredicto|drift/i.test(c.innerText))")
    print("tarjeta del veredicto:", idx)
    if idx >= 0:
        el = pg.evaluate_handle(f"() => document.querySelectorAll('.card')[{idx}]").as_element()
        el.scroll_into_view_if_needed(); pg.wait_for_timeout(900)
        el.screenshot(path=f"{S}/09b-veredicto.png")
        print("  09b-veredicto: ok")
    b.close()
