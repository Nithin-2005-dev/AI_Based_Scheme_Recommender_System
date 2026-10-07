"""
Authoritative Eligibility & Normalization Rules.
Single Source of Truth for GovScheme AI:
- Normalizes states, categories, and applicant profiles
- Enforces strict hard-eligibility gates
- Guarantees invariant: Ineligible user -> eligibility_percentage = 0, eligible = False
- Provides language detection for multilingual queries
"""

import re
from typing import Optional, Tuple, List, Dict, Any
from app.models.user import User
from app.models.scheme import Scheme


# ===== State Aliases & Normalization Map =====
STATE_ALIASES: Dict[str, str] = {
    # Andhra Pradesh
    "andhra pradesh": "Andhra Pradesh",
    "andhra": "Andhra Pradesh",
    "ap": "Andhra Pradesh",
    # Telangana
    "telangana": "Telangana",
    "ts": "Telangana",
    "tg": "Telangana",
    # Tamil Nadu
    "tamil nadu": "Tamil Nadu",
    "tamilnadu": "Tamil Nadu",
    "tn": "Tamil Nadu",
    # Karnataka
    "karnataka": "Karnataka",
    "ka": "Karnataka",
    # Kerala
    "kerala": "Kerala",
    "kl": "Kerala",
    # Maharashtra
    "maharashtra": "Maharashtra",
    "mh": "Maharashtra",
    # Gujarat
    "gujarat": "Gujarat",
    "gj": "Gujarat",
    # Rajasthan
    "rajasthan": "Rajasthan",
    "rj": "Rajasthan",
    # Uttar Pradesh
    "uttar pradesh": "Uttar Pradesh",
    "up": "Uttar Pradesh",
    # Madhya Pradesh
    "madhya pradesh": "Madhya Pradesh",
    "mp": "Madhya Pradesh",
    # West Bengal
    "west bengal": "West Bengal",
    "wb": "West Bengal",
    # Bihar
    "bihar": "Bihar",
    "br": "Bihar",
    # Odisha
    "odisha": "Odisha",
    "orissa": "Odisha",
    "od": "Odisha",
    "or": "Odisha",
    # Punjab
    "punjab": "Punjab",
    "pb": "Punjab",
    # Haryana
    "haryana": "Haryana",
    "hr": "Haryana",
    # Chhattisgarh
    "chhattisgarh": "Chhattisgarh",
    "chattisgarh": "Chhattisgarh",
    "cg": "Chhattisgarh",
    "ct": "Chhattisgarh",
    # Jharkhand
    "jharkhand": "Jharkhand",
    "jh": "Jharkhand",
    # Assam
    "assam": "Assam",
    "as": "Assam",
    # Goa
    "goa": "Goa",
    "ga": "Goa",
    # Himachal Pradesh
    "himachal pradesh": "Himachal Pradesh",
    "hp": "Himachal Pradesh",
    # Uttarakhand
    "uttarakhand": "Uttarakhand",
    "uttaranchal": "Uttarakhand",
    "uk": "Uttarakhand",
    "ua": "Uttarakhand",
    # Jammu and Kashmir
    "jammu and kashmir": "Jammu and Kashmir",
    "j&k": "Jammu and Kashmir",
    "jk": "Jammu and Kashmir",
    # Delhi
    "delhi": "Delhi",
    "new delhi": "Delhi",
    "dl": "Delhi",
    # Puducherry
    "puducherry": "Puducherry",
    "pondicherry": "Puducherry",
    "py": "Puducherry",
    # Ladakh
    "ladakh": "Ladakh",
    # Chandigarh
    "chandigarh": "Chandigarh",
    # Other states & UTs
    "tripura": "Tripura",
    "manipur": "Manipur",
    "meghalaya": "Meghalaya",
    "mizoram": "Mizoram",
    "nagaland": "Nagaland",
    "sikkim": "Sikkim",
    "arunachal pradesh": "Arunachal Pradesh",
    "andaman and nicobar": "Andaman and Nicobar",
    "dadra and nagar haveli": "Dadra and Nagar Haveli",
    "daman and diu": "Daman and Diu",
    "lakshadweep": "Lakshadweep",
}

