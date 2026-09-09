"""Capture the exact request headers the gofile web app sends to /contents/."""
import sys
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context()
    page = ctx.new_page()

    captured = []

    def on_request(req):
        try:
            if "/contents/RE0cXfkA" in req.url:
                captured.append((req.method, req.url, dict(req.headers)))
        except Exception as e:
            print("handler error:", e, file=sys.stderr)

    page.on("request", on_request)
    page.goto("https://gofile.io/d/RE0cXfkA", wait_until="commit", timeout=60000)
    try:
        page.wait_for_selector('button[data-action="download"]', timeout=30000)
    except Exception as e:
        print("selector wait:", e, file=sys.stderr)

    for method, url, headers in captured:
        print("===", method, url)
        for k, v in headers.items():
            print(f"   {k}: {v}")
    if not captured:
        print("NO CAPTURED /contents REQUEST")
    browser.close()
print("DONE")
