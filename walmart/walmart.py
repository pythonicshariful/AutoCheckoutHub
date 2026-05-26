"""
bot.py — Walmart Buy Bot
=========================
Run:  python bot.py --sku <sku> --quantity <qty> --task_id <task_id>
"""

import asyncio
import random
import sys
import argparse
import requests
from pathlib import Path
from loguru import logger as log
from playwright.async_api import async_playwright, BrowserContext, Page, TimeoutError as PWTimeout

# ── Config ────────────────────────────────────────────────────────────────────
WALMART_HOME = "https://www.walmart.com"
USER_AGENT   = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
LAUNCH_ARGS = [
    "--no-sandbox", "--disable-blink-features=AutomationControlled",
    "--disable-dev-shm-usage", "--window-size=1280,900",
    "--lang=en-US,en", "--no-first-run", "--no-default-browser-check",
    "--disable-infobars",
]
STEALTH_JS = """
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
window.chrome = { runtime: {} };
Object.defineProperty(navigator, 'languages', { get: () => ['en-US','en'] });
"""

def report_log(task_id, message, level="info"):
    log.info(f"[{level.upper()}] {message}")
    if task_id:
        try:
            requests.post(f"http://localhost:8000/tasks/{task_id}/log", json={}, params={"message": message, "level": level})
        except:
            pass

def update_status(task_id, status):
    if task_id:
        try:
            requests.post(f"http://localhost:8000/tasks/{task_id}/status", params={"status": status})
        except:
            pass

# ── CAPTCHA Detection & Handler ───────────────────────────────────────────────
PX_SIGNALS = [
    'id="px-captcha"',
    'class="re-captcha"',
    'Robot or human',
    'Activate and hold the button',
    'Human verification challenge',
]

def _has_captcha(html: str) -> bool:
    return any(s in html for s in PX_SIGNALS)

async def _handle_captcha(page: Page, context: str = "", task_id: int = None) -> None:
    try:
        html = await page.content()
    except Exception:
        return

    if not _has_captcha(html):
        return

    origin_url = page.url
    where = f" [{context}]" if context else ""
    report_log(task_id, f"⚠️  CAPTCHA detected{where}! Solve it in the browser.", "error")
    update_status(task_id, "paused")
    
    for _ in range(90):        # 90 × 2s = 3 minutes
        await asyncio.sleep(2)
        try:
            html = await page.content()
        except Exception:
            continue
        if page.url != origin_url or not _has_captcha(html):
            report_log(task_id, "✅ CAPTCHA solved! Resuming...", "success")
            update_status(task_id, "running")
            await asyncio.sleep(1)
            return

    report_log(task_id, "❌ CAPTCHA was not solved in time — continuing anyway", "error")

# ── Safe Navigation ───────────────────────────────────────────────────────────
async def _goto(page: Page, url: str, ctx: str = "", task_id: int = None) -> None:
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30_000)
    except PWTimeout:
        report_log(task_id, f"Navigation timeout for {url} — checking for CAPTCHA", "error")
    await _handle_captcha(page, ctx or url, task_id)

# ── Smart Selector Wait ───────────────────────────────────────────────────────
async def _wait_for(page: Page, selector: str, timeout_ms: int = 15_000,
                    ctx: str = "", task_id: int = None) -> bool:
    try:
        await page.wait_for_selector(selector, timeout=timeout_ms)
        return True
    except PWTimeout:
        await _handle_captcha(page, ctx, task_id)
        try:
            await page.wait_for_selector(selector, timeout=timeout_ms)
            return True
        except PWTimeout:
            return False

# ── Helpers ───────────────────────────────────────────────────────────────────
async def _delay(lo=0.5, hi=1.5):
    await asyncio.sleep(random.uniform(lo, hi))

async def _human_type(page: Page, selector: str, text: str):
    await page.click(selector)
    await _delay(0.3, 0.7)
    await page.fill(selector, "")
    await _delay(0.2, 0.4)
    for char in text:
        await page.type(selector, char, delay=random.randint(60, 180))
        if random.random() < 0.08:
            await _delay(0.15, 0.4)

