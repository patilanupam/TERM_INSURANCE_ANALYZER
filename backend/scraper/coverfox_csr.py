"""
Coverfox claim-settlement-ratio page scraper.
URL: https://www.coverfox.com/life-insurance/claim-settlement-ratio/

Scrapes the 15-row CSR table:  Insurance Provider | Claim Settlement Ratio
Builds full plan entries using PLAN_NAME_MAP and PROVIDER_META lookups.
Adds providers not already covered by other scrapers (e.g. Pramerica/Bandhan Life,
Exide Life, Star Union Dai-ichi).
"""
import logging
import re
import requests
from bs4 import BeautifulSoup
from typing import List, Dict

logger = logging.getLogger(__name__)

CSR_URL = "https://www.coverfox.com/life-insurance/claim-settlement-ratio/"

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

# Map scraped provider name fragments → internal key
PROVIDER_KEY_MAP = {
    "max life":        "max",
    "aegon":           "aegon",
    "bharti axa":      "bharti",
    "life insurance corporation": "lic",
    "pramerica":       "pramerica",
    "bandhan life":    "pramerica",
    "exide life":      "exide",
    "kotak":           "kotak",
    "reliance nippon": "reliance",
    "bajaj allianz":   "bajaj",
    "pnb met":         "pnb",
    "pnb metlife":     "pnb",
    "aditya birla":    "aditya",
    "tata aia":        "tata",
    "aviva":           "aviva",
    "hdfc life":       "hdfc",
    "icici prudential":"icici",
    "sbi life":        "sbi",
    "star union":      "star_union",
    "canara hsbc":     "canara",
    "india first":     "india_first",
    "future generali": "future",
    "edelweiss":       "edelweiss",
    "axis max":        "axis",
}

PLAN_NAME_MAP = {
    "max":        "Smart Secure Plus",
    "aegon":      "iTerm Prime Plan",
    "bharti":     "Smart Jeevan",
    "lic":        "Tech Term Plan",
    "pramerica":  "Mera Term Plan",           # Pramerica / now Bandhan Life
    "exide":      "Smart Term Plan",           # Exide Life (now HDFC Life post-merger)
    "kotak":      "e-Term Plan",
    "reliance":   "Digi-Term Plan",
    "bajaj":      "eTouch Online Term",
    "pnb":        "Mera Term Plan Plus",
    "aditya":     "DigiShield Plan",
    "tata":       "Sampoorna Raksha Promise",
    "aviva":      "i-Term Smart",
    "hdfc":       "Click 2 Protect Super",
    "icici":      "iProtect Smart",
    "sbi":        "eShield Next",
    "star_union": "Pradhan Mantri Jeevan Jyoti Bima Yojana",
    "canara":     "iSelect Smart360",
    "india_first":"e-Term Plan",
    "future":     "Smart Life Plan",
    "edelweiss":  "Total Protect Plus",
    "axis":       "Smart Term Plan Plus",
}

PROVIDER_DISPLAY_MAP = {
    "max":        "Max Life",
    "aegon":      "Aegon Life",
    "bharti":     "Bharti AXA Life",
    "lic":        "LIC",
    "pramerica":  "Bandhan Life",             # Rebranded in 2023
    "exide":      "Exide Life",
    "kotak":      "Kotak Life",
    "reliance":   "Reliance Nippon Life",
    "bajaj":      "Bajaj Allianz",
    "pnb":        "PNB MetLife",
    "aditya":     "Aditya Birla Sun Life",
    "tata":       "Tata AIA",
    "aviva":      "Aviva India",
    "hdfc":       "HDFC Life",
    "icici":      "ICICI Prudential",
    "sbi":        "SBI Life",
    "star_union": "Star Union Dai-ichi Life",
    "canara":     "Canara HSBC Life",
    "india_first":"IndiaFirst Life",
    "future":     "Future Generali",
    "edelweiss":  "Edelweiss Life",
    "axis":       "Axis Max Life",
}

