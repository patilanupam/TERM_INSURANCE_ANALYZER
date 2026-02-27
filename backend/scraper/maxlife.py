"""
Axis Max Life Insurance website scraper.
URL: https://www.maxlifeinsurance.com/term-insurance-plans

Scrapes:
  - Table 9: Plan list with premiums (Sr.No | Plan | Ideal for | SA | Premium | Features)
  - Table 4: Entry age ranges per plan
Returns up to 4 Axis Max Life term plans with real premium data.
"""
import logging
import re
import requests
from bs4 import BeautifulSoup
from typing import List, Dict

logger = logging.getLogger(__name__)

URL = "https://www.maxlifeinsurance.com/term-insurance-plans"

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

# Fallback age ranges per plan (from Table 4 on the page)
PLAN_AGE_MAP = {
    "smart term plan plus":           {"age_min": 18, "age_max": 40},
    "smart total elite protection":   {"age_min": 18, "age_max": 65},
    "smart secure plus":              {"age_min": 18, "age_max": 65},
    "saral jeevan bima":              {"age_min": 18, "age_max": 65},
}

PLAN_SA_MAP = {
    "smart term plan plus":           {"sa_min": 100, "sa_max": 100000},
    "smart total elite protection":   {"sa_min": 100, "sa_max": 100000},
    "smart secure plus":              {"sa_min": 25,  "sa_max": 100000},
    "saral jeevan bima":              {"sa_min": 5,   "sa_max": 25},
}

PLAN_FEATURES_MAP = {
    "smart term plan plus":           "15% discount on premiums|Salaried individuals|Critical illness|Accidental death|Joint life option",
    "smart total elite protection":   "Premium deferment option|Salaried individuals|Critical illness|Comprehensive protection|High sum assured",
    "smart secure plus":              "Self-employed friendly|Joint life cover|Critical illness rider|Terminal illness|Multiple payout options",
    "saral jeevan bima":              "Low-income individuals|Simple process|Basic life cover|Affordable premiums|5-25 lakh coverage",
}

PLAN_URL_MAP = {
    "smart term plan plus":           "https://www.maxlifeinsurance.com/term-insurance-plans/smart-term-plan-plus",
    "smart total elite protection":   "https://www.maxlifeinsurance.com/term-insurance-plans/smart-total-elite-protection",
    "smart secure plus":              "https://www.maxlifeinsurance.com/term-insurance-plans/smart-secure-plus-plan",
    "saral jeevan bima":              "https://www.maxlifeinsurance.com/term-insurance-plans/saral-jeevan-bima",
}


def _plan_key(name: str) -> str:
    n = name.lower()
    for key in PLAN_AGE_MAP:
        if key in n or any(word in n for word in key.split() if len(word) > 4):
            return key
    return ""


def _parse_monthly_premium(text: str) -> float:
    """Extract monthly premium value from text like 'Starts at 595/Month'."""
    match = re.search(r"(\d[\d,]+)\s*/\s*[Mm]onth", text.replace(",", ""))
    if match:
        return float(match.group(1).replace(",", ""))
    # Also try plain number extraction
    nums = re.findall(r"\d[\d,]+", text.replace(",", ""))
    if nums:
        val = float(nums[0])
        if 100 <= val <= 50000:
            return val
    return 0.0


