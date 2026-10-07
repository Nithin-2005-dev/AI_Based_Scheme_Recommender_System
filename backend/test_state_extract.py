import sqlite3
import re

conn = sqlite3.connect('govscheme.db')
c = conn.cursor()

INDIAN_STATES = {
    "andhra pradesh": "Andhra Pradesh",
    "ap": "Andhra Pradesh",
    "arunachal pradesh": "Arunachal Pradesh",
    "assam": "Assam",
    "bihar": "Bihar",
    "chhattisgarh": "Chhattisgarh",
    "chattisgarh": "Chhattisgarh",
    "goa": "Goa",
    "gujarat": "Gujarat",
    "haryana": "Haryana",
    "himachal pradesh": "Himachal Pradesh",
    "jharkhand": "Jharkhand",
    "karnataka": "Karnataka",
    "kerala": "Kerala",
    "madhya pradesh": "Madhya Pradesh",
    "mp": "Madhya Pradesh",
    "maharashtra": "Maharashtra",
    "manipur": "Manipur",
    "meghalaya": "Meghalaya",
    "mizoram": "Mizoram",
    "nagaland": "Nagaland",
    "odisha": "Odisha",
    "orissa": "Odisha",
    "punjab": "Punjab",
    "rajasthan": "Rajasthan",
    "sikkim": "Sikkim",
    "tamil nadu": "Tamil Nadu",
    "tamilnadu": "Tamil Nadu",
    "tn": "Tamil Nadu",
    "telangana": "Telangana",
    "ts": "Telangana",
    "tg": "Telangana",
    "tripura": "Tripura",
    "uttar pradesh": "Uttar Pradesh",
    "up": "Uttar Pradesh",
    "uttarakhand": "Uttarakhand",
    "uttaranchal": "Uttarakhand",
    "west bengal": "West Bengal",
    "wb": "West Bengal",
    "delhi": "Delhi",
    "new delhi": "Delhi",
    "puducherry": "Puducherry",
    "pondicherry": "Puducherry",
    "jammu and kashmir": "Jammu and Kashmir",
    "j&k": "Jammu and Kashmir",
    "ladakh": "Ladakh",
    "chandigarh": "Chandigarh"
}

def extract_state(name, details, eligibility):
    text = f"{name} {details or ''} {eligibility or ''}".lower()
    # Check multi-word states first to avoid substrings (e.g. "andhra pradesh" before "andhra")
    for key, val in sorted(INDIAN_STATES.items(), key=lambda x: len(x[0]), reverse=True):
        if re.search(r'\b' + re.escape(key) + r'\b', text):
            return val
    return None

rows = c.execute("SELECT id, scheme_name, details, eligibility, level, target_state FROM schemes").fetchall()
updated = 0
for r in rows:
    sid, sname, sdetails, selig, slevel, starget = r
    if slevel == "State" and not starget:
        st = extract_state(sname, sdetails, selig)
        if st:
            c.execute("UPDATE schemes SET target_state = ? WHERE id = ?", (st, sid))
            updated += 1

conn.commit()
print(f"Updated target_state for {updated} schemes in govscheme.db!")

# Verify counts
ts_count = c.execute("SELECT COUNT(*) FROM schemes WHERE target_state = 'Telangana'").fetchone()[0]
ap_count = c.execute("SELECT COUNT(*) FROM schemes WHERE target_state = 'Andhra Pradesh'").fetchone()[0]
total_with_state = c.execute("SELECT COUNT(*) FROM schemes WHERE target_state IS NOT NULL").fetchone()[0]
print(f"Total schemes with target_state: {total_with_state}")
print(f"Telangana schemes: {ts_count}")
print(f"Andhra Pradesh schemes: {ap_count}")
conn.close()
