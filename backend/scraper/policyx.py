"""
PolicyX.com term insurance scraper.
Parses the best-plans comparison table — server-side HTML, no Playwright needed.
Data includes: Plan Name, Provider, CSR%, Monthly Premium.
"""
import logging
import re
import requests
from bs4 import BeautifulSoup
from typing import List, Dict

logger = logging.getLogger(__name__)

URL = "https://www.policyx.com/term-insurance/"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-IN,en;q=0.9",
    "Referer": "https://www.google.com",
}

# Provider metadata (age range, sum assured, policy term)
PROVIDER_META = {
    "axis max":    {"age_min": 18, "age_max": 65, "term_min": 10, "term_max": 50, "sa_min": 25,  "sa_max": 100000},
    "hdfc":        {"age_min": 18, "age_max": 65, "term_min": 10, "term_max": 40, "sa_min": 50,  "sa_max": 20000},
    "max life":    {"age_min": 18, "age_max": 65, "term_min": 10, "term_max": 50, "sa_min": 25,  "sa_max": 100000},
    "bajaj":       {"age_min": 18, "age_max": 65, "term_min": 10, "term_max": 40, "sa_min": 25,  "sa_max": 100000},
    "tata aia":    {"age_min": 18, "age_max": 65, "term_min": 10, "term_max": 40, "sa_min": 50,  "sa_max": 100000},
    "icici":       {"age_min": 18, "age_max": 65, "term_min": 5,  "term_max": 40, "sa_min": 50,  "sa_max": 20000},
    "sbi":         {"age_min": 18, "age_max": 65, "term_min": 5,  "term_max": 40, "sa_min": 35,  "sa_max": 20000},
    "lic":         {"age_min": 18, "age_max": 65, "term_min": 10, "term_max": 40, "sa_min": 50,  "sa_max": 10000},
}
DEFAULT_META = {"age_min": 18, "age_max": 65, "term_min": 10, "term_max": 40, "sa_min": 25, "sa_max": 100000}

FEATURES_MAP = {
    "axis max":  "7 Plan Options|Cover Continuance Benefit|Critical illness|Joint life cover|Return of premium",
    "hdfc":      "Life & CI Rebalance|Return of premium|Waiver on disability|Cover till age 85|Income benefit",
    "bajaj":     "Discount on high sum assured|Flexible payout|Cover continuance|Critical illness rider|Affordable",
    "tata aia":  "100% Return of premiums|Affordable premiums|Surrender value|Critical illness|Accidental death",
    "icici":     "Life Stage Protection|Smart Exit Benefit|Whole life option|Critical illness|Waiver of premium",
    "max life":  "Multiple plan options|Critical illness|Terminal illness benefit|Accidental death|Joint life cover",
}

PLAN_URL_MAP = {
    "axis max":  "https://www.axismaxlife.com/term-insurance/smart-term-plan-plus",
    "hdfc":      "https://www.hdfclife.com/term-insurance-plans/click-2-protect-super",
    "bajaj":     "https://www.bajajallianzlife.com/term-insurance/etouch-online-term-plan.html",
    "tata aia":  "https://www.tataaia.com/all-products/life-insurance/term-insurance/sampoorna-raksha-promise.html",
    "icici":     "https://www.iciciprulife.com/term-insurance/iprotect-smart-term-plan.html",
    "max life":  "https://www.maxlifeinsurance.com/term-insurance-plans/smart-secure-plus-plan",
}


def _provider_key(text: str) -> str:
    t = text.lower()
    for key in PROVIDER_META:
        if key in t:
            return key
    return ""


def scrape_policyx() -> List[Dict]:
    """
    Scrape PolicyX.com best-plans table.
    Returns plan dicts with live CSR and premium data.
    """
    try:
        resp = requests.get(URL, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        tables = soup.find_all("table")
        if not tables:
            logger.warning("PolicyX: no tables found on page")
            return []

        plans = []
        for table in tables:
            headers_row = table.find("tr")
            if not headers_row:
                continue
            header_texts = [th.get_text(strip=True).lower() for th in headers_row.find_all(["th", "td"])]

            # Look for table with CSR column
            if not any("csr" in h or "claim" in h or "settlement" in h for h in header_texts):
                continue

            rows = table.find_all("tr")[1:]  # skip header
            for row in rows:
                cells = [td.get_text(separator=" ", strip=True) for td in row.find_all(["td", "th"])]
                if len(cells) < 3:
                    continue

                provider_raw = cells[0]
                plan_name_raw = cells[1] if len(cells) > 1 else provider_raw
                features_raw = cells[2] if len(cells) > 2 else ""
                csr_raw = cells[3] if len(cells) > 3 else ""
                premium_raw = cells[4] if len(cells) > 4 else ""

                provider = re.sub(r"\s+", " ", provider_raw).strip()
                plan_name = re.sub(r"\s+", " ", plan_name_raw).strip()

                # Parse CSR
                csr_match = re.search(r"(\d{2,3}\.?\d*)\s*%", csr_raw)
                if not csr_match:
                    csr_match = re.search(r"(\d{2,3}\.?\d*)", csr_raw)
                csr = float(csr_match.group(1)) if csr_match else 0.0

                # Parse monthly premium → annual
                premium_match = re.search(r"[\d,]+", premium_raw.replace(",", ""))
                monthly_premium = float(premium_match.group().replace(",", "")) if premium_match else 0
                annual_premium = monthly_premium * 12 if monthly_premium > 0 else 0

                if not provider or not plan_name or csr == 0:
                    continue

                pkey = _provider_key(provider)
                meta = PROVIDER_META.get(pkey, DEFAULT_META)

                # Build features from scraped text or fallback map
                scraped_features = [f.strip() for f in re.split(r"(?<=[a-z])(?=[A-Z])|[•·|]", features_raw) if len(f.strip()) > 3][:5]
                features = "|".join(scraped_features) if scraped_features else FEATURES_MAP.get(pkey, "Term insurance|Death benefit|Online purchase")

                plans.append({
                    "plan_name": plan_name,
                    "provider": provider,
                    "source": "policyx",
                    "sum_assured_min": meta["sa_min"],
                    "sum_assured_max": meta["sa_max"],
                    "premium_annual": annual_premium if annual_premium > 0 else 9000,
                    "policy_term_min": meta["term_min"],
                    "policy_term_max": meta["term_max"],
                    "age_min": meta["age_min"],
                    "age_max": meta["age_max"],
                    "claim_settlement_ratio": csr,
                    "key_features": features,
                    "source_url": PLAN_URL_MAP.get(pkey, URL),
                })

        logger.info(f"PolicyX: scraped {len(plans)} plans")
        return plans

    except Exception as e:
        logger.warning(f"PolicyX scraper error: {e}")
        return []
