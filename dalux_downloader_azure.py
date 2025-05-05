# -*- coding: utf-8 -*-
import sys
import os
import argparse
from pathlib import Path
from playwright.sync_api import sync_playwright

# —————————————————————————————————————————————————————
# Bundle your ms-playwright folder into the EXE via PyInstaller
if getattr(sys, "frozen", False):
    base = sys._MEIPASS
else:
    base = os.path.dirname(os.path.abspath(__file__))

os.environ["PLAYWRIGHT_BROWSERS_PATH"] = os.path.join(base, "ms-playwright")
# —————————————————————————————————————————————————————

def run_script(user: str, pwd: str, download_dir: str):
    DOWNLOADS_DIR = Path(download_dir)
    DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(accept_downloads=True)
        page = ctx.new_page()
        # 1) Login
        page.goto("https://build.dalux.com/client/login", wait_until="domcontentloaded")
        page.fill('[data-cy="login-email"]', user)
        page.fill('[data-cy="login-password"]', pwd)
        page.click('[data-cy="login-button"]')
        page.wait_for_url("**/client/*")

        # 2) Dismiss notification if present
        try:
            page.wait_for_selector('[data-cy="notification-close-btn"]', timeout=5_000)
            page.click('[data-cy="notification-close-btn"]')
        except:
            pass

        # 3) Select project
        page.click('[data-cy="project-button-top-bar"]')
        project_name = "RAMB\u00D8LL - SANDKASSE"
        page.wait_for_selector('dlx-project-card[data-cy="product-card"]')
        card = page.locator(
            'dlx-select-product-item-dialog dlx-project-card[data-cy="product-card"]',
            has_text=project_name
        ).first
        card.click()
        page.wait_for_load_state("networkidle")

        # 4) Click Box module
        page.wait_for_selector('button[data-cy^="module-button"]')
        buttons = page.locator('button[data-cy^="module-button"]', has_text="Box")
        if buttons.count() != 1:
            raise RuntimeError(f"Expected 1 Box button, found {buttons.count()}")
        buttons.first.click()

        # 5) Navigate to file
        page.click('[data-cy="folder-dropdown-Filer-false"]')
        page.click('[data-cy="folder-dropdown-Filer-undefined"]')
        page.click('dlx-treeview-node[data-cy-second="tree-view-node-C07 Geometri"]')
        page.click('dlx-treeview-node[data-cy-second="tree-view-node-K01 Arkitektur"]')
        page.click('dlx-treeview-node[data-cy-second="tree-view-node-C07.1 Tegning"]')
        page.dblclick('tr[data-cy="data-grid-row-2"]')

        # 6) Download
        download = page.expect_download(lambda: page.click(
            '[data-cy="file-details-dialog-toolbar-download-btn"]'
        ))
        dest = DOWNLOADS_DIR / download.suggested_filename
        download.save_as(str(dest))
        browser.close()
        return dest

def main():
    p = argparse.ArgumentParser(description="Dalux Downloader (headless)")
    p.add_argument("-f", "--folder", required=True,
                   help="Download folder for the PDF")
    args = p.parse_args()

    user = os.getenv("DALUX_USER")
    pwd  = os.getenv("DALUX_PASSWORD")
    if not user or not pwd:
        print("Error: DALUX_USER and DALUX_PASSWORD must be set", file=sys.stderr)
        sys.exit(1)

    try:
        out = run_script(user, pwd, args.folder)
        print(f"✅ Downloaded to: {out}")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Failed: {e}", file=sys.stderr)
        sys.exit(2)

if __name__ == "__main__":
    main()
