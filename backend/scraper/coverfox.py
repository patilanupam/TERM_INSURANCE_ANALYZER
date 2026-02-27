"""
Coverfox.com term insurance scraper.
Scrapes two tables:
  - Table 1: Plan details (age range, sum assured, policy term)
  - Table 2: Claim Settlement Ratio by insurer

Merges both to produce rich plan records.
"""
import logging
import re
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

URL = "https://www.coverfox.com/term-insurance/"

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

# Premium estimates (annual ₹, ₹1Cr cover, 30-yr male non-smoker)
PREMIUM_MAP = {
    "icici":    8800,
    "aegon":    7600,
    "hdfc":     9200,
    "max":      8100,
    "lic":      8500,
    "tata":     8300,
    "sbi":      7800,
    "bajaj":    7200,
    "kotak":    7500,
    "pnb":      8400,
    "edelweiss":7700,
    "reliance": 7600,
    "canara":   7900,
    "aditya":   8600,
    "future":   7400,
    "bharti":   8200,
    "aviva":    8000,
    "idbi":     8300,
    "india first": 7500,
    "birla":    8600,
    "axis max": 9000,
}

PLAN_NAME_MAP = {
    "icici":       "iProtect Smart",
    "aegon":       "iTerm Prime Plan",
    "hdfc":        "Click 2 Protect Super",
    "max":         "Smart Secure Plus",
    "lic":         "Tech Term Plan",
    "tata":        "Sampoorna Raksha Supreme",
    "sbi":         "eShield Next",
    "bajaj":       "eTouch Online Term",
    "kotak":       "e-Term Plan",
    "pnb":         "Mera Term Plan Plus",
    "edelweiss":   "Total Protect Plus",
    "reliance":    "Digi-Term Plan",
    "canara":      "iSelect Smart360",
    "aditya":      "DigiShield Plan",
    "birla":       "DigiShield Plan",
    "future":      "Smart Life Plan",
    "bharti":      "Smart Jeevan",
    "aviva":       "i-Term Smart",
    "idbi":        "iSurance Flexi Term",
    "india first": "e-Term Plan",
    "axis max":    "Smart Term Plan Plus",
}

FEATURES_MAP = {
    "icici":     "4 plan options|Critical illness cover|Accidental death benefit|Waiver of premium|Terminal illness benefit",
    "aegon":     "Affordable premiums|Return of premium option|Critical illness|Accidental death|Income benefit",
    "hdfc":      "Life & CI Rebalance|Income benefit option|Return of premium|Waiver on disability|Cover till age 85",
    "max":       "Highest CSR in private sector|Critical illness rider|Terminal illness benefit|Accidental death|Joint life cover",
    "lic":       "Pure term plan|Online purchase|Return of premium option|Accidental death benefit|Government-backed",
    "tata":      "Comprehensive protection|Whole life cover option|Increasing income option|Disability benefit|Waiver of premium",
    "sbi":       "3 plan options|Increasing cover|Level cover|Return of premium|Flexible premium payment",
    "bajaj":     "Discount on high sum assured|Flexible payout options|Cover continuance|Critical illness rider|Online",
    "kotak":     "Low premiums|3 plan options|Critical illness optional|Accidental death benefit|Online discount",
    "pnb":       "Flexible cover options|Critical illness|Accidental death|Return of premium|Family income benefit",
    "edelweiss": "Total Protect Plus|Critical illness|Accidental death|Income benefit|Waiver of premium",
    "reliance":  "Affordable premiums|Flexible SA|Critical illness|Accidental death|Online purchase",
    "canara":    "Flexible cover options|Increasing cover|Critical illness add-on|Return of premium|Joint life cover",
    "aditya":    "Comprehensive protection|Critical illness|Accidental death|Income benefit|Waiver of premium",
    "birla":     "Comprehensive protection|Critical illness|Accidental death|Income benefit|Waiver of premium",
    "future":    "Affordable premiums|Flexible payout|Critical illness|Accidental death|Online process",
    "bharti":    "Comprehensive cover|Critical illness|Accidental death|Income benefit|Waiver of premium",
    "aviva":     "Multiple options|Critical illness|Accidental death|Return of premium|Flexible payment",
    "india first":"e-Term Plan|Critical illness|Accidental death|Flexible payout|Online process",
    "axis max":  "7 plan options|Cover continuance|Critical illness|Joint life cover|Return of premium",
}

