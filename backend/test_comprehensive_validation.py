"""
Comprehensive Validation Tests for GovScheme AI Requirements:
- Hard Eligibility Gates (Caste, State, Gender, Age, Income, Occupation)
- Scoring Invariant: Ineligible -> 0%, Eligible -> >0%, Never 100% for Ineligible
- Top 5 Personalized Recommendations
- Multilingual Chatbot (English, Telugu, Hindi detection & localized responses)
"""

import asyncio
import pytest
from app.models.user import User
from app.models.scheme import Scheme
from app.core.database import async_session_factory
from app.services.eligibility_rules import (
    normalize_state,
    normalize_category,
    check_hard_eligibility,
    calculate_eligibility_percentage,
    detect_language,
)
from app.services.eligibility_checker import EligibilityChecker
from app.services.recommendation_engine import RecommendationEngine
from app.services.rag_chatbot import RAGChatbot


def test_1_sc_only_scheme_with_oc_user():
    """Test 1: SC-only scheme + OC user -> eligible = false, eligibility_percentage = 0"""
    user_oc = User(id=1, category="OC", state="Telangana", age=25)
    scheme_sc = Scheme(id=101, scheme_name="Post-Matric Scholarship for SC", level="Central", target_category="SC")
    
    passes_hard, failed = check_hard_eligibility(user_oc, scheme_sc)
    is_eligible, pct, score, matched = calculate_eligibility_percentage(user_oc, scheme_sc, passes_hard, failed)
    
    assert passes_hard is False
    assert is_eligible is False
    assert pct == 0
    assert score == 0.0
    assert len(failed) > 0
    assert failed[0]["criterion"] == "category"
    print("PASS: Test 1 — SC-only scheme + OC user -> eligible=False, pct=0")


def test_2_sc_only_scheme_with_sc_user():
    """Test 2: SC-only scheme + SC user -> eligible = true, eligibility_percentage > 0"""
    user_sc = User(id=2, category="SC", state="Telangana", age=25)
    scheme_sc = Scheme(id=101, scheme_name="Post-Matric Scholarship for SC", level="Central", target_category="SC")
    
    passes_hard, failed = check_hard_eligibility(user_sc, scheme_sc)
    is_eligible, pct, score, matched = calculate_eligibility_percentage(user_sc, scheme_sc, passes_hard, failed)
    
    assert passes_hard is True
    assert is_eligible is True
    assert pct > 0
    assert score > 0.0
    assert len(failed) == 0
    print(f"PASS: Test 2 — SC-only scheme + SC user -> eligible=True, pct={pct}%")


def test_3_telangana_only_scheme_with_ap_user():
    """Test 3: Telangana-only scheme + AP user -> eligible = false, eligibility_percentage = 0"""
    user_ap = User(id=3, category="General", state="Andhra Pradesh", age=30)
    scheme_ts = Scheme(id=102, scheme_name="Rythu Bandhu", level="State", target_state="Telangana")
    
    passes_hard, failed = check_hard_eligibility(user_ap, scheme_ts)
    is_eligible, pct, score, matched = calculate_eligibility_percentage(user_ap, scheme_ts, passes_hard, failed)
    
    assert passes_hard is False
    assert is_eligible is False
    assert pct == 0
    assert any(f["criterion"] == "state" for f in failed)
    print("PASS: Test 3 — Telangana-only scheme + AP user -> eligible=False, pct=0")


def test_4_ap_only_scheme_with_ap_user():
    """Test 4: AP-only scheme + AP user -> state constraint passes"""
    user_ap = User(id=4, category="General", state="AP", age=30)  # test normalization of 'AP'
    scheme_ap = Scheme(id=103, scheme_name="YSR Cheyutha", level="State", target_state="Andhra Pradesh")
    
    passes_hard, failed = check_hard_eligibility(user_ap, scheme_ap)
    is_eligible, pct, score, matched = calculate_eligibility_percentage(user_ap, scheme_ap, passes_hard, failed)
    
    assert passes_hard is True
    assert is_eligible is True
    assert pct > 0
    print(f"PASS: Test 4 — AP-only scheme + AP user -> state constraint passes, pct={pct}%")


def test_5_central_scheme_with_no_state_restriction():
    """Test 5: Central scheme with no state restriction -> AP/Telangana user does not receive 0%"""
    user_ts = User(id=5, category="OBC", state="Telangana", age=35)
    scheme_central = Scheme(id=104, scheme_name="PM Kisan Samman Nidhi", level="Central")
    
    passes_hard, failed = check_hard_eligibility(user_ts, scheme_central)
    is_eligible, pct, score, matched = calculate_eligibility_percentage(user_ts, scheme_central, passes_hard, failed)
    
    assert passes_hard is True
    assert is_eligible is True
    assert pct > 0
    print(f"PASS: Test 5 — Central scheme + TS user -> eligible=True, pct={pct}%")


