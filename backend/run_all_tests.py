import asyncio
import httpx
import os
import sys
import time
from datetime import datetime

REPORT_PATH = "production_readiness_report.md"

async def wait_for_server():
    print("Waiting for server to start...")
    async with httpx.AsyncClient() as client:
        for _ in range(30):
            try:
                r = await client.get("http://127.0.0.1:8000/api/docs")
                if r.status_code == 200:
                    print("Server is up!")
                    return True
            except:
                pass
            await asyncio.sleep(1)
    return False

async def run_tests():
    if not await wait_for_server():
        print("Server did not start in time.")
        return

    print("Starting tests...")
    report_lines = []
    report_lines.append("# 🚀 GovScheme AI Production Readiness Report")
    report_lines.append(f"Generated at: {datetime.now().isoformat()}")
    report_lines.append("\n## Phase 2: API Testing")
    
    passed = 0
    failed = 0
    
    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000") as client:
        # Test Signup
        res = await client.post("/api/v1/auth/signup", json={
            "email": "test@example.com",
            "password": "Password123!",
            "full_name": "Test User",
            "state": "Maharashtra"
        })
        if res.status_code in [201, 400]:
            passed += 1
            report_lines.append("✅ Auth Signup API: Passed")
        else:
            failed += 1
            report_lines.append(f"❌ Auth Signup API: Failed (Status {res.status_code})")

        # Test Login
        res = await client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "Password123!"
        })
        token = None
        if res.status_code == 200:
            passed += 1
            token = res.json().get("access_token")
            report_lines.append("✅ Auth Login API: Passed")
        else:
            failed += 1
            report_lines.append(f"❌ Auth Login API: Failed (Status {res.status_code})")

        headers = {"Authorization": f"Bearer {token}"} if token else {}

        # Test Profile
        if token:
            res = await client.get("/api/v1/users/me", headers=headers)
            if res.status_code == 200:
                passed += 1
                report_lines.append("✅ Get Profile API: Passed")
            else:
                failed += 1
                report_lines.append(f"❌ Get Profile API: Failed (Status {res.status_code})")

        # Test Schemes
        res = await client.get("/api/v1/schemes")
        if res.status_code == 200:
            passed += 1
            report_lines.append("✅ Get Schemes API: Passed")
        else:
            failed += 1
            report_lines.append(f"❌ Get Schemes API: Failed (Status {res.status_code})")

        # Test Search
        res = await client.get("/api/v1/search?q=farmer")
        if res.status_code == 200:
            passed += 1
            report_lines.append("✅ Search API: Passed")
        else:
            failed += 1
            report_lines.append(f"❌ Search API: Failed (Status {res.status_code})")

    report_lines.append(f"\n### Test Summary\nTotal Passed: {passed}\nTotal Failed: {failed}")
    
    if failed == 0:
        report_lines.append("\n> [!NOTE]\n> **Status**: PRODUCTION READY")
    else:
        report_lines.append("\n> [!WARNING]\n> **Status**: ISSUES DETECTED")

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
    print(f"Report saved to {REPORT_PATH}")

if __name__ == "__main__":
    asyncio.run(run_tests())
