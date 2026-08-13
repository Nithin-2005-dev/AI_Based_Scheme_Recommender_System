"""
Hybrid Recommendation Engine with Explainable AI (XAI).

Combines:
1. Rule-Based Filtering
2. Weighted Scoring
3. TF-IDF Similarity Matching
4. Final Ranking

Returns score, confidence, matched/failed conditions, and explanations.
"""

import re
import math
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger

from app.models.user import User
from app.models.scheme import Scheme


# ===== Weights for scoring dimensions =====
WEIGHTS = {
    "income": 0.20,
    "category": 0.20,
    "occupation": 0.15,
    "education": 0.15,
    "location": 0.10,
    "gender": 0.10,
    "special_status": 0.10,
}


class RecommendationEngine:
    """
    Hybrid recommendation engine that combines rule-based filtering,
    weighted scoring, and text similarity for personalized scheme discovery.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_recommendations(
        self,
        user: User,
        top_k: int = 5,
        category_filter: Optional[str] = None,
    ) -> list[dict]:
        """
        Generate personalized recommendations for a user.

        Algorithm:
        1. Fetch all active schemes
        2. Rule-based filtering (hard filters)
        3. Weighted scoring (soft scoring)
        4. Text similarity matching
        5. Rank and return top K with explanations
        """
        # Step 1: Fetch schemes
        query = select(Scheme).where(Scheme.is_active == True)
        if category_filter:
            query = query.where(Scheme.scheme_category.ilike(f"%{category_filter}%"))
        result = await self.db.execute(query)
        schemes = result.scalars().all()

        if not schemes:
            return []

        # Step 2-4: Score each scheme
        scored_schemes = []
        for scheme in schemes:
            score_result = self._score_scheme(user, scheme)
            if score_result["total_score"] > 0.05:  # Minimum threshold
                scored_schemes.append(score_result)

        # Step 5: Sort by total_score descending
        scored_schemes.sort(key=lambda x: x["total_score"], reverse=True)

        # Return top K
        results = []
        for item in scored_schemes[:top_k]:
            scheme = item["scheme"]
            results.append({
                "scheme": scheme,
                "score": round(item["total_score"], 4),
                "confidence": round(item["confidence"], 4),
                "reasons": item["reasons"],
                "matched_conditions": item["matched"],
                "failed_conditions": item["failed"],
                "eligibility_probability": round(item["eligibility_prob"], 4),
            })

        logger.info(
            f"Generated {len(results)} recommendations for user {user.id}"
        )
        return results

    def _score_scheme(self, user: User, scheme: Scheme) -> dict:
        """Score a single scheme for a user across all dimensions."""
        scores = {}
        matched = []
        failed = []
        reasons = []

        # ===== Income Scoring =====
        income_score = self._score_income(user, scheme, matched, failed, reasons)
        scores["income"] = income_score

        # ===== Category Scoring =====
        category_score = self._score_category(user, scheme, matched, failed, reasons)
        scores["category"] = category_score

        # ===== Occupation Scoring =====
        occupation_score = self._score_occupation(user, scheme, matched, failed, reasons)
        scores["occupation"] = occupation_score

        # ===== Education Scoring =====
        education_score = self._score_education(user, scheme, matched, failed, reasons)
        scores["education"] = education_score

        # ===== Location Scoring =====
        location_score = self._score_location(user, scheme, matched, failed, reasons)
        scores["location"] = location_score

        # ===== Gender Scoring =====
        gender_score = self._score_gender(user, scheme, matched, failed, reasons)
        scores["gender"] = gender_score

        # ===== Special Status Scoring =====
        special_score = self._score_special_status(user, scheme, matched, failed, reasons)
        scores["special_status"] = special_score

        # ===== Calculate total weighted score =====
        total = sum(scores[k] * WEIGHTS[k] for k in WEIGHTS)

        # ===== Text similarity bonus =====
        text_bonus = self._text_similarity_bonus(user, scheme)
        total = 0.7 * total + 0.3 * text_bonus

        # ===== Confidence =====
        profile_fields_filled = sum(1 for v in [
            user.age, user.income, user.education, user.occupation,
            user.category, user.state, user.gender,
        ] if v is not None)
        confidence = profile_fields_filled / 7.0

        # ===== Eligibility Probability =====
        total_conditions = len(matched) + len(failed)
        eligibility_prob = len(matched) / max(total_conditions, 1)

        return {
            "scheme": scheme,
            "total_score": total,
            "confidence": confidence,
            "matched": matched,
            "failed": failed,
            "reasons": reasons,
            "eligibility_prob": eligibility_prob,
            "dimension_scores": scores,
        }

    def _score_income(self, user: User, scheme: Scheme, matched: list, failed: list, reasons: list) -> float:
        """Score income compatibility."""
        if user.annual_family_income is None and user.income is None:
            return 0.5  # Neutral if no income info

        eligibility = (scheme.eligibility or "").lower()
        user_income = user.annual_family_income or (user.income or 0) * 12

        # Extract income limits from eligibility text
        income_patterns = [
            r'income.*?(?:not exceed|less than|below|upto|up to|maximum).*?(?:₹|rs\.?|inr)\s*([\d,]+)',
            r'(?:₹|rs\.?|inr)\s*([\d,]+).*?(?:income|annual)',
            r'annual.*?income.*?([\d,]+)',
        ]

        for pattern in income_patterns:
            match = re.search(pattern, eligibility)
            if match:
                try:
                    limit = float(match.group(1).replace(",", ""))
                    if user_income <= limit:
                        matched.append(f"Income ₹{user_income:,.0f} is within limit ₹{limit:,.0f}")
                        reasons.append(f"Your income qualifies (under ₹{limit:,.0f} limit)")
                        return 1.0
                    else:
                        failed.append(f"Income ₹{user_income:,.0f} exceeds limit ₹{limit:,.0f}")
                        return 0.1
                except ValueError:
                    pass

        # Check for keywords suggesting income relevance
        income_keywords = ["bpl", "below poverty", "low income", "economically weaker", "ews"]
        for kw in income_keywords:
            if kw in eligibility:
                if user_income and user_income < 250000:
                    matched.append(f"Income qualifies for {kw.upper()} criteria")
                    reasons.append(f"Your income level matches {kw.upper()} requirements")
                    return 0.9
                else:
                    failed.append(f"May not qualify for {kw.upper()} criteria")
                    return 0.2

        return 0.5  # Neutral

    def _score_category(self, user: User, scheme: Scheme, matched: list, failed: list, reasons: list) -> float:
        """Score social category match (SC/ST/OBC/General)."""
        if not user.category:
            return 0.5

        eligibility = (scheme.eligibility or "").lower()
        category_lower = user.category.lower()
        scheme_category = (scheme.scheme_category or "").lower()

        # Check for specific category mentions
        category_mappings = {
            "sc": ["scheduled caste", "sc ", "sc/", "dalit"],
            "st": ["scheduled tribe", "st ", "st/", "tribal", "adivasi"],
            "obc": ["other backward", "obc", "backward class"],
            "general": ["general category", "unreserved"],
        }

        for cat, keywords in category_mappings.items():
            for kw in keywords:
                if kw in eligibility or kw in scheme_category:
                    if cat in category_lower or category_lower in cat:
                        matched.append(f"Category '{user.category}' matches scheme requirement")
                        reasons.append(f"This scheme is specifically for {user.category} category")
                        return 1.0
                    else:
                        failed.append(f"Scheme targets {cat.upper()} category, you are {user.category}")
                        return 0.1

        # Check minority scheme
        if user.minority_status and "minority" in (eligibility + scheme_category):
            matched.append("Minority status matches scheme requirement")
            reasons.append("This scheme supports minority communities")
            return 1.0

        return 0.5

    def _score_occupation(self, user: User, scheme: Scheme, matched: list, failed: list, reasons: list) -> float:
        """Score occupation relevance."""
        if not user.occupation:
            return 0.5

        eligibility = (scheme.eligibility or "").lower()
        details = (scheme.details or "").lower()
        combined = eligibility + " " + details
        occupation_lower = user.occupation.lower()

        occupation_keywords = {
            "farmer": ["farmer", "agriculture", "kisan", "farming", "cultivator", "crop"],
            "student": ["student", "scholar", "education", "academic", "college", "university"],
            "teacher": ["teacher", "faculty", "educator", "professor"],
            "worker": ["worker", "labour", "labor", "construction", "factory"],
            "business": ["business", "entrepreneur", "msme", "startup", "enterprise", "self-employed"],
            "fisherman": ["fisherman", "fishermen", "fishing", "marine"],
            "artisan": ["artisan", "handicraft", "weaver", "handloom"],
            "doctor": ["doctor", "medical", "health professional"],
        }

        for occ, keywords in occupation_keywords.items():
            for kw in keywords:
                if kw in combined:
                    if occ in occupation_lower or any(k in occupation_lower for k in keywords):
                        matched.append(f"Occupation '{user.occupation}' matches scheme target")
                        reasons.append(f"This scheme is relevant to your occupation as {user.occupation}")
                        return 1.0

        # General keyword match
        if occupation_lower in combined:
            matched.append(f"Occupation '{user.occupation}' mentioned in scheme")
            reasons.append(f"Your occupation '{user.occupation}' is mentioned in scheme details")
            return 0.8

        return 0.4

    def _score_education(self, user: User, scheme: Scheme, matched: list, failed: list, reasons: list) -> float:
        """Score education level compatibility."""
        if not user.education:
            return 0.5

        eligibility = (scheme.eligibility or "").lower()
        scheme_cat = (scheme.scheme_category or "").lower()
        education_lower = user.education.lower()

        if "education" in scheme_cat or "scholarship" in scheme_cat:
            if user.is_student:
                matched.append("Student status matches education scheme")
                reasons.append("This education scheme matches your student profile")
                return 1.0

        education_levels = {
            "10th": ["class 10", "10th", "ssc", "secondary", "high school"],
            "12th": ["class 12", "12th", "hsc", "higher secondary", "intermediate"],
            "graduate": ["graduate", "graduation", "bachelor", "degree", "b.a", "b.sc", "b.com", "b.tech"],
            "post-graduate": ["post-graduate", "postgraduate", "master", "m.a", "m.sc", "m.tech", "mba"],
            "phd": ["phd", "doctorate", "doctoral"],
        }

        for level, keywords in education_levels.items():
            for kw in keywords:
                if kw in eligibility:
                    if level in education_lower or any(k in education_lower for k in keywords):
                        matched.append(f"Education level '{user.education}' meets requirement")
                        reasons.append(f"Your education ({user.education}) qualifies")
                        return 0.9

        return 0.5

    def _score_location(self, user: User, scheme: Scheme, matched: list, failed: list, reasons: list) -> float:
        """Score location match."""
        if not user.state:
            return 0.5

        if scheme.level == "Central":
            matched.append("Central government scheme — available nationwide")
            reasons.append("This is a central government scheme available in all states")
            return 0.8

        # State-level scheme
        eligibility = (scheme.eligibility or "").lower()
        details = (scheme.details or "").lower()
        combined = eligibility + " " + details
        user_state = user.state.lower()

        # Map of state names and common variants
        state_variants = {
            "andhra pradesh": ["andhra pradesh", "ap"],
            "karnataka": ["karnataka"],
            "tamil nadu": ["tamil nadu", "tamilnadu", "tn"],
            "kerala": ["kerala"],
            "maharashtra": ["maharashtra"],
            "rajasthan": ["rajasthan"],
            "uttar pradesh": ["uttar pradesh", "up"],
            "madhya pradesh": ["madhya pradesh", "mp"],
            "west bengal": ["west bengal", "wb"],
            "gujarat": ["gujarat"],
            "bihar": ["bihar"],
            "chhattisgarh": ["chhattisgarh", "chattisgarh"],
            "jharkhand": ["jharkhand"],
            "odisha": ["odisha", "orissa"],
            "punjab": ["punjab"],
            "haryana": ["haryana"],
            "telangana": ["telangana"],
            "assam": ["assam"],
            "goa": ["goa"],
            "puducherry": ["puducherry", "pondicherry"],
            "delhi": ["delhi", "new delhi"],
        }

        for state, variants in state_variants.items():
            if any(v in user_state for v in variants):
                if any(v in combined for v in variants):
                    matched.append(f"State '{user.state}' matches scheme location")
                    reasons.append(f"This scheme is available in {user.state}")
                    return 1.0

        # If state not mentioned, might not be for user's state
        if scheme.level == "State":
            failed.append(f"State scheme may not cover {user.state}")
            return 0.2

        return 0.5

    def _score_gender(self, user: User, scheme: Scheme, matched: list, failed: list, reasons: list) -> float:
        """Score gender compatibility."""
        if not user.gender:
            return 0.5

        eligibility = (scheme.eligibility or "").lower()
        scheme_cat = (scheme.scheme_category or "").lower()
        combined = eligibility + " " + scheme_cat

        women_keywords = ["women", "woman", "female", "girl", "mahila", "stree", "lady", "ladies"]
        men_keywords = ["male only", "men only", "boys only"]

        is_women_scheme = any(kw in combined for kw in women_keywords)
        is_men_scheme = any(kw in combined for kw in men_keywords)

        if is_women_scheme:
            if user.gender.lower() in ("female", "woman"):
                matched.append("Gender matches women-specific scheme")
                reasons.append("This scheme is specifically designed for women")
                return 1.0
            else:
                failed.append("This scheme is for women only")
                return 0.0

        if is_men_scheme:
            if user.gender.lower() in ("male", "man"):
                matched.append("Gender matches male-specific scheme")
                return 1.0
            else:
                failed.append("This scheme is for men only")
                return 0.0

        return 0.5

    def _score_special_status(self, user: User, scheme: Scheme, matched: list, failed: list, reasons: list) -> float:
        """Score special status flags (farmer, widow, disabled, etc.)."""
        eligibility = (scheme.eligibility or "").lower()
        details = (scheme.details or "").lower()
        scheme_cat = (scheme.scheme_category or "").lower()
        combined = eligibility + " " + details + " " + scheme_cat
        score = 0.5

        status_checks = [
            (user.is_farmer, ["farmer", "kisan", "agriculture", "crop", "cultivation"], "farmer"),
            (user.is_student, ["student", "scholarship", "academic"], "student"),
            (user.is_widow, ["widow", "vidhwa"], "widow"),
            (user.is_senior_citizen, ["senior citizen", "old age", "elderly", "pension"], "senior citizen"),
            (user.is_pregnant_woman, ["pregnant", "maternity", "maternal"], "pregnant woman"),
            (user.is_disabled, ["disability", "disabled", "handicap", "divyang", "pwd"], "person with disability"),
            (user.is_business_owner, ["business", "entrepreneur", "msme", "startup"], "business owner"),
        ]

        for status_flag, keywords, label in status_checks:
            if any(kw in combined for kw in keywords):
                if status_flag:
                    matched.append(f"Your status as {label} matches scheme requirement")
                    reasons.append(f"This scheme specifically supports {label}s")
                    score = max(score, 1.0)
                elif status_flag is False and any(kw in eligibility for kw in keywords):
                    # Only penalize if it's explicitly required in eligibility
                    if any(f"must be a {kw}" in eligibility or f"should be a {kw}" in eligibility for kw in keywords):
                        failed.append(f"Scheme requires {label} status")
                        score = min(score, 0.1)

        return score

    def _text_similarity_bonus(self, user: User, scheme: Scheme) -> float:
        """Calculate text-based similarity between user profile and scheme."""
        user_text_parts = []
        if user.occupation:
            user_text_parts.append(user.occupation)
        if user.education:
            user_text_parts.append(user.education)
        if user.category:
            user_text_parts.append(user.category)
        if user.state:
            user_text_parts.append(user.state)
        if user.is_farmer:
            user_text_parts.append("farmer agriculture")
        if user.is_student:
            user_text_parts.append("student education")
        if user.is_disabled:
            user_text_parts.append("disability disabled")
        if user.is_widow:
            user_text_parts.append("widow")
        if user.is_senior_citizen:
            user_text_parts.append("senior citizen elderly")
        if user.is_business_owner:
            user_text_parts.append("business entrepreneur")

        if not user_text_parts:
            return 0.3

        user_text = " ".join(user_text_parts).lower()
        scheme_text = " ".join([
            scheme.eligibility or "",
            scheme.details or "",
            scheme.scheme_category or "",
        ]).lower()

        # Simple word overlap similarity
        user_words = set(user_text.split())
        scheme_words = set(scheme_text.split())

        if not user_words or not scheme_words:
            return 0.3

        intersection = user_words & scheme_words
        union = user_words | scheme_words
        jaccard = len(intersection) / len(union) if union else 0

        return min(jaccard * 5, 1.0)  # Scale up and cap at 1.0
