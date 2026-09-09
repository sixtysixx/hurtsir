#!/usr/bin/env python3
"""
gofile_dl.py - download a gofile.io share via a headless browser.

Flow (mirrors what a human does on the gofile web UI):
  1. open the share page https://gofile.io/d/<code>
  2. wait for the file row to render (JS app fetches content with an
     internally-generated websiteToken, which we don't have to reverse)
  3. click the row's download button (data-action="download")
  4. Chromium handles the download natively into a temp folder; we then
     move it to the requested destination.

Cookies: everything runs inside one headless browser context, so gofile's
own cookies (and any user cookies, if we point the profile at a real
Chrome profile) persist for the duration of the flow. To reuse the
*user's* existing login, pass `--user-data-dir` to Playwright's
`launch_persistent_context` - then cookies/localStorage are kept between
runs.
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout


def download_gofile(
    code: str,
    dest: Path,
    *,
    user_data_dir: Path | None = None,
    headless: bool = True,
    timeout_ms: int = 120_000,
) -> Path:
    """Download the single file in gofile share `code` to `dest`."""
    dest = dest.resolve()
    dest.parent.mkdir(parents=True, exist_ok=True)

    # The browser downloads to its own dir first; we relocate afterwards.
    dl_dir = dest.parent / ".gofile_dl_tmp"
    dl_dir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        if user_data_dir:
            ctx = p.chromium.launch_persistent_context(
                str(user_data_dir),
                headless=headless,
                args=["--disable-blink-features=AutomationControlled"],
            )
        else:
            ctx = p.chromium.launch(
                headless=headless,
                args=["--disable-blink-features=AutomationControlled"],
            )
            ctx = ctx.new_context(accept_downloads=True)
        page = ctx.new_page()
        try:
            page.goto(f"https://gofile.io/d/{code}",
                      wait_until="domcontentloaded", timeout=timeout_ms)

            # Wait for the file row / download button (UI is a JS app).
            btn = page.locator('button[data-action="download"]')
            btn.first.wait_for(state="visible", timeout=timeout_ms)
            btn.first.scroll_into_view_if_needed()
            with page.expect_download(timeout=timeout_ms) as dl_info:
                btn.first.click()
            download = dl_info.value

            tmp_path = download.path()          # Chromium's temp file
            shutil.move(str(tmp_path), dest)    # relocate
            return dest
        finally:
            ctx.close()
            shutil.rmtree(dl_dir, ignore_errors=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("code", help="gofile code, e.g. RE0cXfkA or full URL")
    ap.add_argument("dest", help="destination file path")
    ap.add_argument("--user-data-dir", help="Chromium profile dir (keeps cookies/logins)")
    ap.add_argument("--headed", action="store_true", help="show the browser")
    args = ap.parse_args()

    m = re.search(r"([A-Za-z0-9]{6,12})\s*$", args.code)
    if not m:
        print(f"Could not parse gofile code from: {args.code}", file=sys.stderr)
        sys.exit(2)
    code = m.group(1)

    out = download_gofile(code, Path(args.dest),
                          user_data_dir=(Path(args.user_data_dir) if args.user_data_dir else None),
                          headless=not args.headed)
    print(f"OK {out}")


if __name__ == "__main__":
    main()