# ===== Category Normalization Map =====
CATEGORY_ALIASES: Dict[str, str] = {
    "sc": "SC",
    "scheduled caste": "SC",
    "scheduled castes": "SC",
    "dalit": "SC",
    "st": "ST",
    "scheduled tribe": "ST",
    "scheduled tribes": "ST",
    "tribal": "ST",
    "adivasi": "ST",
    "sc/st": "SC/ST",
    "sc and st": "SC/ST",
    "obc": "OBC",
    "other backward class": "OBC",
    "other backward classes": "OBC",
    "backward class": "OBC",
    "bc": "OBC",
    "ews": "EWS",
    "economically weaker section": "EWS",
    "economically weaker sections": "EWS",
    "general": "General",
    "oc": "General",
    "open": "General",
    "open category": "General",
    "unreserved": "General",
    "ur": "General",
    "general/oc": "General",
    "minority": "Minority",
}


def normalize_state(state: Optional[str]) -> Optional[str]:
    """Normalize any Indian state name or abbreviation into its canonical title."""
    if not state:
        return None
    cleaned = state.strip().lower()
    cleaned = re.sub(r'^(state of|govt of|government of)\s+', '', cleaned)
    cleaned = re.sub(r'\s+(state|pradesh)$', lambda m: ' pradesh' if m.group(1) == 'pradesh' else '', cleaned).strip()
    # Check direct dictionary match
    if cleaned in STATE_ALIASES:
        return STATE_ALIASES[cleaned]
    # Check multi-word state names
    for key, val in sorted(STATE_ALIASES.items(), key=lambda x: len(x[0]), reverse=True):
        if re.search(r'\b' + re.escape(key) + r'\b', cleaned):
            return val
    return state.strip().title()


def normalize_category(category: Optional[str]) -> Optional[str]:
    """Normalize social category to canonical code (SC, ST, SC/ST, OBC, EWS, General, Minority)."""
    if not category:
        return None
    cleaned = category.strip().lower()
    if cleaned in CATEGORY_ALIASES:
        return CATEGORY_ALIASES[cleaned]
    for key, val in sorted(CATEGORY_ALIASES.items(), key=lambda x: len(x[0]), reverse=True):
        if key in cleaned:
            return val
    return category.strip()


def extract_scheme_state(scheme: Scheme) -> Optional[str]:
    """Extract canonical state restriction for a scheme."""
    if scheme.level == "Central":
        return None  # Central schemes are nationwide
    if scheme.target_state:
        norm = normalize_state(scheme.target_state)
        if norm:
            return norm
    text = f"{scheme.scheme_name} {scheme.details or ''} {scheme.eligibility or ''}".lower()
    for key, val in sorted(STATE_ALIASES.items(), key=lambda x: len(x[0]), reverse=True):
        if len(key) > 2 and re.search(r'\b' + re.escape(key) + r'\b', text):
            return val
    return None


def extract_scheme_category_restriction(scheme: Scheme) -> Optional[str]:
    """
    Extract whether a scheme is strictly restricted to a social category.
    Returns: 'SC', 'ST', 'SC/ST', 'OBC', 'Minority', 'General', or None (open).
    """
    if scheme.target_category:
        norm = normalize_category(scheme.target_category)
        if norm in ("SC", "ST", "SC/ST", "OBC", "Minority"):
            return norm

    text = f"{scheme.scheme_name} {scheme.details or ''} {scheme.eligibility or ''}".lower()

    # Check for strict SC/ST restriction
    if re.search(r'\b(sc/st|sc and st|scheduled castes? (and|or) scheduled tribes?)\b', text):
        return "SC/ST"
    # Check for SC-only restriction
    if re.search(r'\b(only sc|sc only|scheduled castes? only|belong to scheduled caste|for sc students?|for sc candidates?)\b', text):
        return "SC"
    # Check for ST-only restriction
    if re.search(r'\b(only st|st only|scheduled tribes? only|belong to scheduled tribe|for st students?|for st candidates?|tribal community only)\b', text):
        return "ST"
    # Check general SC mention if prominent
    if re.search(r'\bscheduled caste\b', text) and not re.search(r'\bscheduled tribe\b', text):
        return "SC"
    if re.search(r'\bscheduled tribe\b', text) and not re.search(r'\bscheduled caste\b', text):
        return "ST"
    if re.search(r'\b(obc only|other backward classes? only)\b', text):
        return "OBC"

    return None


