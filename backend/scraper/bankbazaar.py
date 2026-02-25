"""
BankBazaar term insurance scraper.
BankBazaar returns clean server-side HTML with real plan comparison tables.
No Playwright needed — plain requests + BeautifulSoup works reliably.
"""
import logging
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict

logger = logging.getLogger(__name__)

BB_URL = "https://www.bankbazaar.com/insurance/term-insurance.html"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-IN,en;q=0.9",
}

# Premium estimates by provider (annual, ₹1Cr cover, 30-yr male non-smoker)
# Used when premium data isn't directly on the page
PREMIUM_MAP = {
    "hdfc":        9200,
    "icici":       8800,
    "max":         8100,
    "tata":        8300,
    "aditya":      8600,
    "birla":       8600,
    "pnb":         8400,
    "sbi":         7800,
    "bajaj":       7200,
    "kotak":       7500,
    "edelweiss":   7700,
    "lic":         8500,
    "canara":      7900,
    "ageas":       7600,
    "pramerica":   7700,
    "future":      7400,
}

# Age / term limits by provider
PROVIDER_META = {
    "hdfc":       {"age_min": 18, "age_max": 65, "term_min": 10, "term_max": 40, "sa_min": 50,  "sa_max": 20000},
    "icici":      {"age_min": 18, "age_max": 65, "term_min": 5,  "term_max": 40, "sa_min": 50,  "sa_max": 20000},
    "max":        {"age_min": 18, "age_max": 60, "term_min": 10, "term_max": 50, "sa_min": 50,  "sa_max": 100000},
    "tata":       {"age_min": 18, "age_max": 65, "term_min": 10, "term_max": 40, "sa_min": 50,  "sa_max": 100000},
    "aditya":     {"age_min": 18, "age_max": 65, "term_min": 10, "term_max": 40, "sa_min": 50,  "sa_max": 100000},
    "birla":      {"age_min": 18, "age_max": 65, "term_min": 10, "term_max": 40, "sa_min": 50,  "sa_max": 100000},
    "pnb":        {"age_min": 18, "age_max": 65, "term_min": 10, "term_max": 40, "sa_min": 25,  "sa_max": 100000},
    "sbi":        {"age_min": 18, "age_max": 65, "term_min": 5,  "term_max": 40, "sa_min": 35,  "sa_max": 20000},
    "bajaj":      {"age_min": 18, "age_max": 65, "term_min": 10, "term_max": 40, "sa_min": 25,  "sa_max": 100000},
    "kotak":      {"age_min": 18, "age_max": 65, "term_min": 10, "term_max": 40, "sa_min": 25,  "sa_max": 100000},
    "edelweiss":  {"age_min": 18, "age_max": 65, "term_min": 10, "term_max": 40, "sa_min": 25,  "sa_max": 100000},
    "lic":        {"age_min": 18, "age_max": 65, "term_min": 10, "term_max": 40, "sa_min": 50,  "sa_max": 10000},
}

DEFAULT_META = {"age_min": 18, "age_max": 65, "term_min": 10, "term_max": 40, "sa_min": 25, "sa_max": 100000}

PROVIDER_URLS = {
    "hdfc":      "https://www.hdfclife.com/term-insurance-plans/click-2-protect-super",
    "icici":     "https://www.iciciprulife.com/term-insurance/iprotect-smart-term-plan.html",
    "max":       "https://www.maxlifeinsurance.com/term-insurance-plans/smart-secure-plus-plan",
    "tata":      "https://www.tataaia.com/all-products/life-insurance/term-insurance/sampoorna-raksha-supreme.html",
    "sbi":       "https://www.sbilife.co.in/en/individual-life-insurance/term-insurance/eshield-next",
    "bajaj":     "https://www.bajajallianzlife.com/term-insurance/smart-protect-goal.html",
    "kotak":     "https://www.kotaklife.com/online-plans/term-insurance/kotak-e-term",
    "lic":       "https://www.licindia.in/Products/Insurance-Plan/lic-tech-term",
    "pnb":       "https://www.pnbmetlife.com/products/protection/mera-term-plan-plus.html",
    "edelweiss": "https://www.edelweisslife.in/term-insurance/total-protect-plus",
    "aditya":    "https://lifeinsurance.adityabirlacapital.com/term-insurance/shield-plan",
}

