import sqlite3

DB = "stray.db"

conn = sqlite3.connect(DB)
cursor = conn.cursor()

# -------------------------
# CITIZENS
# -------------------------

citizens = [
    ("Aditi Patil", "aditi@gmail.com", "9876543210", "Kothrud, Pune", "Aditi@123"),
    ("Rahul Sharma", "rahul@gmail.com", "9876543211", "Baner, Pune", "Rahul@123"),
    ("Sneha Kulkarni", "sneha@gmail.com", "9876543212", "Wakad, Pune", "Sneha@123"),
    ("Rohan Joshi", "rohan@gmail.com", "9876543213", "Hadapsar, Pune", "Rohan@123"),
    ("Priya Deshmukh", "priya@gmail.com", "9876543214", "Katraj, Pune", "Priya@123"),
    ("Neha Pawar", "neha@gmail.com", "9876543215", "Aundh, Pune", "Neha@123"),
    ("Akash More", "akash@gmail.com", "9876543216", "Viman Nagar, Pune", "Akash@123"),
    ("Pooja Jadhav", "pooja@gmail.com", "9876543217", "Sinhagad Road, Pune", "Pooja@123"),
    ("Omkar Shinde", "omkar@gmail.com", "9876543218", "Pimpri, Pune", "Omkar@123"),
    ("Isha Mehta", "isha@gmail.com", "9876543219", "Kharadi, Pune", "Isha@123")
]

for c in citizens:
    cursor.execute("""
        INSERT OR IGNORE INTO citizens
        (name, email, phone, area, password)
        VALUES (?, ?, ?, ?, ?)
    """, c)


# -------------------------
# NGOs
# -------------------------

ngos = [
    ("Paws Rescue NGO", "Neha Shah", "neha@pawsrescue.org",
     "9123456780", "Pune", "NGO@123"),

    ("Happy Tails Shelter", "Rahul Mehta", "rahul@happytails.org",
     "9123456781", "Mumbai", "Tails@123"),

    ("Animal Care Foundation", "Snehal Patil", "snehal@animalcare.org",
     "9123456782", "Pune", "Care@123"),

    ("Hope for Paws", "Amit Joshi", "amit@hopeforpaws.org",
     "9123456783", "Pimpri", "Hope@123"),

    ("Safe Strays Society", "Kavita More", "kavita@safestrays.org",
     "9123456784", "Kothrud, Pune", "Safe@123")
]

for n in ngos:
    cursor.execute("""
        INSERT OR IGNORE INTO ngos
        (name, contact, email, phone, location, password)
        VALUES (?, ?, ?, ?, ?, ?)
    """, n)


# -------------------------
# GET NGO IDs
# -------------------------

ngo_ids = {}

for email in [
    "neha@pawsrescue.org",
    "rahul@happytails.org",
    "snehal@animalcare.org",
    "amit@hopeforpaws.org",
    "kavita@safestrays.org"
]:
    row = cursor.execute(
        "SELECT id FROM ngos WHERE email = ?", (email,)
    ).fetchone()

    if row:
        ngo_ids[email] = row[0]


# -------------------------
# ANIMALS
# -------------------------

animals = [
    ("Bruno", "Dog", "Kothrud, Pune", "Healthy",
     ngo_ids["neha@pawsrescue.org"], "Available"),

    ("Rocky", "Dog", "Baner, Pune", "Injured leg - recovering",
     ngo_ids["rahul@happytails.org"], "Under Treatment"),

    ("Mia", "Cat", "Wakad, Pune", "Healthy",
     ngo_ids["neha@pawsrescue.org"], "Available"),

    ("Simba", "Cat", "Hadapsar, Pune", "Weak - recovering",
     ngo_ids["snehal@animalcare.org"], "Under Treatment"),

    ("Coco", "Dog", "Aundh, Pune", "Healthy",
     ngo_ids["amit@hopeforpaws.org"], "Available"),

    ("Max", "Dog", "Katraj, Pune", "Minor injury",
     ngo_ids["neha@pawsrescue.org"], "Under Treatment"),

    ("Lily", "Cat", "Viman Nagar, Pune", "Healthy",
     ngo_ids["kavita@safestrays.org"], "Available"),

    ("Tiger", "Dog", "Kharadi, Pune", "Vaccination pending",
     ngo_ids["snehal@animalcare.org"], "Available"),

    ("Oreo", "Cat", "Pimpri, Pune", "Healthy",
     ngo_ids["rahul@happytails.org"], "Available"),

    ("Sheru", "Dog", "Sinhagad Road, Pune", "Recovering",
     ngo_ids["amit@hopeforpaws.org"], "Under Treatment")
]

