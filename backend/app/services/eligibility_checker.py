"""
Eligibility Checker Service.

Checks user eligibility for a specific scheme or ALL schemes.
Returns: Eligible / Not Eligible (binary for dashboard)
with matched/failed criteria, missing documents, confidence, and explanations.
"""

import re
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from loguru import logger

from app.models.user import User, UserDocument
from app.models.scheme import Scheme


class EligibilityChecker:
    """Checks user eligibility for government schemes using NLP rule extraction."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def check_all_schemes(
        self,
        user: User,
        page: int = 1,
        page_size: int = 50,
        search: Optional[str] = None,
        category: Optional[str] = None,
        state_filter: Optional[str] = None,
        eligibility_filter: Optional[str] = None,  # "eligible" | "ineligible" | None
    ) -> dict:
        """
        Evaluate the user against ALL active schemes.
        Returns paginated results classified as ELIGIBLE or NOT ELIGIBLE (binary).
        """
        # Build base query
        query = select(Scheme).where(Scheme.is_active == True)
        count_query = select(func.count(Scheme.id)).where(Scheme.is_active == True)

        if search:
            pattern = f"%{search}%"
            search_cond = or_(
                Scheme.scheme_name.ilike(pattern),
                Scheme.details.ilike(pattern),
                Scheme.scheme_category.ilike(pattern),
            )
            query = query.where(search_cond)
            count_query = count_query.where(search_cond)

        if category:
            cat_cond = Scheme.scheme_category.ilike(f"%{category}%")
            query = query.where(cat_cond)
            count_query = count_query.where(cat_cond)

        if state_filter:
            state_cond = or_(
                Scheme.level == "Central",
                Scheme.target_state.ilike(f"%{state_filter}%"),
                Scheme.eligibility.ilike(f"%{state_filter}%"),
                Scheme.details.ilike(f"%{state_filter}%"),
            )
            query = query.where(state_cond)
            count_query = count_query.where(state_cond)

        # Get user documents once
        doc_result = await self.db.execute(
            select(UserDocument).where(UserDocument.user_id == user.id)
        )
        user_docs = [d.document_type.lower() for d in doc_result.scalars().all()]

        # If filtering by eligibility, we need to evaluate all schemes first
        if eligibility_filter:
            # Fetch all matching schemes (no pagination yet)
            all_result = await self.db.execute(query.order_by(Scheme.scheme_name))
            all_schemes = list(all_result.scalars().all())

            eligible_schemes = []
            ineligible_schemes = []

            for scheme in all_schemes:
                result = self._evaluate_scheme(user, scheme, user_docs)
                if result["is_eligible"]:
                    eligible_schemes.append(result)
                else:
                    ineligible_schemes.append(result)

            # Sort eligible by confidence desc, ineligible by name
            eligible_schemes.sort(key=lambda x: x["confidence"], reverse=True)

            if eligibility_filter == "eligible":
                filtered = eligible_schemes
            else:
                filtered = ineligible_schemes

            total = len(filtered)
            paginated = filtered[(page - 1) * page_size : page * page_size]

            return {
                "schemes": paginated,
                "total": total,
                "page": page,
                "page_size": page_size,
                "eligible_count": len(eligible_schemes),
                "ineligible_count": len(ineligible_schemes),
            }

        # No eligibility filter — evaluate paginated schemes
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(Scheme.scheme_name).offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        schemes = list(result.scalars().all())

        evaluated = []
        eligible_count = 0
        ineligible_count = 0

        for scheme in schemes:
            eval_result = self._evaluate_scheme(user, scheme, user_docs)
            evaluated.append(eval_result)
            if eval_result["is_eligible"]:
                eligible_count += 1
            else:
                ineligible_count += 1

        # Get global counts (all schemes)
        all_result = await self.db.execute(
            select(Scheme).where(Scheme.is_active == True).order_by(Scheme.id)
        )
        all_schemes = list(all_result.scalars().all())
        total_eligible = 0
        total_ineligible = 0
        for s in all_schemes:
            r = self._evaluate_scheme(user, s, user_docs)
            if r["is_eligible"]:
                total_eligible += 1
            else:
                total_ineligible += 1

        return {
            "schemes": evaluated,
            "total": total,
            "page": page,
            "page_size": page_size,
            "eligible_count": total_eligible,
            "ineligible_count": total_ineligible,
        }

    def _evaluate_scheme(self, user: User, scheme: Scheme, user_docs: list[str]) -> dict:
        """Evaluate a single scheme for a user. Returns binary eligible/not_eligible."""
        matched = []
        failed = []
        missing_info = []
        suggestions = []

        eligibility_text = (scheme.eligibility or "").strip()
        if not eligibility_text:
            return {
                "scheme_id": scheme.id,
                "scheme_name": scheme.scheme_name,
                "slug": scheme.slug,
                "level": scheme.level,
                "scheme_category": scheme.scheme_category,
                "is_eligible": True,
                "status": "eligible",
                "confidence": 0.3,
                "score": 0.5,
                "matched_criteria": [],
                "failed_criteria": [],
                "missing_info": ["Eligibility information unavailable"],
                "missing_documents": [],
                "documents_required": (scheme.documents_required or "")[:500],
                "benefits": (scheme.benefits or "")[:500],
                "explanation": "Eligibility information unavailable for this scheme. You may still be eligible.",
                "application_link": scheme.application_link or scheme.official_website,
            }

        conditions = self._extract_conditions(eligibility_text)

        for condition in conditions:
            check_result = self._check_condition(user, condition)
            if check_result["status"] == "matched":
                matched.append(check_result["description"])
            elif check_result["status"] == "failed":
                failed.append(check_result["description"])
                if check_result.get("suggestion"):
                    suggestions.append(check_result["suggestion"])
            else:
                missing_info.append(check_result["description"])

        missing_docs = self._check_documents(scheme, user_docs)

        total_checked = len(matched) + len(failed)
        if total_checked == 0:
            score = 0.5
            confidence = 0.3
        else:
            score = len(matched) / total_checked
            confidence = min(total_checked / 5, 1.0)

        # Binary classification
        is_eligible = len(failed) == 0 and (len(matched) > 0 or total_checked == 0)

        status = "eligible" if is_eligible else "not_eligible"
        explanation = self._build_explanation(status, matched, failed, missing_docs)

        return {
            "scheme_id": scheme.id,
            "scheme_name": scheme.scheme_name,
            "slug": scheme.slug,
            "level": scheme.level,
            "scheme_category": scheme.scheme_category,
            "is_eligible": is_eligible,
            "status": status,
            "confidence": round(confidence, 4),
            "score": round(score, 4),
            "matched_criteria": matched,
            "failed_criteria": failed,
            "missing_info": missing_info,
            "missing_documents": missing_docs,
            "documents_required": (scheme.documents_required or "")[:500],
            "benefits": (scheme.benefits or "")[:500],
            "explanation": explanation,
            "application_link": scheme.application_link or scheme.official_website,
        }

    async def check_eligibility(self, user: User, scheme_id: int) -> dict:
        """
        Check if a user is eligible for a specific scheme.

        Returns:
            {
                "scheme_id": int,
                "scheme_name": str,
                "status": "eligible" | "partially_eligible" | "not_eligible",
                "score": float,
                "confidence": float,
                "matched_criteria": [...],
                "failed_criteria": [...],
                "missing_documents": [...],
                "suggestions": [...],
                "explanation": str,
            }
        """
        result = await self.db.execute(select(Scheme).where(Scheme.id == scheme_id))
        scheme = result.scalar_one_or_none()
        if not scheme:
            raise ValueError("Scheme not found")

        # Get user's documents
        doc_result = await self.db.execute(
            select(UserDocument).where(UserDocument.user_id == user.id)
        )
        user_docs = [d.document_type.lower() for d in doc_result.scalars().all()]

        matched = []
        failed = []
        suggestions = []

        # ===== Extract and check eligibility rules =====
        eligibility_text = (scheme.eligibility or "").strip()
        if not eligibility_text:
            return self._build_result(
                scheme, "eligible", 0.5, 0.3, matched, failed, [], suggestions,
                "No specific eligibility criteria found for this scheme."
            )

        # Parse eligibility into individual conditions
        conditions = self._extract_conditions(eligibility_text)

        for condition in conditions:
            check_result = self._check_condition(user, condition)
            if check_result["status"] == "matched":
                matched.append(check_result["description"])
            elif check_result["status"] == "failed":
                failed.append(check_result["description"])
                if check_result.get("suggestion"):
                    suggestions.append(check_result["suggestion"])
            # "unknown" conditions are skipped

        # ===== Check required documents =====
        missing_docs = self._check_documents(scheme, user_docs)

        # ===== Calculate eligibility score =====
        total = len(matched) + len(failed)
        if total == 0:
            score = 0.5
        else:
            score = len(matched) / total

        # Determine status
        if score >= 0.8 and not failed:
            status = "eligible"
        elif score >= 0.4:
            status = "partially_eligible"
        else:
            status = "not_eligible"

        # Adjust for missing documents
        if missing_docs and status == "eligible":
            status = "partially_eligible"
            suggestions.append("Upload required documents to complete your application")

        confidence = min(total / 5, 1.0)  # Higher confidence with more conditions checked

        explanation = self._build_explanation(status, matched, failed, missing_docs)

        logger.info(f"Eligibility check: user={user.id}, scheme={scheme_id}, status={status}, score={score:.2f}")

        return self._build_result(
            scheme, status, score, confidence, matched, failed, missing_docs, suggestions, explanation
        )

    async def check_scheme_for_chatbot(self, user: User, scheme_name: str) -> dict:
        """Check eligibility for a scheme by name (for chatbot use)."""
        pattern = f"%{scheme_name}%"
        result = await self.db.execute(
            select(Scheme).where(
                Scheme.is_active == True,
                Scheme.scheme_name.ilike(pattern),
            ).limit(1)
        )
        scheme = result.scalar_one_or_none()
        if not scheme:
            return {"found": False, "message": f"Scheme '{scheme_name}' not found in database."}

        doc_result = await self.db.execute(
            select(UserDocument).where(UserDocument.user_id == user.id)
        )
        user_docs = [d.document_type.lower() for d in doc_result.scalars().all()]

        eval_result = self._evaluate_scheme(user, scheme, user_docs)
        eval_result["found"] = True
        return eval_result

    async def get_eligible_schemes_for_chatbot(self, user: User, limit: int = 10) -> list[dict]:
        """Get eligible schemes for a user (for chatbot use)."""
        doc_result = await self.db.execute(
            select(UserDocument).where(UserDocument.user_id == user.id)
        )
        user_docs = [d.document_type.lower() for d in doc_result.scalars().all()]

        result = await self.db.execute(
            select(Scheme).where(Scheme.is_active == True).order_by(Scheme.view_count.desc()).limit(200)
        )
        schemes = list(result.scalars().all())

        eligible = []
        for scheme in schemes:
            eval_result = self._evaluate_scheme(user, scheme, user_docs)
            if eval_result["is_eligible"]:
                eligible.append(eval_result)
            if len(eligible) >= limit:
                break

        eligible.sort(key=lambda x: x["confidence"], reverse=True)
        return eligible

    def _extract_conditions(self, text: str) -> list[dict]:
        """Extract individual eligibility conditions from free text."""
        conditions = []

        # Split by common separators
        separators = [
            r'\.\s+(?=[A-Z])',  # Period followed by capital letter
            r'\n',
            r'(?:;)',
            r'(?:\d+[\.\)]\s)',  # Numbered lists
        ]

        parts = re.split('|'.join(separators), text)
        parts = [p.strip() for p in parts if p.strip() and len(p.strip()) > 10]

        for part in parts:
            condition = {"raw": part, "type": "unknown"}

            # Classify condition type
            part_lower = part.lower()

            if any(kw in part_lower for kw in ["age", "years old", "year of age"]):
                condition["type"] = "age"
                age_match = re.search(r'(\d+)\s*(?:to|-)\s*(\d+)\s*(?:years|yrs)', part_lower)
                if age_match:
                    condition["min_age"] = int(age_match.group(1))
                    condition["max_age"] = int(age_match.group(2))
                else:
                    age_match = re.search(r'(?:at least|minimum|above|more than)\s*(\d+)', part_lower)
                    if age_match:
                        condition["min_age"] = int(age_match.group(1))
                    age_match = re.search(r'(?:not exceed|maximum|below|less than|under)\s*(\d+)', part_lower)
                    if age_match:
                        condition["max_age"] = int(age_match.group(1))

            elif any(kw in part_lower for kw in ["income", "earning", "bpl", "poverty"]):
                condition["type"] = "income"
                income_match = re.search(r'(?:₹|rs\.?|inr)\s*([\d,]+)', part_lower)
                if income_match:
                    condition["income_limit"] = float(income_match.group(1).replace(",", ""))

            elif any(kw in part_lower for kw in ["resident", "domicile", "living in", "residing"]):
                condition["type"] = "location"

            elif any(kw in part_lower for kw in ["scheduled caste", "scheduled tribe", "obc", "sc/st", "backward"]):
                condition["type"] = "category"

            elif any(kw in part_lower for kw in ["female", "woman", "women", "girl", "male", "boy"]):
                condition["type"] = "gender"

            elif any(kw in part_lower for kw in ["farmer", "agriculture", "kisan"]):
                condition["type"] = "occupation_farmer"

            elif any(kw in part_lower for kw in ["student", "studying", "enrolled"]):
                condition["type"] = "occupation_student"

            elif any(kw in part_lower for kw in ["disability", "disabled", "handicap", "pwd"]):
                condition["type"] = "disability"

            elif any(kw in part_lower for kw in ["widow"]):
                condition["type"] = "widow"

            elif any(kw in part_lower for kw in ["senior citizen", "old age", "elderly"]):
                condition["type"] = "senior_citizen"

            elif any(kw in part_lower for kw in ["registered", "member", "enrolled"]):
                condition["type"] = "registration"

            conditions.append(condition)

        return conditions

    def _check_condition(self, user: User, condition: dict) -> dict:
        """Check a single condition against user profile."""
        cond_type = condition["type"]
        raw = condition["raw"]

        if cond_type == "age":
            if user.age is None:
                return {"status": "unknown", "description": raw}
            min_age = condition.get("min_age")
            max_age = condition.get("max_age")
            if min_age and user.age < min_age:
                return {
                    "status": "failed",
                    "description": f"Age requirement: {raw} (Your age: {user.age})",
                    "suggestion": f"Minimum age requirement is {min_age} years",
                }
            if max_age and user.age > max_age:
                return {
                    "status": "failed",
                    "description": f"Age requirement: {raw} (Your age: {user.age})",
                    "suggestion": f"Maximum age requirement is {max_age} years",
                }
            return {"status": "matched", "description": f"Age requirement met: {raw}"}

        elif cond_type == "income":
            income = user.annual_family_income or (user.income or 0) * 12
            if income == 0:
                return {"status": "unknown", "description": raw}
            limit = condition.get("income_limit")
            if limit and income > limit:
                return {
                    "status": "failed",
                    "description": f"Income limit: {raw} (Your income: ₹{income:,.0f})",
                    "suggestion": f"Annual income should not exceed ₹{limit:,.0f}",
                }
            return {"status": "matched", "description": f"Income requirement met: {raw}"}

        elif cond_type == "location":
            if not user.state:
                return {"status": "unknown", "description": raw}
            raw_lower = raw.lower()
            state_lower = user.state.lower()
            if state_lower in raw_lower or any(
                variant in raw_lower for variant in [state_lower, state_lower.replace(" ", "")]
            ):
                return {"status": "matched", "description": f"Location requirement met: {raw}"}
            # Don't fail for location — scheme text might mention state differently
            return {"status": "unknown", "description": raw}

        elif cond_type == "gender":
            if not user.gender:
                return {"status": "unknown", "description": raw}
            raw_lower = raw.lower()
            if "female" in raw_lower or "women" in raw_lower or "woman" in raw_lower:
                if user.gender.lower() in ("female", "woman"):
                    return {"status": "matched", "description": f"Gender requirement met: {raw}"}
                else:
                    return {
                        "status": "failed",
                        "description": f"Gender: {raw}",
                        "suggestion": "This scheme is for women only",
                    }
            return {"status": "unknown", "description": raw}

        elif cond_type == "category":
            if not user.category:
                return {"status": "unknown", "description": raw}
            raw_lower = raw.lower()
            cat_lower = user.category.lower()
            if cat_lower in raw_lower or any(
                kw in raw_lower for kw in [cat_lower, cat_lower.replace("/", "")]
            ):
                return {"status": "matched", "description": f"Category requirement met: {raw}"}
            return {
                "status": "failed",
                "description": f"Category: {raw} (Your category: {user.category})",
                "suggestion": f"This scheme requires specific social category",
            }

        elif cond_type == "occupation_farmer":
            if user.is_farmer:
                return {"status": "matched", "description": f"Farmer status verified: {raw}"}
            return {
                "status": "failed",
                "description": f"Farmer requirement: {raw}",
                "suggestion": "This scheme is for farmers",
            }

        elif cond_type == "occupation_student":
            if user.is_student:
                return {"status": "matched", "description": f"Student status verified: {raw}"}
            return {
                "status": "failed",
                "description": f"Student requirement: {raw}",
                "suggestion": "This scheme is for students",
            }

        elif cond_type == "disability":
            if user.is_disabled:
                return {"status": "matched", "description": f"Disability status verified: {raw}"}
            return {
                "status": "failed",
                "description": f"Disability requirement: {raw}",
                "suggestion": "This scheme requires disability certification",
            }

        elif cond_type == "widow":
            if user.is_widow:
                return {"status": "matched", "description": f"Widow status verified: {raw}"}
            return {
                "status": "failed",
                "description": f"Widow requirement: {raw}",
                "suggestion": "This scheme is for widows",
            }

        elif cond_type == "senior_citizen":
            if user.is_senior_citizen or (user.age and user.age >= 60):
                return {"status": "matched", "description": f"Senior citizen status verified: {raw}"}
            return {
                "status": "failed",
                "description": f"Senior citizen requirement: {raw}",
                "suggestion": "This scheme is for senior citizens (60+ years)",
            }

        # Default: unknown condition
        return {"status": "unknown", "description": raw}

    def _check_documents(self, scheme: Scheme, user_docs: list[str]) -> list[str]:
        """Check which required documents the user is missing."""
        missing = []
        docs_text = (scheme.documents_required or "").lower()
        if not docs_text:
            return missing

        # Common document types to check
        doc_checks = {
            "aadhaar": ["aadhaar", "aadhar", "aadhaar card"],
            "pan": ["pan card", "pan"],
            "income_certificate": ["income certificate", "income proof"],
            "caste_certificate": ["caste certificate", "category certificate"],
            "residence_certificate": ["residence certificate", "residential certificate", "domicile"],
            "bank_passbook": ["bank passbook", "bank account", "bank details"],
            "passport_photo": ["passport-size photograph", "passport size photo", "photograph"],
            "ration_card": ["ration card"],
            "birth_certificate": ["birth certificate", "date of birth"],
            "disability_certificate": ["disability certificate"],
            "voter_id": ["voter id", "electoral identity card"],
        }

        for doc_type, keywords in doc_checks.items():
            if any(kw in docs_text for kw in keywords):
                if doc_type not in user_docs:
                    # Format for display
                    display_name = doc_type.replace("_", " ").title()
                    missing.append(display_name)

        return missing

    def _build_explanation(
        self,
        status: str,
        matched: list[str],
        failed: list[str],
        missing_docs: list[str],
    ) -> str:
        """Build a human-readable explanation of the eligibility check."""
        parts = []

        if status == "eligible":
            parts.append("✅ You appear to be eligible for this scheme.")
        elif status == "partially_eligible":
            parts.append("⚠️ You may be partially eligible for this scheme.")
        else:
            parts.append("❌ You do not appear to be eligible for this scheme.")

        if matched:
            parts.append(f"\n✓ {len(matched)} condition(s) matched:")
            for m in matched[:5]:
                parts.append(f"  • {m}")

        if failed:
            parts.append(f"\n✗ {len(failed)} condition(s) not met:")
            for f in failed[:5]:
                parts.append(f"  • {f}")

        if missing_docs:
            parts.append(f"\n📄 {len(missing_docs)} document(s) needed:")
            for d in missing_docs:
                parts.append(f"  • {d}")

        return "\n".join(parts)

    def _build_result(
        self,
        scheme: Scheme,
        status: str,
        score: float,
        confidence: float,
        matched: list[str],
        failed: list[str],
        missing_docs: list[str],
        suggestions: list[str],
        explanation: str,
    ) -> dict:
        return {
            "scheme_id": scheme.id,
            "scheme_name": scheme.scheme_name,
            "status": status,
            "score": round(score, 4),
            "confidence": round(confidence, 4),
            "matched_criteria": matched,
            "failed_criteria": failed,
            "missing_documents": missing_docs,
            "suggestions": suggestions,
            "explanation": explanation,
        }
