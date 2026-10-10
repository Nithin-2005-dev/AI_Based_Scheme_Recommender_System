import asyncio
import os
import sys
import glob

# 1. Update text files
directory = r"C:\Users\NITHIN\Downloads\tetrifox-assignment\scheme_app\AI_Based_Scheme_Recommender_System"
search_replace = [
    ("300", "300"),
    ("300", "300"),
    ("150", "150"),
    ("150", "150"),
    ("150", "150")
]

for root, _, files in os.walk(directory):
    if "venv" in root or ".git" in root or "node_modules" in root or "__pycache__" in root or ".next" in root:
        continue
    for file in files:
        if file.endswith((".ts", ".tsx", ".py", ".md", ".json")):
            filepath = os.path.join(root, file)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                
                new_content = content
                for old_val, new_val in search_replace:
                    new_content = new_content.replace(old_val, new_val)
                    
                if new_content != content:
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(new_content)
                    print(f"Updated {filepath}")
            except Exception as e:
                pass

# 2. Reset database with exactly 300 schemes (150 Central, 150 State)
sys.path.insert(0, os.path.join(directory, "backend"))
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text
from app.core.config import get_settings

settings = get_settings()
engine = create_async_engine(settings.DATABASE_URL)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def reimport_schemes():
    import csv
    import uuid
    import json
    
    csv_path = os.path.join(directory, "updated_data.csv")
    
    central_rows = []
    state_rows = []
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('level', '') == 'Central' and len(central_rows) < 150:
                central_rows.append(row)
            elif row.get('level', '') == 'State' and len(state_rows) < 150:
                state_rows.append(row)
                
            if len(central_rows) == 150 and len(state_rows) == 150:
                break
                
    combined_rows = central_rows + state_rows
    
    async with AsyncSessionLocal() as session:
        # Clear existing
        await session.execute(text("DELETE FROM schemes"))
        
        # Insert exactly 300
        for row in combined_rows:
            stmt = text("""
                INSERT INTO schemes (
                    id, scheme_name, description, benefits,
                    eligibility_criteria, application_process, documents_required,
                    state, category, scheme_type,
                    tags, level, department_name, ministry_name
                ) VALUES (
                    :id, :scheme_name, :description, :benefits,
                    :eligibility_criteria, :application_process, :documents_required,
                    :state, :category, :scheme_type,
                    :tags, :level, :department_name, :ministry_name
                )
            """)
            await session.execute(stmt, {
                "id": str(uuid.uuid4()),
                "scheme_name": str(row.get('scheme_name', '')),
                "description": str(row.get('description', '')),
                "benefits": str(row.get('benefits', '')),
                "eligibility_criteria": str(row.get('eligibility_criteria', '')),
                "application_process": str(row.get('application_process', '')),
                "documents_required": str(row.get('documents_required', '')),
                "state": str(row.get('state', '')),
                "category": str(row.get('category', '')),
                "scheme_type": "",
                "tags": str(row.get('tags', '')),
                "level": str(row.get('level', '')),
                "department_name": "",
                "ministry_name": ""
            })
            
        await session.commit()
        
        # Verify
        total = (await session.execute(text("SELECT COUNT(*) FROM schemes"))).scalar()
        central = (await session.execute(text("SELECT COUNT(*) FROM schemes WHERE level = 'Central'"))).scalar()
        state = (await session.execute(text("SELECT COUNT(*) FROM schemes WHERE level = 'State'"))).scalar()
        
        print(f"Total schemes in DB: {total}")
        print(f"Central schemes: {central}")
        print(f"State schemes: {state}")

if __name__ == "__main__":
    asyncio.run(reimport_schemes())