def check_hard_eligibility(user: User, scheme: Scheme) -> Tuple[bool, List[Dict[str, str]]]:
    """
    Evaluate strict hard eligibility gates.
    Returns:
        (passes_hard_gates, failed_criteria)
        failed_criteria is a list of {"criterion": str, "reason": str}.
    """
    failed: List[Dict[str, str]] = []

    # ----------------------------------------------------
    # Gate 1: Caste / Category
    # ----------------------------------------------------
    scheme_cat = extract_scheme_category_restriction(scheme)
    if scheme_cat:
        user_cat = normalize_category(user.category)
        if not user_cat:
            # Profile category missing while scheme is strictly restricted
            failed.append({
                "criterion": "category",
                "reason": f"This scheme is restricted to {scheme_cat} applicants. Your profile category is not set.",
            })
        elif scheme_cat == "SC":
            if user_cat != "SC":
                failed.append({
                    "criterion": "category",
                    "reason": f"This scheme is restricted to SC applicants. (Your category: {user_cat})",
                })
        elif scheme_cat == "ST":
            if user_cat != "ST":
                failed.append({
                    "criterion": "category",
                    "reason": f"This scheme is restricted to ST applicants. (Your category: {user_cat})",
                })
        elif scheme_cat == "SC/ST":
            if user_cat not in ("SC", "ST", "SC/ST"):
                failed.append({
                    "criterion": "category",
                    "reason": f"This scheme is restricted to SC/ST applicants. (Your category: {user_cat})",
                })
        elif scheme_cat == "OBC":
            if user_cat != "OBC":
                failed.append({
                    "criterion": "category",
                    "reason": f"This scheme is restricted to OBC applicants. (Your category: {user_cat})",
                })
        elif scheme_cat == "Minority":
            if not user.minority_status and user_cat != "Minority":
                failed.append({
                    "criterion": "category",
                    "reason": "This scheme is restricted to minority community applicants.",
                })

    # ----------------------------------------------------
    # Gate 2: State Restriction
    # ----------------------------------------------------
    if scheme.level == "State":
        scheme_state = extract_scheme_state(scheme)
        if scheme_state:
            user_state = normalize_state(user.state)
            if not user_state:
                failed.append({
                    "criterion": "state",
                    "reason": f"This scheme is restricted to residents of {scheme_state}. Your state is not specified.",
                })
            elif user_state != scheme_state:
                failed.append({
                    "criterion": "state",
                    "reason": f"This scheme is restricted to residents of {scheme_state}. (Your state: {user_state})",
                })

    # ----------------------------------------------------
    # Gate 3: Gender Restrictions
    # ----------------------------------------------------
    user_gender = (user.gender or "").strip().lower()
    combined_text = f"{scheme.scheme_name} {scheme.details or ''} {scheme.eligibility or ''} {scheme.scheme_category or ''}".lower()

    is_female_scheme = (
        scheme.target_gender == "female" or
        re.search(r'\b(women only|girls? only|female only|mahila|pregnant|maternity|widow|widows)\b', combined_text) is not None
    )
    is_male_scheme = (
        scheme.target_gender == "male" or
        re.search(r'\b(men only|boys? only|male only)\b', combined_text) is not None
    )

    if is_female_scheme:
        if user_gender in ("male", "man", "boy"):
            failed.append({
                "criterion": "gender",
                "reason": "This scheme is restricted to female applicants.",
            })
    elif is_male_scheme:
        if user_gender in ("female", "woman", "girl"):
            failed.append({
                "criterion": "gender",
                "reason": "This scheme is restricted to male applicants.",
            })

    # ----------------------------------------------------
    # Gate 4: Age Bounds
    # ----------------------------------------------------
    if user.age is not None:
        if scheme.min_age and user.age < scheme.min_age:
            failed.append({
                "criterion": "age",
                "reason": f"Minimum age required is {scheme.min_age} years. (Your age: {user.age})",
            })
        if scheme.max_age and user.age > scheme.max_age:
            failed.append({
                "criterion": "age",
                "reason": f"Maximum age allowed is {scheme.max_age} years. (Your age: {user.age})",
            })

    # ----------------------------------------------------
    # Gate 5: Income Limits
    # ----------------------------------------------------
    user_income = user.annual_family_income or ((user.income or 0) * 12)
    if scheme.max_income and user_income and user_income > scheme.max_income:
        failed.append({
            "criterion": "income",
            "reason": f"Annual family income exceeds maximum limit of ₹{scheme.max_income:,.0f}. (Your income: ₹{user_income:,.0f})",
        })

    # ----------------------------------------------------
    # Gate 6: Mandatory Occupation / Status
    # ----------------------------------------------------
    if scheme.requires_farmer:
        user_occ = (user.occupation or "").lower()
        if not user.is_farmer and "farmer" not in user_occ and "kisan" not in user_occ and "agriculture" not in user_occ:
            failed.append({
                "criterion": "occupation",
                "reason": "This scheme requires the applicant to be a farmer.",
            })

    if scheme.requires_student:
        if not user.is_student and (user.employment_status or "").lower() != "student":
            failed.append({
                "criterion": "student_status",
                "reason": "This scheme requires the applicant to be an enrolled student.",
            })

    if scheme.requires_disability:
        if not user.is_disabled:
            failed.append({
                "criterion": "disability",
                "reason": "This scheme requires a valid disability certificate.",
            })

    if scheme.requires_widow:
        if not user.is_widow:
            failed.append({
                "criterion": "widow_status",
                "reason": "This scheme is restricted to widows.",
            })

    if scheme.requires_senior_citizen:
        if not user.is_senior_citizen and (user.age is not None and user.age < 60):
            failed.append({
                "criterion": "senior_citizen",
                "reason": "This scheme is restricted to senior citizens (60+ years).",
            })

    passes_hard = len(failed) == 0
    return passes_hard, failed