PREMIUM_MAP = {
    "max": 8100, "aegon": 7600, "bharti": 8200, "lic": 8500,
    "pramerica": 7800, "exide": 8000, "kotak": 7500, "reliance": 7600,
    "bajaj": 7200, "pnb": 8400, "aditya": 8600, "tata": 8300,
    "aviva": 8000, "hdfc": 9200, "icici": 8800, "sbi": 7800,
    "star_union": 7200, "canara": 7900, "india_first": 7500,
    "future": 7400, "edelweiss": 7700, "axis": 9000,
}

PROVIDER_META = {
    "max":        {"age_min": 18, "age_max": 60, "term_min": 10, "term_max": 50, "sa_min": 25,  "sa_max": 100000},
    "aegon":      {"age_min": 18, "age_max": 65, "term_min": 5,  "term_max": 40, "sa_min": 25,  "sa_max": 100000},
    "bharti":     {"age_min": 18, "age_max": 65, "term_min": 10, "term_max": 40, "sa_min": 25,  "sa_max": 100000},
    "lic":        {"age_min": 18, "age_max": 65, "term_min": 10, "term_max": 40, "sa_min": 50,  "sa_max": 10000},
    "pramerica":  {"age_min": 18, "age_max": 65, "term_min": 10, "term_max": 40, "sa_min": 25,  "sa_max": 100000},
    "exide":      {"age_min": 18, "age_max": 65, "term_min": 10, "term_max": 40, "sa_min": 25,  "sa_max": 100000},
    "kotak":      {"age_min": 18, "age_max": 65, "term_min": 10, "term_max": 40, "sa_min": 25,  "sa_max": 100000},
    "reliance":   {"age_min": 18, "age_max": 60, "term_min": 10, "term_max": 35, "sa_min": 25,  "sa_max": 100000},
    "bajaj":      {"age_min": 18, "age_max": 65, "term_min": 10, "term_max": 40, "sa_min": 25,  "sa_max": 100000},
    "pnb":        {"age_min": 18, "age_max": 65, "term_min": 10, "term_max": 40, "sa_min": 25,  "sa_max": 100000},
    "aditya":     {"age_min": 18, "age_max": 65, "term_min": 10, "term_max": 40, "sa_min": 30,  "sa_max": 100000},
    "tata":       {"age_min": 18, "age_max": 65, "term_min": 10, "term_max": 40, "sa_min": 50,  "sa_max": 100000},
    "aviva":      {"age_min": 18, "age_max": 60, "term_min": 10, "term_max": 35, "sa_min": 25,  "sa_max": 100000},
    "hdfc":       {"age_min": 18, "age_max": 65, "term_min": 10, "term_max": 40, "sa_min": 50,  "sa_max": 20000},
    "icici":      {"age_min": 18, "age_max": 65, "term_min": 5,  "term_max": 40, "sa_min": 50,  "sa_max": 20000},
    "sbi":        {"age_min": 18, "age_max": 65, "term_min": 5,  "term_max": 40, "sa_min": 35,  "sa_max": 20000},
    "star_union": {"age_min": 18, "age_max": 65, "term_min": 10, "term_max": 30, "sa_min": 25,  "sa_max": 50000},
    "canara":     {"age_min": 18, "age_max": 65, "term_min": 5,  "term_max": 40, "sa_min": 25,  "sa_max": 100000},
    "india_first":{"age_min": 18, "age_max": 65, "term_min": 5,  "term_max": 40, "sa_min": 50,  "sa_max": 100000},
    "future":     {"age_min": 18, "age_max": 65, "term_min": 10, "term_max": 35, "sa_min": 25,  "sa_max": 100000},
    "edelweiss":  {"age_min": 18, "age_max": 65, "term_min": 10, "term_max": 40, "sa_min": 25,  "sa_max": 100000},
    "axis":       {"age_min": 18, "age_max": 65, "term_min": 10, "term_max": 50, "sa_min": 25,  "sa_max": 100000},
}
DEFAULT_META = {"age_min": 18, "age_max": 65, "term_min": 10, "term_max": 40, "sa_min": 25, "sa_max": 100000}

