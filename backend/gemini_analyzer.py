"""
Gemini LLM integration for analyzing and ranking term insurance plans.
Uses google-generativeai (gemini-1.5-flash) to produce structured recommendations.
"""
import json
import logging
import os
import re
from typing import List, Dict, Any

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

genai.configure(api_key=os.getenv("GEMINI_API_KEY", ""))
_model = genai.GenerativeModel("gemini-2.5-flash-lite")

# Ordered fallback list in case a model hits quota
_MODEL_FALLBACKS = [
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-flash-lite-latest",
    "gemini-flash-latest",
]


def _get_working_model():
    """Return the first model that responds without quota errors."""
    for name in _MODEL_FALLBACKS:
        try:
            m = genai.GenerativeModel(name)
            m.generate_content("hi")
            return m
        except Exception as e:
            if "404" in str(e) or "not found" in str(e).lower():
                continue
            if "429" in str(e) or "quota" in str(e).lower():
                continue
    return None


def _build_prompt(user: Dict, plans: List[Dict]) -> str:
    plans_text = json.dumps(plans, indent=2)
    return f"""
You are an expert Indian term insurance advisor. Analyze the following term insurance plans and recommend the best ones for the user described below.

USER PROFILE:
- Age: {user['age']} years
- Desired Sum Assured: ₹{user['sum_assured']} Lakhs
- Maximum Annual Premium Budget: ₹{user['premium_budget']}
- Desired Policy Term: {user['policy_term']} years
- Minimum Claim Settlement Ratio preferred: {user['min_csr']}%

AVAILABLE PLANS (filtered for this user's age):
{plans_text}

INSTRUCTIONS:
1. Rank ALL plans from best to worst for this specific user.
2. For each plan provide: rank, plan_name, provider, reason (2-3 sentences explaining why it suits or doesn't suit the user), score (0-100), and a pros/cons list.
3. Give an overall_summary paragraph (3-4 sentences) explaining the top recommendation clearly.
4. Consider: claim settlement ratio, premium affordability, policy term match, sum assured coverage, and key features.
5. If a plan's premium exceeds the budget, flag it clearly.

Respond ONLY with valid JSON in this exact format:
{{
  "overall_summary": "...",
  "top_pick": "Plan Name by Provider",
  "ranked_plans": [
    {{
      "rank": 1,
      "plan_name": "...",
      "provider": "...",
      "score": 92,
      "reason": "...",
      "pros": ["...", "..."],
      "cons": ["...", "..."],
      "within_budget": true,
      "claim_settlement_ratio": 99.5
    }}
  ]
}}
"""


def analyze_plans(user_inputs: Dict[str, Any], plans: List[Dict]) -> Dict:
    """
    Send user inputs + plans to Gemini and return structured recommendation.
    Falls back to a simple sort-based recommendation if Gemini is unavailable.
    """
    if not plans:
        return {
            "overall_summary": "No plans available in the database. Please trigger a scrape first.",
            "top_pick": "N/A",
            "ranked_plans": [],
        }

    # Filter plans suitable for user's age
    age = user_inputs.get("age", 30)
    eligible = [
        p for p in plans if p.get("age_min", 0) <= age <= p.get("age_max", 99)
    ]
    if not eligible:
        eligible = plans  # fallback: use all

    # Build plan dicts for the prompt (only relevant fields)
    plan_summaries = [
        {
            "plan_name": p["plan_name"],
            "provider": p["provider"],
            "premium_annual": p["premium_annual"],
            "sum_assured_min_lakhs": p["sum_assured_min"],
            "sum_assured_max_lakhs": p["sum_assured_max"],
            "policy_term_min": p["policy_term_min"],
            "policy_term_max": p["policy_term_max"],
            "claim_settlement_ratio": p["claim_settlement_ratio"],
            "key_features": p.get("key_features", "").split("|"),
        }
        for p in eligible
    ]

    prompt = _build_prompt(user_inputs, plan_summaries)

    try:
        active_model = _model
        response = active_model.generate_content(prompt)
        raw = response.text.strip()

        # Extract JSON from response (handles markdown code blocks)
        json_match = re.search(r"\{.*\}", raw, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        return json.loads(raw)

    except Exception as e:
        # On quota/rate-limit, try other models automatically
        if "429" in str(e) or "quota" in str(e).lower() or "404" in str(e):
            logger.warning(f"Primary model failed ({e}). Trying fallback models...")
            for model_name in _MODEL_FALLBACKS[1:]:
                try:
                    m = genai.GenerativeModel(model_name)
                    response = m.generate_content(prompt)
                    raw = response.text.strip()
                    json_match = re.search(r"\{.*\}", raw, re.DOTALL)
                    if json_match:
                        return json.loads(json_match.group())
                    return json.loads(raw)
                except Exception as fe:
                    logger.warning(f"Fallback model {model_name} also failed: {fe}")
                    continue
        logger.warning(f"All Gemini models failed: {e}. Using rule-based ranking.")
        return _fallback_ranking(user_inputs, eligible)


def _fallback_ranking(user_inputs: Dict, plans: List[Dict]) -> Dict:
    """Simple rule-based ranking when Gemini is unavailable."""
    budget = user_inputs.get("premium_budget", float("inf"))
    min_csr = user_inputs.get("min_csr", 0)

    def score(p):
        s = p.get("claim_settlement_ratio", 0) * 0.5
        if p.get("premium_annual", 0) <= budget:
            s += 30
        if p.get("claim_settlement_ratio", 0) >= min_csr:
            s += 20
        return s

    sorted_plans = sorted(plans, key=score, reverse=True)
    ranked = []
    for i, p in enumerate(sorted_plans, 1):
        within_budget = p.get("premium_annual", 0) <= budget
        ranked.append(
            {
                "rank": i,
                "plan_name": p["plan_name"],
                "provider": p["provider"],
                "score": round(score(p), 1),
                "reason": (
                    f"{'Within budget. ' if within_budget else 'Exceeds budget. '}"
                    f"Claim settlement ratio: {p.get('claim_settlement_ratio', 0)}%."
                ),
                "pros": p.get("key_features", "").split("|")[:3],
                "cons": ["Gemini analysis unavailable — rule-based ranking only"],
                "within_budget": within_budget,
                "claim_settlement_ratio": p.get("claim_settlement_ratio", 0),
            }
        )

    top = sorted_plans[0] if sorted_plans else {}
    return {
        "overall_summary": (
            f"Based on rule-based analysis (Gemini unavailable), "
            f"'{top.get('plan_name', 'N/A')}' by {top.get('provider', 'N/A')} "
            f"ranks highest with a CSR of {top.get('claim_settlement_ratio', 0)}%. "
            "Please configure your Gemini API key for detailed AI analysis."
        ),
        "top_pick": f"{top.get('plan_name', 'N/A')} by {top.get('provider', 'N/A')}",
        "ranked_plans": ranked,
    }
