import sqlite3

conn = sqlite3.connect('govscheme.db')
c = conn.cursor()

state_names = [
    'Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar', 'Chhattisgarh', 'Goa', 'Gujarat',
    'Haryana', 'Himachal Pradesh', 'Jharkhand', 'Karnataka', 'Kerala', 'Madhya Pradesh',
    'Maharashtra', 'Manipur', 'Meghalaya', 'Mizoram', 'Nagaland', 'Odisha', 'Punjab',
    'Rajasthan', 'Sikkim', 'Tamil Nadu', 'Telangana', 'Tripura', 'Uttar Pradesh', 'Uttarakhand',
    'West Bengal', 'Delhi', 'Puducherry', 'Jammu and Kashmir', 'Ladakh', 'Chandigarh'
]

state_counts = {}
matched = 0
rows = c.execute("SELECT id, scheme_name, details, eligibility FROM schemes WHERE level = 'State'").fetchall()
for row in rows:
    text = (row[1] + ' ' + (row[2] or '') + ' ' + (row[3] or '')).lower()
    found_state = None
    for st in state_names:
        if st.lower() in text:
            found_state = st
            break
    if found_state:
        matched += 1
        state_counts[found_state] = state_counts.get(found_state, 0) + 1

print(f"State schemes with identified state: {matched} / {len(rows)}")
for st, cnt in sorted(state_counts.items(), key=lambda x: x[1], reverse=True)[:15]:
    print(f"  {st}: {cnt}")
