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


def _normalize_compare_keys(comparison_table: list, plan_names: list) -> list:
    """
    Gemini often invents slightly different plan-name keys in the values dict.
    This re-maps every key back to the exact plan_name strings we passed in.
    """
    for row in comparison_table:
        raw = row.get("values")
        if not isinstance(raw, dict):
            continue
        normalized: dict = {}
        for exact_name in plan_names:
            if exact_name in raw:
                normalized[exact_name] = raw[exact_name]
                continue
            # Case-insensitive exact
            lower = exact_name.lower()
            matched = next((v for k, v in raw.items() if k.lower() == lower), None)
            if matched is not None:
                normalized[exact_name] = matched
                continue
            # Word-overlap fuzzy match
            exact_words = set(exact_name.lower().split())
            best_val, best_score = None, 0.0
            for key, val in raw.items():
                key_words = set(key.lower().split())
                overlap = len(exact_words & key_words) / max(len(exact_words | key_words), 1)
                if overlap > best_score:
                    best_score, best_val = overlap, val
            if best_val is not None and best_score > 0.25:
                normalized[exact_name] = best_val
        row["values"] = normalized
    return comparison_table


def compare_specific_plans(user_profile: Dict, plans: List[Dict]) -> Dict:
    """Compare 2–3 plans side-by-side using Gemini AI."""
    plan_names = [p["plan_name"] for p in plans]
    plans_text = json.dumps(plans, indent=2)
    # Build explicit key list so Gemini uses EXACT names
    keys_csv = ", ".join(f'"{n}"' for n in plan_names)
    prompt = f"""You are an expert Indian term insurance advisor. Compare the following plans side-by-side for this user.

USER PROFILE:
- Age: {user_profile.get('age')} years
- Desired Sum Assured: ₹{user_profile.get('sum_assured')} Lakhs
- Premium Budget: ₹{user_profile.get('premium_budget')}/year
- Policy Term: {user_profile.get('policy_term')} years

PLANS TO COMPARE:
{plans_text}

IMPORTANT: In the "values" dict of each comparison_table row, use EXACTLY these keys (copy verbatim):
{keys_csv}

Respond ONLY with valid JSON in this exact format:
{{
  "verdict": "2-3 sentences on overall winner and why",
  "winner": "Plan Name",
  "comparison_table": [
    {{
      "aspect": "Claim Settlement Ratio",
      "values": {{{", ".join(f'"{n}": "value"' for n in plan_names)}}},
      "winner_plan": "{plan_names[0]}",
      "why": "Higher CSR means more reliable claim payments"
    }}
  ],
  "detailed_comparison": [
    {{
      "plan_name": "...",
      "provider": "...",
      "strengths": ["...", "..."],
      "weaknesses": ["...", "..."],
      "best_for": "..."
    }}
  ]
}}
Include aspects: Claim Settlement Ratio, Annual Premium (approx. for ₹{user_profile.get('sum_assured')} Lakhs, {user_profile.get('policy_term')} years), Sum Assured Range, Policy Term, Key Features, Value for Money (within your budget for ₹{user_profile.get('sum_assured')} Lakhs, {user_profile.get('policy_term')} years)."""
    try:
        response = _model.generate_content(prompt)
        raw = response.text.strip()
        json_match = re.search(r"\{.*\}", raw, re.DOTALL)
        result = json.loads(json_match.group() if json_match else raw)
        # Normalize keys in comparison table to match exact plan names
        if "comparison_table" in result:
            result["comparison_table"] = _normalize_compare_keys(result["comparison_table"], plan_names)
        return result
    except Exception as e:
        logger.warning(f"Compare failed: {e}")
        return {
            "verdict": "Comparison unavailable. Please check your API key.",
            "winner": plans[0]["plan_name"] if plans else "N/A",
            "comparison_table": [],
            "detailed_comparison": [],
        }


def chat_with_advisor(message: str, user_profile: Dict, top_plans: List[Dict]) -> str:
    """Answer follow-up insurance questions using Gemini AI."""
    context_parts = []
    if user_profile:
        context_parts.append(
            f"User: Age {user_profile.get('age')}, Budget ₹{user_profile.get('premium_budget')}/yr, "
            f"Coverage ₹{user_profile.get('sum_assured')}L, Term {user_profile.get('policy_term')} yrs"
        )
    if top_plans:
        names = ", ".join(p.get("plan_name", "") for p in top_plans[:3])
        context_parts.append(f"Top plans shown: {names}")

    context = "\n".join(context_parts)
    prompt = f"""You are a helpful, friendly Indian term insurance advisor. Answer concisely in 2–4 sentences.
Be practical and specific to the Indian insurance market. No markdown, plain text only.

{context}

User question: {message}"""
    try:
        response = _model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        logger.warning(f"Chat failed: {e}")
        return "I'm unable to answer right now. Please check your Gemini API key or try again."


def estimate_premium_range(age: int, sum_assured: float, policy_term: int) -> Dict:
    """Estimate annual premium range using Gemini or rule-based calculation."""
    prompt = f"""Estimate the annual premium range in INR for an Indian non-smoker, healthy individual:
- Age: {age} years
- Sum Assured: ₹{sum_assured} Lakhs
- Policy Term: {policy_term} years

Respond ONLY with valid JSON:
{{
  "min_premium": 8000,
  "max_premium": 15000,
  "typical_premium": 11000,
  "factors": ["Age {age} - moderate risk", "Coverage ₹{sum_assured}L", "{policy_term} year term"],
  "tip": "One sentence tip to reduce premium"
}}"""
    try:
        response = _model.generate_content(prompt)
        raw = response.text.strip()
        json_match = re.search(r"\{.*\}", raw, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        return json.loads(raw)
    except Exception:
        # Rule-based fallback
        base = 0.0006 + max(0, age - 25) * 0.00003
        annual = base * sum_assured * 100000
        return {
            "min_premium": int(annual * 0.7),
            "max_premium": int(annual * 1.4),
            "typical_premium": int(annual),
            "factors": [
                f"Age {age} — {'low' if age < 35 else 'moderate' if age < 50 else 'higher'} risk",
                f"Coverage ₹{sum_assured}L",
                f"{policy_term} year term",
            ],
            "tip": "Buying at a younger age and maintaining a healthy lifestyle significantly reduces your premium.",
        }