def calculate_eligibility_percentage(
    user: User,
    scheme: Scheme,
    passes_hard: bool,
    failed_criteria: List[Dict[str, str]],
) -> Tuple[bool, float, float, List[str]]:
    """
    Authoritative single pipeline for calculating eligibility percentage and status.
    INVARIANT:
      If hard eligibility condition fails:
          eligibility_percentage = 0
          eligible = False
          score = 0.0

    Returns:
        (is_eligible, eligibility_percentage, score, matched_criteria)
    """
    if not passes_hard or len(failed_criteria) > 0:
        return False, 0.0, 0.0, []

    matched: List[str] = []

    # State condition
    if scheme.level == "Central":
        matched.append("Central Government scheme — open nationwide")
    else:
        st = extract_scheme_state(scheme)
        if st and normalize_state(user.state) == st:
            matched.append(f"Resident of {st} requirement met")

    # Category condition
    cat = extract_scheme_category_restriction(scheme)
    if cat:
        matched.append(f"Social category ({normalize_category(user.category)}) matches scheme requirement")

    # Gender condition
    if scheme.target_gender in ("female", "male"):
        matched.append(f"Gender requirement met ({user.gender})")

    # Age condition
    if user.age is not None and (scheme.min_age or scheme.max_age):
        matched.append(f"Age {user.age} falls within eligible bounds")

    # Status conditions
    if scheme.requires_farmer and user.is_farmer:
        matched.append("Farmer status verified")
    if scheme.requires_student and user.is_student:
        matched.append("Student enrollment verified")
    if scheme.requires_disability and user.is_disabled:
        matched.append("Disability status verified")
    if scheme.requires_senior_citizen and (user.is_senior_citizen or (user.age and user.age >= 60)):
        matched.append("Senior citizen status verified")

    if not matched:
        matched.append("General eligibility criteria met")

    # Profile completeness bonus (up to 15%)
    profile_fields = [
        user.age, user.income, user.state, user.category,
        user.gender, user.occupation, user.education,
    ]
    completeness = sum(1 for f in profile_fields if f is not None) / len(profile_fields)

    base_score = 0.70 + (completeness * 0.15) + (min(len(matched), 3) * 0.05)
    score = min(max(round(base_score, 4), 0.50), 1.0)
    percentage = round(score * 100.0)

    return True, percentage, score, matched


def detect_language(text: str) -> str:
    """
    Detect language of the text:
    - Telugu (script range \u0C00 - \u0C7F) -> 'te'
    - Hindi (Devanagari script range \u0900 - \u097F) -> 'hi'
    - Otherwise -> 'en'
    """
    if not text:
        return "en"

    # Count characters in specific unicode blocks
    te_chars = sum(1 for c in text if '\u0C00' <= c <= '\u0C7F')
    hi_chars = sum(1 for c in text if '\u0900' <= c <= '\u097F')

    if te_chars >= 2 or (te_chars > 0 and te_chars >= hi_chars):
        return "te"
    if hi_chars >= 2 or (hi_chars > 0 and hi_chars > te_chars):
        return "hi"

    # Transliterated Telugu keywords
    te_keywords = ["pathakalu", "arhata", "arhatalu", "prabhutva", "telugu", "naaku", "evaro"]
    if any(k in text.lower() for k in te_keywords):
        return "te"

    # Transliterated Hindi keywords
    hi_keywords = ["yojana", "patrata", "sarkari", "hindi", "kripya", "kaise", "batao"]
    if any(k in text.lower() for k in hi_keywords):
        return "hi"

    return "en"
