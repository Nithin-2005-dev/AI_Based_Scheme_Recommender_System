"""
CSV Import Script: Import all 300 government schemes from updated_data.csv into the database.

Handles:
- Reading CSV with proper encoding
- Normalizing field names
- Deduplication by slug
- Validating required fields
- Creating tags
- NLP-based extraction of eligibility parameters (age, income, gender, etc.)
"""

import csv
import re
import os
import sys
import asyncio

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from app.core.database import engine, async_session_factory, Base
from app.models.scheme import Scheme, SchemeTag, scheme_tag_association
from app.models.user import User, UserDocument, RefreshToken
from app.models.notification import Notification, DeadlineReminder, SavedScheme, ApplicationTracker, ChatHistory, AnalyticsEvent


def extract_age_range(text: str) -> tuple:
    """Extract min/max age from eligibility text."""
    if not text:
        return None, None

    text_lower = text.lower()
    min_age, max_age = None, None

    # Pattern: "18 to 60 years" or "18-60 years"
    match = re.search(r'(\d+)\s*(?:to|-)\s*(\d+)\s*(?:years|yrs)', text_lower)
    if match:
        min_age = int(match.group(1))
        max_age = int(match.group(2))
        return min_age, max_age

    # Pattern: "at least 18 years" / "minimum age 18"
    match = re.search(r'(?:at least|minimum|above|not less than|more than)\s*(\d+)\s*(?:years|yrs|year)', text_lower)
    if match:
        min_age = int(match.group(1))

    # Pattern: "below 60 years" / "not exceed 60"
    match = re.search(r'(?:not exceed|maximum|below|less than|under|up to)\s*(\d+)\s*(?:years|yrs|year)', text_lower)
    if match:
        max_age = int(match.group(1))

    return min_age, max_age


def extract_income_limit(text: str) -> tuple:
    """Extract income limits from eligibility text."""
    if not text:
        return None, None

    text_lower = text.lower()

    patterns = [
        r'(?:income|annual income).*?(?:not exceed|less than|below|up to|maximum).*?(?:₹|rs\.?|inr)\s*([\d,]+)',
        r'(?:₹|rs\.?|inr)\s*([\d,]+).*?(?:income|annual)',
        r'(?:income|annual income).*?([\d,]+)',
    ]

    for pattern in patterns:
        match = re.search(pattern, text_lower)
        if match:
            try:
                limit = float(match.group(1).replace(",", ""))
                return None, limit
            except ValueError:
                continue

    return None, None


def extract_target_gender(text: str, category: str) -> str:
    """Determine target gender from eligibility text."""
    combined = (text or "").lower() + " " + (category or "").lower()

    women_keywords = ["women", "woman", "female", "girl", "mahila", "stree", "lady"]
    if any(kw in combined for kw in women_keywords):
        return "female"

    men_keywords = ["male only", "men only", "boys only"]
    if any(kw in combined for kw in men_keywords):
        return "male"

    return "all"


def extract_flags(text: str, category: str) -> dict:
    """Extract boolean flags from text."""
    combined = (text or "").lower() + " " + (category or "").lower()

    return {
        "requires_disability": any(kw in combined for kw in ["disability", "disabled", "handicap", "divyang", "pwd"]),
        "requires_farmer": any(kw in combined for kw in ["farmer", "kisan", "agriculture", "cultivator"]),
        "requires_student": any(kw in combined for kw in ["student", "scholarship", "studying"]),
        "requires_widow": any(kw in combined for kw in ["widow", "vidhwa"]),
        "requires_senior_citizen": any(kw in combined for kw in ["senior citizen", "old age", "elderly"]),
        "requires_pregnant": any(kw in combined for kw in ["pregnant", "maternity", "maternal"]),
        "requires_business_owner": any(kw in combined for kw in ["entrepreneur", "business owner", "startup"]),
    }


def extract_target_category(text: str) -> str:
    """Extract target social category."""
    if not text:
        return None

    text_lower = text.lower()

    if any(kw in text_lower for kw in ["scheduled caste", "sc ", "sc/"]):
        return "SC"
    if any(kw in text_lower for kw in ["scheduled tribe", "st ", "st/"]):
        return "ST"
    if any(kw in text_lower for kw in ["sc/st"]):
        return "SC/ST"
    if any(kw in text_lower for kw in ["other backward", "obc"]):
        return "OBC"
    if any(kw in text_lower for kw in ["minority"]):
        return "Minority"
    if any(kw in text_lower for kw in ["general"]):
        return "General"

    return None


