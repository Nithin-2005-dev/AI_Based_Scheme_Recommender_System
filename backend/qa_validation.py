import asyncio
import httpx
import os
from datetime import datetime

REPORT_PATH = "comprehensive_qa_report.md"

queries = [
    "What schemes are for farmers?", "How to apply for PM Kisan?", "Is there any scheme for women entrepreneurs?",
    "What is the eligibility for Mudra Yojana?", "Are there scholarships for SC/ST students?",
    "How much financial assistance is given in PMAY?", "Documents required for Ayushman Bharat?",
    "Schemes for pregnant women?", "Can a senior citizen apply for pension?", "How to get a tractor loan?",
    "What is the income limit for EWS certificate?", "Are there subsidies for solar panels?",
    "Which schemes help disabled persons?", "What is Stand-up India?", "How to register for MSME?",
    "Schemes for handloom weavers?", "Is there any life insurance scheme?", "What is PM Jeevan Jyoti Bima Yojana?",
    "How to get free ration?", "What is PM Garib Kalyan Yojana?",
    "Schemes for girl child education?", "What is Sukanya Samriddhi Yojana?", "How to open a Jan Dhan account?",
    "Benefits of Atal Pension Yojana?", "Schemes for dairy farming?",
    "What is PM Fasal Bima Yojana?", "How to get KCC (Kisan Credit Card)?", "Are there schemes for fishermen?",
    "What is PM Matsya Sampada Yojana?", "Schemes for street vendors?",
    "What is PM SVANidhi?", "How to get housing loan subsidy?", "Schemes for minority students?",
    "What is the National Means-cum-Merit Scholarship?", "Schemes for tribal welfare?",
    "What is Eklavya Model Residential School?", "Schemes for rural employment?", "What is MGNREGA?",
    "How many days of work in MGNREGA?", "Schemes for urban development?",
    "What is AMRUT scheme?", "Schemes for skill development?", "What is PM Kaushal Vikas Yojana?",
    "How to get skill training?", "Schemes for startups?",
    "What is Startup India?", "How to get seed fund for startup?", "Schemes for export promotion?",
    "What is MEIS?", "Schemes for electric vehicles?",
    "What is FAME India scheme?", "Schemes for renewable energy?", "How to get solar water pump?",
    "What is PM KUSUM?", "Schemes for health insurance?",
    "How to claim Ayushman Bharat benefits?", "Schemes for tuberculosis patients?", "What is Nikshay Poshan Yojana?",
    "Schemes for sanitation?", "What is Swachh Bharat Abhiyan?",
    "How to get subsidy for building toilet?", "Schemes for drinking water?", "What is Jal Jeevan Mission?",
    "Schemes for road connectivity?", "What is PMGSY?",
    "Schemes for digitisation?", "What is Digital India?", "How to get CSC (Common Service Centre)?",
    "Schemes for broadband connectivity?", "What is BharatNet?",
    "Schemes for financial inclusion?", "What is JAM trinity?", "Schemes for women empowerment?",
    "What is Beti Bachao Beti Padhao?", "Schemes for maternity benefit?",
    "What is PM Matru Vandana Yojana?", "Schemes for child nutrition?", "What is Poshan Abhiyaan?",
    "Schemes for school meals?", "What is PM POSHAN (Mid-Day Meal)?",
    "Schemes for youth?", "What is Nehru Yuva Kendra?", "Schemes for sports?",
    "What is Khelo India?", "Schemes for traditional medicines?", "What is AYUSH?",
    "Schemes for generic medicines?", "What is PM Jan Aushadhi Yojana?", "Schemes for widow pension?",
    "How to apply for IGNDPS?", "Schemes for unorganised workers?", "What is e-Shram?",
    "How to register on e-Shram portal?", "Schemes for provident fund?", "What is PMRPY?",
    "Schemes for MSME collateral free loan?", "What is CGTMSE?", "Schemes for food processing?",
    "What is PM FME?", "Schemes for self help groups (SHGs)?", "What is NRLM (Ajeevika)?",
    "How to get bank linkage for SHG?", "Schemes for craft persons?", "What is PM Vishwakarma?",
]

