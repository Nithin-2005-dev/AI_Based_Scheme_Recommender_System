import os
import subprocess

# 1. Update text files
directory = r"C:\Users\NITHIN\Downloads\tetrifox-assignment\scheme_app\AI_Based_Scheme_Recommender_System"
search_replace = [
    ("150", "300"),
    ("75", "150"),
]

for root, _, files in os.walk(directory):
    if "venv" in root or ".git" in root or "node_modules" in root or "__pycache__" in root or ".next" in root:
        continue
    for file in files:
        if file.endswith((".ts", ".tsx", ".py", ".md", ".json")):
            filepath = os.path.join(root, file)
            # Skip this script
            if file == "fix_300.py":
                continue
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

print("String replacement complete.")