FEATURES_MAP = {
    "max":       "Highest CSR in private sector|Critical illness rider|Terminal illness|Accidental death|Joint life cover",
    "aegon":     "Affordable premiums|Return of premium option|Critical illness|Accidental death|Income benefit",
    "bharti":    "Comprehensive cover|Critical illness|Accidental death|Income benefit|Waiver of premium",
    "lic":       "Government-backed|Trusted brand|Return of premium option|Accidental death benefit|Pan-India reach",
    "pramerica": "Flexible cover options|Critical illness|Accidental death|Return of premium|Easy online process",
    "exide":     "Affordable premiums|Flexible payout|Critical illness|Accidental death|Online process",
    "kotak":     "Low premiums|3 plan options|Critical illness optional|Accidental death benefit|Online discount",
    "reliance":  "Affordable premiums|Flexible SA|Critical illness|Accidental death|Online purchase",
    "bajaj":     "Discount on high sum assured|Flexible payout options|Cover continuance|Critical illness rider|Online",
    "pnb":       "Flexible cover options|Critical illness|Accidental death|Return of premium|Family income benefit",
    "aditya":    "Comprehensive protection|Critical illness|Accidental death|Income benefit|Waiver of premium",
    "tata":      "100% Return of premiums|Affordable premiums|Surrender benefit|Critical illness|Accidental death",
    "aviva":     "Multiple options|Critical illness|Accidental death|Return of premium|Flexible payment",
    "hdfc":      "Life & CI Rebalance|Income benefit option|Return of premium|Waiver on disability|Cover till age 85",
    "icici":     "4 plan options|Critical illness cover|Accidental death benefit|Waiver of premium|Terminal illness",
    "sbi":       "3 plan options|Increasing cover|Level cover|Return of premium|Flexible premium payment",
    "star_union":"Affordable premiums|Simple process|Death benefit|Annual premium payment|Basic cover",
    "canara":    "Flexible cover options|Increasing cover|Critical illness add-on|Return of premium|Joint life cover",
    "india_first":"Online term plan|Critical illness|Accidental death|Flexible payout|Affordable premiums",
    "future":    "Affordable premiums|Flexible payout|Critical illness|Accidental death|Online process",
    "edelweiss": "Total Protect Plus|Critical illness|Accidental death|Income benefit|Waiver of premium",
    "axis":      "7 plan options|Cover continuance benefit|Critical illness|Joint life cover|Return of premium",
}

PROVIDER_URL_MAP = {
    "max":       "https://www.maxlifeinsurance.com/term-insurance-plans/smart-secure-plus-plan",
    "aegon":     "https://www.aegonlife.com/insurance-products/iTerm-Prime",
    "bharti":    "https://www.bharti-axalife.com/products/protection/smart-jeevan-plan",
    "lic":       "https://www.licindia.in/Products/Insurance-Plan/lic-tech-term",
    "pramerica": "https://www.bandhanlife.com/term-insurance",
    "exide":     "https://www.hdfclife.com/term-insurance-plans",
    "kotak":     "https://www.kotaklife.com/online-plans/term-insurance/kotak-e-term",
    "reliance":  "https://www.reliancenipponlife.com/term-insurance/digi-term-plan.html",
    "bajaj":     "https://www.bajajallianzlife.com/term-insurance/etouch-online-term-plan.html",
    "pnb":       "https://www.pnbmetlife.com/products/protection/mera-term-plan-plus.html",
    "aditya":    "https://lifeinsurance.adityabirlacapital.com/term-insurance/shield-plan",
    "tata":      "https://www.tataaia.com/all-products/life-insurance/term-insurance/sampoorna-raksha-promise.html",
    "aviva":     "https://www.avivaindiablog.com/life-insurance/term-insurance",
    "hdfc":      "https://www.hdfclife.com/term-insurance-plans/click-2-protect-super",
    "icici":     "https://www.iciciprulife.com/term-insurance/iprotect-smart-term-plan.html",
    "sbi":       "https://www.sbilife.co.in/en/individual-life-insurance/term-insurance/eshield-next",
    "star_union":"https://www.starunionlife.com/term-insurance",
    "canara":    "https://www.canarahsbclife.com/term-insurance",
    "india_first":"https://www.indiafirstlife.com/term-insurance",
    "future":    "https://www.futuregenerali.in/life-insurance/term-insurance",
    "edelweiss": "https://www.edelweisslife.in/term-insurance/total-protect-plus",
    "axis":      "https://www.axismaxlife.com/term-insurance/smart-term-plan-plus",
}