# ── Browser Factory ───────────────────────────────────────────────────────────
async def _launch(pw, task_id):
    profile_dir = Path(f"c:/temp/profile_{task_id}")
    profile_dir.mkdir(exist_ok=True, parents=True)
    context = await pw.chromium.launch_persistent_context(
        str(profile_dir),
        headless=False,
        args=LAUNCH_ARGS,
        viewport={"width": 1280, "height": 900},
        user_agent=USER_AGENT,
        locale="en-US",
        timezone_id="America/New_York",
    )
    await context.add_init_script(STEALTH_JS)
    page = context.pages[0] if context.pages else await context.new_page()
    return context, page

# ── Step 1: Login ─────────────────────────────────────────────────────────────
async def step1_login(page: Page, task_id: int) -> None:
    report_log(task_id, "Step 1 — Opening Walmart & checking login...", "info")
    await _goto(page, WALMART_HOME, "homepage", task_id)

    async def _signed_in():
        try:
            await _delay(1.0, 2.0)
            return not await page.locator('text="Sign In"').first.is_visible(timeout=4_000)
        except Exception:
            return False

    if await _signed_in():
        report_log(task_id, "✅ Already logged in (chrome_profile session active)", "success")
        return

    report_log(task_id, "🔐 Not logged in. Please sign in manually in the browser window.", "error")
    update_status(task_id, "paused")

    for _ in range(150):
        await asyncio.sleep(2)
        if await _signed_in():
            report_log(task_id, "✅ Login confirmed! Profile saved.", "success")
            update_status(task_id, "running")
            await _delay(2.0, 3.0)
            return
            
    report_log(task_id, "ℹ️ Continuing as guest.", "info")
    update_status(task_id, "running")

# ── Step 2: SKU Search → Product Page ────────────────────────────────────────
async def step2_search_sku(page: Page, sku: str, qty: int, task_id: int) -> str:
    report_log(task_id, f"Step 2 — Searching for SKU: {sku} with QTY: {qty}", "info")

    if "walmart.com" not in page.url:
        await _goto(page, WALMART_HOME, "pre-search", task_id)

    search_sel = '[data-automation-id="header-input-search"]'
    found = await _wait_for(page, search_sel, timeout_ms=10_000, ctx="search-bar", task_id=task_id)
    if not found:
        report_log(task_id, "Search bar not found — cannot search", "error")
        return None

    await _human_type(page, search_sel, sku)
    await _delay(0.4, 0.9)

    await page.press(search_sel, "Enter")

    try:
        await page.wait_for_url("**/search**", timeout=15_000)
    except PWTimeout:
        await _handle_captcha(page, "after-search-submit", task_id)

    await _handle_captcha(page, "search-results-page", task_id)

    result_selectors = [
        '[data-testid="item-stack"]',
        '[data-testid="list-view"]',
        'section[data-dca-type="module"] a[href*="/ip/"]',
    ]
    found_results = False
    for sel in result_selectors:
        ok = await _wait_for(page, sel, timeout_ms=12_000, ctx=f"results-{sel[:20]}", task_id=task_id)
        if ok:
            found_results = True
            break

    if not found_results:
        report_log(task_id, "Could not find any search result elements", "error")
        return None

    await _delay(0.6, 1.2)

    first_link = page.locator('a[href*="/ip/"]').first
    try:
        href = await first_link.get_attribute("href", timeout=5_000)
    except Exception:
        report_log(task_id, "No /ip/ product link found in search results", "error")
        return None

    product_url = f"https://www.walmart.com{href}" if href.startswith("/") else href
    product_url = product_url.split("?")[0]
    report_log(task_id, f"First result URL: {product_url}", "info")

    await _delay(0.5, 1.0)
    await _goto(page, product_url, "product-page", task_id)

    await _wait_for(page, 'h1[itemprop="name"], [data-automation-id="product-title"], h1',
                    timeout_ms=12_000, ctx="product-title", task_id=task_id)

    report_log(task_id, f"✅ On product page", "success")
    return product_url

