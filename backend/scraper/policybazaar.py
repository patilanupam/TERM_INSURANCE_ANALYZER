"""
PolicyBazaar term insurance scraper.
Attempts live scraping via Playwright; falls back to seed data on failure.
"""
import asyncio
import logging
from datetime import datetime
from typing import List, Dict

logger = logging.getLogger(__name__)

PB_URL = "https://www.policybazaar.com/life-insurance/term-insurance/quotes/"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


async def _scrape_live() -> List[Dict]:
    """Attempt to scrape PolicyBazaar term insurance plans using Playwright."""
    from playwright.async_api import async_playwright

    plans = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=HEADERS["User-Agent"],
            viewport={"width": 1280, "height": 800},
        )
        page = await context.new_page()

        try:
            await page.goto(
                "https://www.policybazaar.com/life-insurance/term-insurance/",
                timeout=30000,
                wait_until="domcontentloaded",
            )
            await page.wait_for_timeout(5000)

            # Try to extract plan cards — selectors may vary with site updates
            plan_cards = await page.query_selector_all(
                ".plan-card, .planCard, [class*='plan-name'], [class*='insurer-name']"
            )

            for card in plan_cards[:10]:
                try:
                    name_el = await card.query_selector(
                        "[class*='plan-name'], [class*='planName'], h3, h4"
                    )
                    provider_el = await card.query_selector(
                        "[class*='insurer'], [class*='company'], [class*='brand']"
                    )
                    premium_el = await card.query_selector(
                        "[class*='premium'], [class*='price'], [class*='amount']"
                    )
                    csr_el = await card.query_selector(
                        "[class*='claim'], [class*='csr'], [class*='settlement']"
                    )

                    plan_name = (await name_el.inner_text()).strip() if name_el else ""
                    provider = (
                        (await provider_el.inner_text()).strip() if provider_el else ""
                    )
                    premium_text = (
                        (await premium_el.inner_text()).strip() if premium_el else "0"
                    )
                    csr_text = (
                        (await csr_el.inner_text()).strip() if csr_el else "0"
                    )

                    # Parse numeric values
                    premium = float(
                        "".join(filter(lambda c: c.isdigit() or c == ".", premium_text))
                        or 0
                    )
                    csr = float(
                        "".join(filter(lambda c: c.isdigit() or c == ".", csr_text))
                        or 0
                    )

                    if plan_name and provider:
                        plans.append(
                            {
                                "plan_name": plan_name,
                                "provider": provider,
                                "source": "policybazaar",
                                "sum_assured_min": 50,
                                "sum_assured_max": 10000,
                                "premium_annual": premium,
                                "policy_term_min": 10,
                                "policy_term_max": 40,
                                "age_min": 18,
                                "age_max": 65,
                                "claim_settlement_ratio": csr,
                                "key_features": "",
                                "source_url": PB_URL,
                            }
                        )
                except Exception:
                    continue

        except Exception as e:
            logger.warning(f"PolicyBazaar scrape failed: {e}")
        finally:
            await browser.close()

    return plans


def scrape_policybazaar() -> List[Dict]:
    """Scrape PolicyBazaar; return live data or empty list on failure."""
    import concurrent.futures

    def _run():
        import sys
        if sys.platform == "win32":
            loop = asyncio.ProactorEventLoop()
        else:
            loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(_scrape_live())
        finally:
            loop.close()

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            plans = executor.submit(_run).result(timeout=60)
        logger.info(f"PolicyBazaar: scraped {len(plans)} plans")
        return plans
    except Exception as e:
        logger.warning(f"PolicyBazaar scraper error: {e}")
        return []