def test_6_any_hard_constraint_failure():
    """Test 6: Any hard constraint failure -> eligibility_percentage == 0, eligible == false"""
    # Case A: Gender failure (Female scheme with male user)
    user_male = User(id=6, gender="male", state="Karnataka")
    scheme_women = Scheme(id=105, scheme_name="Sukanya Samriddhi", target_gender="female", level="Central")
    p_a, f_a = check_hard_eligibility(user_male, scheme_women)
    ie_a, pct_a, _, _ = calculate_eligibility_percentage(user_male, scheme_women, p_a, f_a)
    assert p_a is False and ie_a is False and pct_a == 0

    # Case B: Age failure (Min age 60, user age 25)
    user_young = User(id=7, age=25, state="Karnataka")
    scheme_senior = Scheme(id=106, scheme_name="Old Age Pension", min_age=60, level="Central")
    p_b, f_b = check_hard_eligibility(user_young, scheme_senior)
    ie_b, pct_b, _, _ = calculate_eligibility_percentage(user_young, scheme_senior, p_b, f_b)
    assert p_b is False and ie_b is False and pct_b == 0

    # Case C: Income limit failure
    user_rich = User(id=8, annual_family_income=600000.0, state="Karnataka")
    scheme_bpl = Scheme(id=107, scheme_name="BPL Ration", max_income=200000.0, level="Central")
    p_c, f_c = check_hard_eligibility(user_rich, scheme_bpl)
    ie_c, pct_c, _, _ = calculate_eligibility_percentage(user_rich, scheme_bpl, p_c, f_c)
    assert p_c is False and ie_c is False and pct_c == 0

    print("PASS: Test 6 — All hard constraint failures strictly yield 0% and eligible=False")


def test_7_language_detection():
    """Test language detection for English, Telugu, and Hindi"""
    # English
    assert detect_language("What schemes am I eligible for?") == "en"
    assert detect_language("How to apply for PM Kisan?") == "en"

    # Telugu
    assert detect_language("నాకు ఏ ప్రభుత్వ పథకాలు అందుబాటులో ఉన్నాయి?") == "te"
    assert detect_language("విద్యార్థులకు ఏ పథకాలు ఉన్నాయి?") == "te"

    # Hindi
    assert detect_language("मेरे लिए कौन सी सरकारी योजनाएं उपलब्ध हैं?") == "hi"
    assert detect_language("छात्रों के लिए छात्रवृत्ति योजनाएं") == "hi"

    print("PASS: Language detection accurately identifies en, te, and hi")


async def test_async_top5_recommendations():
    """Test 7: Top 5 recommendations personalized and max 5"""
    async with async_session_factory() as db:
        user_farmer = User(
            id=10, email="farmer@test.com", hashed_password="x",
            full_name="Ramesh", age=40, state="Maharashtra",
            category="OBC", is_farmer=True, occupation="Farmer",
            annual_family_income=300000.0
        )
        engine = RecommendationEngine(db)
        recs = await engine.get_recommendations(user_farmer, top_k=5)
        
        assert len(recs) <= 5
        print(f"PASS: Test 7 — Returned exactly {len(recs)} Top recommendations for user")
        for idx, r in enumerate(recs, 1):
            assert r["eligible"] is True
            assert r["eligibility_percentage"] > 0
            assert len(r["failed_conditions"]) == 0
            print(f"   #{idx}: {r['scheme'].scheme_name[:50]}... (Score: {r['score']}, Pct: {r['eligibility_percentage']}%)")


async def test_async_chatbot_multilingual():
    """Test 8, 9, 10: Chatbot responses in en, te, hi"""
    async with async_session_factory() as db:
        user = User(
            id=11, email="citizen@test.com", hashed_password="x",
            full_name="Citizen", age=28, state="Telangana",
            category="General", is_farmer=False,
        )
        chatbot = RAGChatbot(db)

        # Test 8: English query
        res_en = await chatbot.ask(user.id, "What schemes am I eligible for?", user=user)
        assert res_en["language"] == "en"
        assert "eligible" in res_en["answer"].lower()
        print("PASS: Test 8 — English question received English response")

        # Test 9: Telugu query
        res_te = await chatbot.ask(user.id, "నాకు ఏ ప్రభుత్వ పథకాలు అందుబాటులో ఉన్నాయి?", user=user)
        assert res_te["language"] == "te"
        assert any('\u0C00' <= c <= '\u0C7F' for c in res_te["answer"])
        print("PASS: Test 9 — Telugu question received Telugu response")

        # Test 10: Hindi query
        res_hi = await chatbot.ask(user.id, "मेरे लिए कौन सी सरकारी योजनाएं उपलब्ध हैं?", user=user)
        assert res_hi["language"] == "hi"
        assert any('\u0900' <= c <= '\u097F' for c in res_hi["answer"])
        print("PASS: Test 10 — Hindi question received Hindi response")


def run_all():
    print("=" * 60)
    print("RUNNING COMPREHENSIVE BACKEND VALIDATION SUITE")
    print("=" * 60)
    test_1_sc_only_scheme_with_oc_user()
    test_2_sc_only_scheme_with_sc_user()
    test_3_telangana_only_scheme_with_ap_user()
    test_4_ap_only_scheme_with_ap_user()
    test_5_central_scheme_with_no_state_restriction()
    test_6_any_hard_constraint_failure()
    test_7_language_detection()
    
    asyncio.run(test_async_top5_recommendations())
    asyncio.run(test_async_chatbot_multilingual())
    print("=" * 60)
    print("ALL 10 BACKEND UNIT & INTEGRATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    run_all()
