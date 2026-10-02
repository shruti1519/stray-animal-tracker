import sqlite3

conn = sqlite3.connect("stray.db")
c = conn.cursor()

# Report 1
c.execute("""
INSERT INTO reports
(citizen_id, species, location, description, ngo_id, date, status)
VALUES (
    (SELECT id FROM citizens WHERE email='aditi@gmail.com'),
    'Dog',
    'Kothrud, Pune',
    'Injured stray dog near the road',
    1,
    '2026-10-02',
    'Rescued'
)
""")

# Report 2
c.execute("""
INSERT INTO reports
(citizen_id, species, location, description, ngo_id, date, status)
VALUES (
    (SELECT id FROM citizens WHERE email='rahul@gmail.com'),
    'Cat',
    'Shivajinagar, Pune',
    'Stray cat needs medical attention',
    2,
    '2026-10-02',
    'In Progress'
)
""")

# Report 3
c.execute("""
INSERT INTO reports
(citizen_id, species, location, description, ngo_id, date, status)
VALUES (
    (SELECT id FROM citizens WHERE email='aditi@gmail.com'),
    'Dog',
    'Katraj, Pune',
    'Stray dog found near residential area',
    2,
    '2026-10-02',
    'Rescued'
)
""")

conn.commit()
conn.close()

print("Reports added successfully!")