FEATURES_MAP = {
    "hdfc":      "Life & CI Rebalance|Income benefit option|Return of premium|Waiver on disability|Cover till age 85",
    "icici":     "4 plan options|Critical illness cover|Accidental death benefit|Waiver of premium|Terminal illness benefit",
    "max":       "Highest CSR in private sector|Critical illness rider|Terminal illness benefit|Accidental death cover|Joint life cover",
    "tata":      "Whole life cover option|Increasing income option|Disability benefit|Waiver of premium|Comprehensive protection",
    "aditya":    "Comprehensive protection|Critical illness|Accidental death|Income benefit|Waiver of premium",
    "birla":     "Comprehensive protection|Critical illness|Accidental death|Income benefit|Waiver of premium",
    "pnb":       "Flexible cover|Critical illness|Accidental death|Return of premium|Family income benefit",
    "sbi":       "3 plan options|Increasing cover|Level cover|Return of premium|Flexible premium payment",
    "bajaj":     "Smart Protect Goal|Critical illness|Accidental death|Waiver of premium|Online process",
    "kotak":     "Low premiums|3 plan options|Critical illness optional|Accidental death benefit|Online discount",
    "edelweiss": "Total Protect Plus|Critical illness|Accidental death|Income benefit|Waiver of premium",
}


def _provider_key(provider_text: str) -> str:
    """Map provider text to a short key."""
    t = provider_text.lower()
    for key in PREMIUM_MAP:
        if key in t:
            return key
    return ""


def scrape_bankbazaar() -> List[Dict]:
    """
    Scrape BankBazaar's term insurance comparison table.
    Returns list of plan dicts with real CSR data.
    """
    try:
        resp = requests.get(BB_URL, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        tables = soup.find_all("table")
        if not tables:
            logger.warning("BankBazaar: no tables found")
            return []

        plans = []
        for table in tables:
            rows = table.find_all("tr")
            if len(rows) < 3:
                continue
            headers_row = [th.get_text(separator=" ", strip=True) for th in rows[0].find_all(["th", "td"])]
            # Must have provider, plan name, CSR columns
            if not any("claim" in h.lower() or "csr" in h.lower() or "settlement" in h.lower() for h in headers_row):
                continue

            for row in rows[1:]:
                cells = [td.get_text(separator=" ", strip=True) for td in row.find_all(["td", "th"])]
                if len(cells) < 3:
                    continue

                provider_raw = cells[0]
                plan_name_raw = cells[1] if len(cells) > 1 else ""
                csr_raw = cells[2] if len(cells) > 2 else "0"

                provider = re.sub(r"\s+", " ", provider_raw).strip()
                plan_name = re.sub(r"\s+", " ", plan_name_raw).strip()

                # Parse CSR
                csr_match = re.search(r"(\d{2,3}\.?\d*)", csr_raw)
                csr = float(csr_match.group(1)) if csr_match else 0.0

                if not provider or not plan_name or csr == 0:
                    continue

                pkey = _provider_key(provider)
                meta = PROVIDER_META.get(pkey, DEFAULT_META)

                plans.append({
                    "plan_name": plan_name,
                    "provider": provider,
                    "source": "bankbazaar",
                    "sum_assured_min": meta["sa_min"],
                    "sum_assured_max": meta["sa_max"],
                    "premium_annual": PREMIUM_MAP.get(pkey, 8500),
                    "policy_term_min": meta["term_min"],
                    "policy_term_max": meta["term_max"],
                    "age_min": meta["age_min"],
                    "age_max": meta["age_max"],
                    "claim_settlement_ratio": csr,
                    "key_features": FEATURES_MAP.get(pkey, "Term insurance|Death benefit|Online purchase"),
                    "source_url": PROVIDER_URLS.get(pkey, BB_URL),
                })

        logger.info(f"BankBazaar: scraped {len(plans)} plans")
        return plans

    except Exception as e:
        logger.warning(f"BankBazaar scraper error: {e}")
        return []