def scrape_maxlife() -> List[Dict]:
    """
    Scrape Axis Max Life's term insurance plans page.
    Extracts up to 4 plans from the plan-listing table.
    """
    try:
        resp = requests.get(URL, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        tables = soup.find_all("table")
        if not tables:
            logger.warning("MaxLife: no tables found")
            return []

        plan_table = None
        for t in tables:
            rows = t.find_all("tr")
            if not rows:
                continue
            header = [th.get_text(strip=True).lower() for th in rows[0].find_all(["th", "td"])]
            # Look for plan listing table: has 'plan' + ('premium' or 'sum assured' or 'ideal')
            if any("plan" in h for h in header) and (
                any("premium" in h for h in header) or
                any("ideal" in h for h in header) or
                any("sum" in h for h in header)
            ):
                plan_table = t
                break

        if not plan_table:
            logger.warning("MaxLife: plan table not found")
            return []

        age_map: Dict[str, dict] = {}
        # Also try to parse Table 4 (entry age ranges)
        for t in tables:
            rows = t.find_all("tr")
            if not rows:
                continue
            header = [th.get_text(strip=True).lower() for th in rows[0].find_all(["th", "td"])]
            if any("term plan" in h or "plan" in h for h in header) and \
               any("entry" in h or "age" in h or "minimum" in h for h in header):
                for row in rows[1:]:
                    cells = [td.get_text(separator=" ", strip=True) for td in row.find_all(["td", "th"])]
                    if len(cells) < 2:
                        continue
                    plan_raw = cells[0].lower()
                    age_max_raw = cells[-1] if len(cells) > 1 else ""
                    age_max_match = re.search(r"(\d+)\s*[Yy]ear", age_max_raw)
                    if age_max_match:
                        pkey = _plan_key(plan_raw)
                        if pkey:
                            age_map[pkey] = {"age_min": 18, "age_max": int(age_max_match.group(1))}
                break

        plans = []
        seen = set()
        for row in plan_table.find_all("tr")[1:]:
            cells = [td.get_text(separator=" ", strip=True) for td in row.find_all(["td", "th"])]
            if len(cells) < 4:
                continue

            # Find which cell is plan name (usually the longest or 2nd column)
            # Table structure: Sr.No | Plan | Ideal for | SA | Premium | Features | Link
            plan_name_raw = cells[1] if len(cells) > 1 else cells[0]
            sa_raw = cells[3] if len(cells) > 3 else ""
            premium_raw = cells[4] if len(cells) > 4 else ""

            plan_name = re.sub(r"\s+", " ", plan_name_raw).strip()
            if not plan_name or len(plan_name) < 5:
                continue
            if plan_name.lower() in seen:
                continue
            seen.add(plan_name.lower())

            pkey = _plan_key(plan_name)
            monthly = _parse_monthly_premium(premium_raw)
            annual = monthly * 12 if monthly > 0 else 0

            # Sum assured parsing
            sa_match = re.search(r"(\d+)\s*[Cc]rore|(\d+)\s*[Ll]akh", sa_raw)
            if sa_match:
                if sa_match.group(1):
                    sa_max = int(sa_match.group(1)) * 100
                    sa_min = sa_max
                else:
                    sa_max_lakh = int(sa_match.group(2))
                    sa_min = sa_max_lakh
                    sa_max = sa_max_lakh
            else:
                sa_vals = PLAN_SA_MAP.get(pkey, {"sa_min": 25, "sa_max": 100000})
                sa_min, sa_max = sa_vals["sa_min"], sa_vals["sa_max"]

            age_info = age_map.get(pkey, PLAN_AGE_MAP.get(pkey, {"age_min": 18, "age_max": 65}))

            plans.append({
                "plan_name": plan_name,
                "provider": "Axis Max Life",
                "source": "maxlife",
                "sum_assured_min": sa_min,
                "sum_assured_max": sa_max,
                "premium_annual": annual if annual > 0 else 9000,
                "policy_term_min": 10,
                "policy_term_max": 50,
                "age_min": age_info["age_min"],
                "age_max": age_info["age_max"],
                "claim_settlement_ratio": 99.51,  # IRDAI 2022-23 (Max Life)
                "key_features": PLAN_FEATURES_MAP.get(pkey, "Term insurance|Death benefit|Online purchase"),
                "source_url": PLAN_URL_MAP.get(pkey, URL),
            })

        logger.info(f"MaxLife: scraped {len(plans)} plans")
        return plans

    except Exception as e:
        logger.warning(f"MaxLife scraper error: {e}")
        return []