PROVIDER_URLS = {
    "icici":     "https://www.iciciprulife.com/term-insurance/iprotect-smart-term-plan.html",
    "aegon":     "https://www.aegonlife.com/insurance-products/iTerm-Prime",
    "hdfc":      "https://www.hdfclife.com/term-insurance-plans/click-2-protect-super",
    "max":       "https://www.maxlifeinsurance.com/term-insurance-plans/smart-secure-plus-plan",
    "lic":       "https://www.licindia.in/Products/Insurance-Plan/lic-tech-term",
    "tata":      "https://www.tataaia.com/all-products/life-insurance/term-insurance/sampoorna-raksha-supreme.html",
    "sbi":       "https://www.sbilife.co.in/en/individual-life-insurance/term-insurance/eshield-next",
    "bajaj":     "https://www.bajajallianzlife.com/term-insurance/etouch-online-term-plan.html",
    "kotak":     "https://www.kotaklife.com/online-plans/term-insurance/kotak-e-term",
    "pnb":       "https://www.pnbmetlife.com/products/protection/mera-term-plan-plus.html",
    "edelweiss": "https://www.edelweisslife.in/term-insurance/total-protect-plus",
    "reliance":  "https://www.reliancenipponlife.com/term-insurance/digi-term",
    "canara":    "https://www.canarahsbclife.com/term-insurance",
    "aditya":    "https://lifeinsurance.adityabirlacapital.com/term-insurance/shield-plan",
    "birla":     "https://lifeinsurance.adityabirlacapital.com/term-insurance/shield-plan",
    "future":    "https://www.futuregenerali.in/life-insurance/term-insurance",
    "bharti":    "https://www.bharti-axalife.com/products/protection/smart-jeevan-plan",
    "aviva":     "https://www.avivaindiablog.com/life-insurance/term-insurance",
    "india first":"https://www.indiafirstlife.com/term-insurance",
    "axis max":  "https://www.axismaxlife.com/term-insurance/smart-term-plan-plus",
}