def _match_provider(text: str) -> str:
    t = text.lower()
    for fragment, key in PROVIDER_KEY_MAP.items():
        if fragment in t:
            return key
    return ""


def scrape_coverfox_csr() -> List[Dict]:
    """
    Scrape Coverfox's dedicated claim-settlement-ratio page.
    Returns one plan per insurer with live CSR from the 15-row table.
    """
    try:
        resp = requests.get(CSR_URL, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        tables = soup.find_all("table")
        if not tables:
            logger.warning("CoverfoxCSR: no tables on page")
            return []

        # Find the table with Insurance Provider | Claim Settlement Ratio columns
        csr_table = None
        for t in tables:
            rows = t.find_all("tr")
            if not rows:
                continue
            header = [th.get_text(strip=True).lower() for th in rows[0].find_all(["th", "td"])]
            if any("provider" in h or "insurer" in h or "insurance" in h for h in header) and \
               any("ratio" in h or "csr" in h or "claim" in h for h in header):
                csr_table = t
                break

        if not csr_table:
            logger.warning("CoverfoxCSR: CSR table not found")
            return []

        plans = []
        seen = set()
        for row in csr_table.find_all("tr")[1:]:
            cells = [td.get_text(separator=" ", strip=True) for td in row.find_all(["td", "th"])]
            if len(cells) < 2:
                continue

            provider_raw = cells[0]
            csr_raw = cells[1]

            csr_match = re.search(r"(\d{2,3}\.?\d*)\s*%", csr_raw)
            if not csr_match:
                continue
            csr = float(csr_match.group(1))

            pkey = _match_provider(provider_raw)
            if not pkey or pkey in seen:
                continue
            seen.add(pkey)

            meta = PROVIDER_META.get(pkey, DEFAULT_META)
            plan_name = PLAN_NAME_MAP.get(pkey, f"{pkey.title()} Term Plan")
            provider_display = PROVIDER_DISPLAY_MAP.get(pkey, provider_raw.strip())

            plans.append({
                "plan_name": plan_name,
                "provider": provider_display,
                "source": "coverfox_csr",
                "sum_assured_min": meta["sa_min"],
                "sum_assured_max": meta["sa_max"],
                "premium_annual": PREMIUM_MAP.get(pkey, 8500),
                "policy_term_min": meta["term_min"],
                "policy_term_max": meta["term_max"],
                "age_min": meta["age_min"],
                "age_max": meta["age_max"],
                "claim_settlement_ratio": csr,
                "key_features": FEATURES_MAP.get(pkey, "Term insurance|Death benefit|Online purchase"),
                "source_url": PROVIDER_URL_MAP.get(pkey, CSR_URL),
            })

        logger.info(f"CoverfoxCSR: scraped {len(plans)} plans")
        return plans

    except Exception as e:
        logger.warning(f"CoverfoxCSR scraper error: {e}")
        return []