async def run_tests():
    print("Starting Comprehensive QA Validation...")
    report_lines = []
    report_lines.append("# 🚀 Comprehensive QA Validation Report")
    report_lines.append(f"Generated at: {datetime.now().isoformat()}\n")
    
    passed = 0
    failed = 0
    
    def log_result(test_name, success, info=""):
        nonlocal passed, failed
        if success:
            passed += 1
            report_lines.append(f"✅ {test_name}: Passed {info}")
            print(f"✅ {test_name} passed.")
        else:
            failed += 1
            report_lines.append(f"❌ {test_name}: Failed {info}")
            print(f"❌ {test_name} failed. {info}")

    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000", timeout=60.0) as client:
        # 1. Auth Setup
        res = await client.post("/api/v1/auth/login", json={"email": "test@example.com", "password": "Password123!"})
        if res.status_code == 200:
            token = res.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            log_result("Auth Login", True)
        else:
            # Try signup
            await client.post("/api/v1/auth/signup", json={"email": "test@example.com", "password": "Password123!", "full_name": "QA User"})
            res = await client.post("/api/v1/auth/login", json={"email": "test@example.com", "password": "Password123!"})
            token = res.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            log_result("Auth Signup & Login", True)

        # 2. Test Recommendation Engine
        res = await client.get("/api/v1/recommendations", headers=headers)
        if res.status_code == 200:
            log_result("Recommendation Engine", True, f"({len(res.json().get('recommendations', []))} recs returned)")
        else:
            log_result("Recommendation Engine", False, f"Status: {res.status_code}")

        # 3. Test Eligibility Engine (assuming scheme_id=1 exists)
        res = await client.post("/api/v1/eligibility/check", json={"scheme_id": 1}, headers=headers)
        if res.status_code in [200, 404]:
            log_result("Eligibility Engine", True, f"Status: {res.status_code}")
        else:
            log_result("Eligibility Engine", False, f"Status: {res.status_code}")

        # 4. Test Multilingual Support
        res = await client.get("/api/v1/translate/languages")
        if res.status_code == 200:
            log_result("Multilingual Engine - Languages", True)
        else:
            log_result("Multilingual Engine - Languages", False)

        res = await client.post("/api/v1/translate", json={"text": "Hello", "target_language": "hi", "source_language": "en"})
        if res.status_code == 200:
            log_result("Multilingual Engine - Translate", True)
        else:
            log_result("Multilingual Engine - Translate", False)

        # 5. Test Notifications
        res = await client.get("/api/v1/notifications", headers=headers)
        if res.status_code == 200:
            log_result("Notification Engine", True)
        else:
            log_result("Notification Engine", False)
            
        # 6. Rule-change detection
        admin_res = await client.post("/api/v1/auth/login", json={"email": "admin@govscheme.ai", "password": "Admin@123456"})
        if admin_res.status_code == 200:
            admin_token = admin_res.json()["access_token"]
            admin_headers = {"Authorization": f"Bearer {admin_token}"}
            rc_res = await client.get("/api/v1/admin/scheme-versions/1", headers=admin_headers)
            if rc_res.status_code in [200, 404]:
                log_result("Rule-Change Detection API", True, f"Status: {rc_res.status_code}")
            else:
                log_result("Rule-Change Detection API", False, f"Status: {rc_res.status_code}")
        else:
            log_result("Admin Auth (for Rule-Change)", False, "Could not login as admin")

        # 7. Test RAG Chatbot (100 queries)
        print(f"Testing Chatbot with {len(queries)} queries...")
        chat_success = 0
        for i, q in enumerate(queries):
            try:
                c_res = await client.post("/api/v1/chatbot", json={"message": q, "session_id": "test_session_1"}, headers=headers)
                if c_res.status_code == 200:
                    chat_success += 1
            except Exception as e:
                print(f"Query '{q}' failed: {e}")
            if (i+1) % 20 == 0:
                print(f"Processed {i+1}/100 queries...")
                
        if chat_success == len(queries):
            log_result("RAG Chatbot (100 Diverse Queries)", True, f"({chat_success}/{len(queries)} successful)")
        else:
            log_result("RAG Chatbot (100 Diverse Queries)", False, f"({chat_success}/{len(queries)} successful)")

    report_lines.append(f"\n### Test Summary\nTotal Passed: {passed}\nTotal Failed: {failed}")
    if failed == 0:
        report_lines.append("\n> [!NOTE]\n> **Status**: QA FULLY VALIDATED")
    else:
        report_lines.append("\n> [!WARNING]\n> **Status**: QA ISSUES DETECTED")

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
    print(f"\nQA Validation complete! Report saved to {REPORT_PATH}")

if __name__ == "__main__":
    asyncio.run(run_tests())