PROVIDER_META = {
    "icici":    {"age_min": 18, "age_max": 65, "term_min": 5,  "term_max": 40, "sa_min": 50,  "sa_max": 20000},
    "aegon":    {"age_min": 18, "age_max": 65, "term_min": 5,  "term_max": 40, "sa_min": 25,  "sa_max": 100000},
    "hdfc":     {"age_min": 18, "age_max": 65, "term_min": 10, "term_max": 40, "sa_min": 50,  "sa_max": 20000},
    "max":      {"age_min": 18, "age_max": 60, "term_min": 10, "term_max": 50, "sa_min": 25,  "sa_max": 100000},
    "lic":      {"age_min": 18, "age_max": 65, "term_min": 10, "term_max": 40, "sa_min": 50,  "sa_max": 10000},
    "tata":     {"age_min": 18, "age_max": 65, "term_min": 10, "term_max": 40, "sa_min": 50,  "sa_max": 100000},
    "sbi":      {"age_min": 18, "age_max": 65, "term_min": 5,  "term_max": 40, "sa_min": 35,  "sa_max": 20000},
    "bajaj":    {"age_min": 18, "age_max": 65, "term_min": 10, "term_max": 40, "sa_min": 25,  "sa_max": 100000},
    "kotak":    {"age_min": 18, "age_max": 65, "term_min": 10, "term_max": 40, "sa_min": 25,  "sa_max": 100000},
    "pnb":      {"age_min": 18, "age_max": 65, "term_min": 10, "term_max": 40, "sa_min": 25,  "sa_max": 100000},
    "edelweiss":{"age_min": 18, "age_max": 65, "term_min": 10, "term_max": 40, "sa_min": 25,  "sa_max": 100000},
    "reliance": {"age_min": 18, "age_max": 60, "term_min": 10, "term_max": 35, "sa_min": 25,  "sa_max": 100000},
    "canara":   {"age_min": 18, "age_max": 65, "term_min": 5,  "term_max": 40, "sa_min": 25,  "sa_max": 100000},
    "aditya":   {"age_min": 18, "age_max": 65, "term_min": 10, "term_max": 40, "sa_min": 30,  "sa_max": 100000},
    "birla":    {"age_min": 18, "age_max": 65, "term_min": 10, "term_max": 40, "sa_min": 30,  "sa_max": 100000},
    "future":   {"age_min": 18, "age_max": 65, "term_min": 10, "term_max": 35, "sa_min": 25,  "sa_max": 100000},
    "bharti":   {"age_min": 18, "age_max": 65, "term_min": 10, "term_max": 40, "sa_min": 25,  "sa_max": 100000},
    "aviva":    {"age_min": 18, "age_max": 60, "term_min": 10, "term_max": 35, "sa_min": 25,  "sa_max": 100000},
    "india first":{"age_min":18,"age_max": 65, "term_min": 5,  "term_max": 40, "sa_min": 50,  "sa_max": 100000},
    "axis max": {"age_min": 18, "age_max": 65, "term_min": 10, "term_max": 50, "sa_min": 25,  "sa_max": 100000},
}
DEFAULT_META = {"age_min": 18, "age_max": 65, "term_min": 10, "term_max": 40, "sa_min": 25, "sa_max": 100000}


def _provider_key(text: str) -> str:
    t = text.lower()
    for key in list(PREMIUM_MAP.keys()):
        if key in t:
            return key
    return ""


def _parse_sa(text: str):
    """Parse sum assured: returns (min_lakhs, max_lakhs)."""
    nums = re.findall(r"\d+\.?\d*", text.lower().replace(",", ""))
    if not nums:
        return 25, 100000
    vals = [float(n) for n in nums if n and n != "."]
    # Convert crore to lakhs if needed
    converted = []
    raw = text.lower()
    for i, v in enumerate(vals):
        if "cr" in raw:
            converted.append(v * 100)
        else:
            converted.append(v)
    if len(converted) == 1:
        return converted[0], 100000
    return min(converted), max(converted) if max(converted) < 200000 else 100000


def _parse_term(text: str):
    """Parse policy term range: returns (min_years, max_years)."""
    nums = re.findall(r"\d+", text)
    if len(nums) >= 2:
        return int(nums[0]), int(nums[1])
    if len(nums) == 1:
        return 10, int(nums[0])
    return 10, 40


def _parse_age(text: str):
    """Parse age range: returns (min_age, max_age)."""
    nums = re.findall(r"\d+", text)
    if len(nums) >= 2:
        return int(nums[0]), int(nums[1])
    return 18, 65