async def import_csv(csv_path: str):
    """Import CSV data into the database."""
    print(f"📂 Reading CSV from: {csv_path}")

    # Read CSV
    rows = []
    encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
    for encoding in encodings:
        try:
            with open(csv_path, "r", encoding=encoding) as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            print(f"✅ Read {len(rows)} rows with {encoding} encoding")
            break
        except (UnicodeDecodeError, Exception) as e:
            print(f"❌ Failed with {encoding}: {e}")
            continue

    if not rows:
        print("❌ No rows read from CSV")
        return

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database tables created")

    # Import
    async with async_session_factory() as session:
        # CLEAR DB
        await session.execute(select(Scheme)) # Just to load it
        from sqlalchemy import text
        await session.execute(text("DELETE FROM scheme_tag_association"))
        await session.execute(text("DELETE FROM schemes"))
        await session.commit()
        print("✅ Cleared old schemes")
        seen_slugs = set()
        imported = 0
        skipped = 0
        all_tags = {}
        
        central_count = 0
        state_count = 0

        for row in rows:
            slug = (row.get("slug") or "").strip()
            scheme_name = (row.get("scheme_name") or "").strip()

            if not slug or not scheme_name:
                skipped += 1
                continue

            if slug in seen_slugs:
                skipped += 1
                continue
                
            level_clean = (row.get("level") or "Central").strip()
            if level_clean not in ("Central", "State"):
                level_clean = "Central"
                
            if level_clean == "Central":
                if central_count >= 150:
                    skipped += 1
                    continue
                central_count += 1
            else:
                if state_count >= 150:
                    skipped += 1
                    continue
                state_count += 1

            # Check if already exists
            existing = await session.execute(
                select(Scheme).where(Scheme.slug == slug)
            )
            if existing.scalar_one_or_none():
                seen_slugs.add(slug)
                skipped += 1
                continue

            seen_slugs.add(slug)

            details = (row.get("details") or "").strip()
            benefits = (row.get("benefits") or "").strip()
            eligibility = (row.get("eligibility") or "").strip()
            application = (row.get("application") or "").strip()
            documents = (row.get("documents") or "").strip()
            level = (row.get("level") or "Central").strip()
            category = (row.get("schemeCategory") or "").strip()
            tags_str = (row.get("tags") or "").strip()

            # Extract NLP features
            min_age, max_age = extract_age_range(eligibility)
            min_income, max_income = extract_income_limit(eligibility)
            target_gender = extract_target_gender(eligibility, category)
            target_category = extract_target_category(eligibility)
            flags = extract_flags(eligibility, category)

            # Create scheme
            scheme = Scheme(
                scheme_name=scheme_name,
                slug=slug,
                details=details,
                benefits=benefits,
                eligibility=eligibility,
                application_process=application,
                documents_required=documents,
                level=level if level in ("Central", "State") else "Central",
                scheme_category=category,
                min_age=min_age,
                max_age=max_age,
                min_income=min_income,
                max_income=max_income,
                target_gender=target_gender,
                target_category=target_category,
                **flags,
            )
            session.add(scheme)
            imported += 1

            # Process tags
            if tags_str:
                tag_names = [t.strip() for t in tags_str.split(",") if t.strip()]
                for tag_name in tag_names:
                    if tag_name not in all_tags:
                        # Check if tag exists
                        tag_result = await session.execute(
                            select(SchemeTag).where(SchemeTag.name == tag_name)
                        )
                        tag = tag_result.scalar_one_or_none()
                        if not tag:
                            tag = SchemeTag(name=tag_name)
                            session.add(tag)
                            await session.flush()
                        all_tags[tag_name] = tag

            # Commit in batches
            if imported % 200 == 0:
                await session.commit()
                print(f"   📊 Imported {imported} schemes...")

        await session.commit()
        print(f"\n✅ Import complete!")
        print(f"   📊 Imported: {imported}")
        print(f"   ⏭️  Skipped (duplicates/empty): {skipped}")
        print(f"   🏷️  Tags created: {len(all_tags)}")


async def seed_admin():
    """Create default admin user."""
    from app.core.security import hash_password

    async with async_session_factory() as session:
        result = await session.execute(
            select(User).where(User.email == "admin@govscheme.ai")
        )
        if result.scalar_one_or_none():
            print("ℹ️  Admin user already exists")
            return

        admin = User(
            email="admin@govscheme.ai",
            hashed_password=hash_password("Admin@123456"),
            full_name="System Administrator",
            role="admin",
            is_email_verified=True,
            profile_completed=True,
        )
        session.add(admin)
        await session.commit()
        print("✅ Admin user created: admin@govscheme.ai / Admin@123456")


async def main():
    """Run import and seeding."""
    csv_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "..", "updated_data.csv"
    )

    # Try alternative paths
    if not os.path.exists(csv_path):
        csv_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "updated_data.csv"
        )
    if not os.path.exists(csv_path):
        csv_path = "updated_data.csv"
    if not os.path.exists(csv_path):
        # Look in parent directories
        for parent in [".", "..", "../.."]:
            candidate = os.path.join(parent, "updated_data.csv")
            if os.path.exists(candidate):
                csv_path = candidate
                break

    if not os.path.exists(csv_path):
        print(f"❌ CSV file not found. Please place updated_data.csv in the project root.")
        return

    await import_csv(csv_path)
    await seed_admin()


if __name__ == "__main__":
    asyncio.run(main())
