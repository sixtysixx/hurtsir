"""Debug: render gofile share page and dump DOM + API responses."""
import json, sys, time
from playwright.sync_api import sync_playwright

code = "RE0cXfkA"
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(accept_downloads=True)
    page = ctx.new_page()

    api_responses = []
    def on_response(resp):
        if "api.gofile.io" in resp.url or "server" in resp.url.lower():
            try:
                body = resp.text()[:800]
            except Exception:
                body = "<binary>"
            api_responses.append((resp.status, resp.url, body))
    page.on("response", on_response)

    page.goto(f"https://gofile.io/d/{code}", wait_until="domcontentloaded")
    page.wait_for_timeout(15000)
    html = page.content()
    print("=== API RESPONSES ===")
    for s, u, b in api_responses:
        print(s, u)
        print("   ", b[:400].replace("\n", " "))
    print("=== VISIBLE TEXT ===")
    print(page.inner_text("body")[:2000])
    print("=== HTML SNIPPET ===")
    # find anything resembling a file row or download control
    import re
    for pat in ("download", "list-group", "file-row", "content", "row"):
        hits = re.findall(rf"<[^>]*[^>]*{pat}[^>]*>", html, re.I)
        for h in list(dict.fromkeys(hits))[:8]:
            print(h[:200])
    page.screenshot(path="gofile_debug.png", full_page=True)
    browser.close()