# ── Step 3: Wait for Buy Now → Click → Set Quantity ─────────────────────────
async def step3_buy_now(page: Page, qty: int, task_id: int) -> bool:
    report_log(task_id, "Step 3 — Waiting for 'Buy Now' button...", "info")
    buy_now_sel = '[data-testid="buy-now-wrapper"]'

    for attempt in range(300):       # up to ~10 minutes
        await _handle_captcha(page, "buy-now-poll", task_id)
        try:
            btn = page.locator(buy_now_sel).first
            visible  = await btn.is_visible(timeout=1_500)
            disabled = await btn.is_disabled(timeout=1_500)
            if visible and not disabled:
                break
        except Exception:
            pass
        await asyncio.sleep(2)
    else:
        report_log(task_id, "❌ Buy Now button never became available", "error")
        return False

    await _delay(0.3, 0.8)
    await page.locator(buy_now_sel).first.click()
    report_log(task_id, "Clicked Buy Now", "info")

    stepper_sel  = '[data-testid="quantity-stepper"]'
    inc_btn_sel  = '[data-testid="quantity-stepper-inc-button"]'
    qty_label_sel = '[data-testid="quantity-label"]'

    found = await _wait_for(page, stepper_sel, timeout_ms=15_000, ctx="quantity-stepper", task_id=task_id)
    if not found:
        return True

    await _handle_captcha(page, "after-buy-now", task_id)
    await _delay(0.5, 1.0)

    if qty > 1:
        for i in range(qty - 1):
            try:
                inc_btn = page.locator(inc_btn_sel).first
                if await inc_btn.is_disabled(timeout=2_000):
                    break
                await inc_btn.click()
                await _delay(0.3, 0.7)
            except Exception:
                break

    report_log(task_id, f"✅ Quantity set", "success")
    return True

# ── Step 4: Place Order ─────────────────────────────────────────────────────
async def step4_place_order(page: Page, task_id: int) -> bool:
    report_log(task_id, "Step 4 — Waiting for 'Place order' button...", "info")
    place_order_sels = [
        '[aria-label*="Place order"]',
        'button:has-text("Place order")',
        '[data-dca-id="B:B72770B2F7"]',
    ]

    for attempt in range(150):   # up to 5 minutes
        await _handle_captcha(page, "place-order-poll", task_id)

        for sel in place_order_sels:
            try:
                btn = page.locator(sel).first
                if await btn.is_visible(timeout=1_000) and not await btn.is_disabled(timeout=1_000):
                    await _delay(0.5, 1.2)
                    await btn.click()
                    report_log(task_id, "🛒 'Place order' clicked — order submitted!", "success")
                    await _delay(2.0, 3.5)
                    await _handle_captcha(page, "post-place-order", task_id)
                    return True
            except Exception:
                continue
        await asyncio.sleep(2)

    report_log(task_id, "❌ Place Order button never became available", "error")
    return False

# ── Main ──────────────────────────────────────────────────────────────────────
async def run_bot(sku: str, qty: int, task_id: int):
    report_log(task_id, "Bot browser starting...", "info")
    update_status(task_id, "running")
    
    async with async_playwright() as pw:
        context, page = await _launch(pw, task_id)

        await step1_login(page, task_id)
        product_url = await step2_search_sku(page, sku, qty, task_id)

        if product_url:
            ok = await step3_buy_now(page, qty, task_id)
            if ok:
                await step4_place_order(page, task_id)

        report_log(task_id, "Task Finished", "success")
        update_status(task_id, "completed")
        print("\nBrowser is now staying open. Press enter in terminal to close.")
        await asyncio.get_event_loop().run_in_executor(None, input, "")
        await context.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Walmart Auto Checkout Bot")
    parser.add_argument("--sku", type=str, required=True, help="SKU to monitor")
    parser.add_argument("--quantity", type=int, default=1, help="Quantity to buy")
    parser.add_argument("--task_id", type=int, required=True, help="Backend Task ID")
    
    args = parser.parse_args()
    asyncio.run(run_bot(args.sku, args.quantity, args.task_id))
