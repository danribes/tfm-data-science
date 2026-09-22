from playwright.sync_api import sync_playwright
import os
S = os.environ["SHOT"]
with sync_playwright() as pw:
    b = pw.chromium.launch(args=["--no-sandbox","--disable-gpu","--disable-dev-shm-usage"])
    pg = b.new_page(viewport={"width":1500,"height":1150}, device_scale_factor=2)
    pg.goto("https://danribes.github.io/tfm-data-science/prediccion", wait_until="networkidle")
    pg.wait_for_timeout(12000)
    for i, nombre in ((1, "09b-resultado"), (2, "09c-horizonte")):
        el = pg.evaluate_handle(f"() => document.querySelectorAll('.card')[{i}]").as_element()
        el.scroll_into_view_if_needed(); pg.wait_for_timeout(800)
        el.screenshot(path=f"{S}/{nombre}.png")
        print(f"  {nombre}: ok")
    b.close()