for a in animals:
    cursor.execute("""
        INSERT INTO animals
        (name, species, location, health, ngo_id, status)
        VALUES (?, ?, ?, ?, ?, ?)
    """, a)


# -------------------------
# GET CITIZEN IDs
# -------------------------

citizen_ids = {}

for email in [
    "aditi@gmail.com",
    "rahul@gmail.com",
    "sneha@gmail.com",
    "rohan@gmail.com",
    "priya@gmail.com",
    "neha@gmail.com",
    "akash@gmail.com",
    "pooja@gmail.com",
    "omkar@gmail.com",
    "isha@gmail.com"
]:
    row = cursor.execute(
        "SELECT id FROM citizens WHERE email = ?", (email,)
    ).fetchone()

    if row:
        citizen_ids[email] = row[0]


# -------------------------
# REPORTS
# -------------------------

reports = [
    ("aditi@gmail.com", "Dog", "Kothrud, Pune",
     "Injured stray dog near the main road",
     "neha@pawsrescue.org", "Pending"),

    ("rahul@gmail.com", "Cat", "Baner, Pune",
     "Stray cat needs food and medical help",
     "rahul@happytails.org", "Assigned"),

    ("sneha@gmail.com", "Dog", "Wakad, Pune",
     "Puppy found alone near a society gate",
     "neha@pawsrescue.org", "Rescued"),

    ("rohan@gmail.com", "Cat", "Hadapsar, Pune",
     "Injured cat near a bus stop",
     "snehal@animalcare.org", "Under Treatment"),

    ("priya@gmail.com", "Dog", "Katraj, Pune",
     "Dog has a visible leg injury",
     "amit@hopeforpaws.org", "Assigned"),

    ("neha@gmail.com", "Cat", "Aundh, Pune",
     "Sick stray cat near a residential area",
     "kavita@safestrays.org", "Pending"),

    ("akash@gmail.com", "Dog", "Viman Nagar, Pune",
     "Stray dog needs vaccination",
     "neha@pawsrescue.org", "Rescued"),

    ("pooja@gmail.com", "Cat", "Kharadi, Pune",
     "Lost/stray kitten found near a shop",
     "snehal@animalcare.org", "Assigned"),

    ("omkar@gmail.com", "Dog", "Pimpri, Pune",
     "Injured dog found near a parking area",
     "rahul@happytails.org", "Under Treatment"),

    ("isha@gmail.com", "Dog", "Sinhagad Road, Pune",
     "Stray dog needs medical attention",
     "amit@hopeforpaws.org", "Pending")
]

for citizen_email, species, location, description, ngo_email, status in reports:

    citizen_id = citizen_ids[citizen_email]
    ngo_id = ngo_ids[ngo_email]

    cursor.execute("""
        INSERT INTO reports
        (citizen_id, species, location, description, ngo_id, date, status)
        VALUES (?, ?, ?, ?, ?, date('now'), ?)
    """, (
        citizen_id,
        species,
        location,
        description,
        ngo_id,
        status
    ))


# Save everything
conn.commit()
conn.close()

print("================================")
print("ALL DATA ADDED SUCCESSFULLY!")
print("================================")
print("Citizens : 10")
print("NGOs     : 5")
print("Animals  : 10")
print("Reports  : 10")