def scrape_coverfox() -> List[Dict]:
    """
    Scrape Coverfox.com for term insurance plan data.
    Merges plan details table with CSR data table.
    """
    try:
        resp = requests.get(URL, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")
        tables = soup.find_all("table")

        if len(tables) < 2:
            logger.warning("Coverfox: fewer than 2 tables found")
            return []

        # ── Table 1: Plan details ──────────────────────────────────────
        plan_details: Dict[str, dict] = {}
        rows_t1 = tables[0].find_all("tr")[1:]  # skip header
        for row in rows_t1:
            cells = [td.get_text(separator=" ", strip=True) for td in row.find_all(["td", "th"])]
            if len(cells) < 2:
                continue
            plan_name = re.sub(r"\s+", " ", cells[0]).strip()
            age_text  = cells[1] if len(cells) > 1 else ""
            sa_text   = cells[2] if len(cells) > 2 else ""
            term_text = cells[3] if len(cells) > 3 else ""

            age_min, age_max = _parse_age(age_text)
            sa_min, sa_max   = _parse_sa(sa_text)
            term_min, term_max = _parse_term(term_text)

            plan_details[plan_name.lower()] = {
                "plan_name": plan_name,
                "age_min": age_min,
                "age_max": age_max,
                "sa_min": sa_min,
                "sa_max": sa_max,
                "term_min": term_min,
                "term_max": term_max,
            }

        # ── Table 2: CSR data ──────────────────────────────────────────
        csr_map: Dict[str, float] = {}
        rows_t2 = tables[1].find_all("tr")[1:]  # skip header
        for row in rows_t2:
            cells = [td.get_text(separator=" ", strip=True) for td in row.find_all(["td", "th"])]
            if len(cells) < 2:
                continue
            provider_raw = cells[0]
            csr_raw = cells[1]
            csr_match = re.search(r"(\d{2,3}\.?\d*)\s*%", csr_raw)
            if not csr_match:
                continue
            csr = float(csr_match.group(1))
            pkey = _provider_key(provider_raw)
            if pkey:
                csr_map[pkey] = csr

        # ── Merge: build one plan per provider in csr_map ─────────────
        plans = []
        seen_providers = set()
        for pkey, csr in csr_map.items():
            if pkey in seen_providers:
                continue
            seen_providers.add(pkey)

            plan_name = PLAN_NAME_MAP.get(pkey, f"{pkey.title()} Term Plan")
            meta = PROVIDER_META.get(pkey, DEFAULT_META)

            # Try to enrich with table-1 details
            for key, detail in plan_details.items():
                if pkey in key or any(word in key for word in pkey.split()):
                    meta = {
                        "age_min": detail["age_min"],
                        "age_max": detail["age_max"],
                        "sa_min":  detail["sa_min"],
                        "sa_max":  detail["sa_max"],
                        "term_min":detail["term_min"],
                        "term_max":detail["term_max"],
                    }
                    break

            plans.append({
                "plan_name": plan_name,
                "provider": _nice_provider_name(pkey),
                "source": "coverfox",
                "sum_assured_min": meta.get("sa_min", 25),
                "sum_assured_max": meta.get("sa_max", 100000),
                "premium_annual": PREMIUM_MAP.get(pkey, 8500),
                "policy_term_min": meta.get("term_min", 10),
                "policy_term_max": meta.get("term_max", 40),
                "age_min": meta.get("age_min", 18),
                "age_max": meta.get("age_max", 65),
                "claim_settlement_ratio": csr,
                "key_features": FEATURES_MAP.get(pkey, "Term insurance|Death benefit|Online purchase"),
                "source_url": PROVIDER_URLS.get(pkey, URL),
            })

        logger.info(f"Coverfox: scraped {len(plans)} plans (CSR data)")
        return plans

    except Exception as e:
        logger.warning(f"Coverfox scraper error: {e}")
        return []


def _nice_provider_name(pkey: str) -> str:
    """Convert provider key to display name."""
    names = {
        "icici":     "ICICI Prudential",
        "aegon":     "Aegon Life",
        "hdfc":      "HDFC Life",
        "max":       "Max Life",
        "lic":       "LIC",
        "tata":      "Tata AIA",
        "sbi":       "SBI Life",
        "bajaj":     "Bajaj Allianz",
        "kotak":     "Kotak Life",
        "pnb":       "PNB MetLife",
        "edelweiss": "Edelweiss Life",
        "reliance":  "Reliance Nippon Life",
        "canara":    "Canara HSBC Life",
        "aditya":    "Aditya Birla Sun Life",
        "birla":     "Aditya Birla Sun Life",
        "future":    "Future Generali",
        "bharti":    "Bharti AXA Life",
        "aviva":     "Aviva India",
        "india first":"IndiaFirst Life",
        "idbi":      "IDBI Federal Life",
        "axis max":  "Axis Max Life",
    }
    return names.get(pkey, pkey.title())
