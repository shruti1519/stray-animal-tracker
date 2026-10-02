import sqlite3
from datetime import date
from functools import wraps
from flask import Flask, render_template, request, redirect, session, flash, g
from werkzeug.security import generate_password_hash as H, check_password_hash as C

app = Flask(__name__)
app.secret_key = "change-this-secret"
DB = "stray.db"
ROLES = {"citizen": "citizens", "ngo": "ngos", "admin": "admins"}
SCHEMA = """
CREATE TABLE IF NOT EXISTS citizens(id INTEGER PRIMARY KEY, name, email UNIQUE, phone, area, password);
CREATE TABLE IF NOT EXISTS ngos(id INTEGER PRIMARY KEY, name, contact, email UNIQUE, phone, location, password);
CREATE TABLE IF NOT EXISTS admins(id INTEGER PRIMARY KEY, name, email UNIQUE, password);
CREATE TABLE IF NOT EXISTS animals(id INTEGER PRIMARY KEY, name, species, location, health, ngo_id, status DEFAULT 'Available');
CREATE TABLE IF NOT EXISTS reports(id INTEGER PRIMARY KEY, citizen_id, species, location, description, ngo_id, rdate, status DEFAULT 'Pending');
CREATE TABLE IF NOT EXISTS adoptions(id INTEGER PRIMARY KEY, citizen_id, animal_id, adate, status DEFAULT 'Pending');
CREATE TABLE IF NOT EXISTS feedback(id INTEGER PRIMARY KEY, citizen_id, ngo_id, rating, comment);
"""

def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close(e):
    d = g.pop("db", None)
    if d: d.close()

def q(sql, args=(), one=False):
    rows = db().execute(sql, args).fetchall()
    db().commit()
    return (rows[0] if rows else None) if one else rows

def init():
    with sqlite3.connect(DB) as c:
        c.executescript(SCHEMA)
        if not c.execute("SELECT 1 FROM admins").fetchone():
            c.execute("INSERT INTO admins(name,email,password) VALUES('Admin One','admin1@gmail.com',?)", (H("admin123"),))
            for n, h, e, p, l in [("Paws Rescue NGO","Neha Shah","hr@pawsrescue.org","9123456780","Pune"),
                                  ("Happy Tails Shelter","Rahul Mehta","hr@happytails.org","9123456781","Mumbai")]:
                c.execute("INSERT INTO ngos(name,contact,email,phone,location,password) VALUES(?,?,?,?,?,?)", (n, h, e, p, l, H("ngo12345")))
            for n, s, l, h, ngo in [("Bruno","Dog","Kothrud, Pune","Healthy",1),("Mia","Cat","Baner, Pune","Needs vaccination",1),
                                    ("Rocky","Dog","Andheri, Mumbai","Injured leg - recovering",2)]:
                c.execute("INSERT INTO animals(name,species,location,health,ngo_id) VALUES(?,?,?,?,?)", (n, s, l, h, ngo))

def need(*roles):
    def deco(f):
        @wraps(f)
        def w(*a, **k):
            if session.get("role") not in roles:
                return redirect("/login/" + roles[0])
            return f(*a, **k)
        return w
    return deco

def fld(label, name, type="text", value="", options=None, ro=False):
    return dict(label=label, name=name, type=type, value=value, options=options, ro=ro)

def pairs(items): return [(x, x) for x in items]
def rows(sql, args=()): return [list(r) for r in q(sql, args)]

def dash(title, sub, cards):
    return render_template("dashboard.html", title=title, sub=sub, cards=cards)

# ---------- public ----------
@app.route("/")
def index(): return render_template("index.html")

@app.route("/login/<role>", methods=["GET", "POST"])
def login(role):
    if role not in ROLES: return redirect("/")
    if request.method == "POST":
        u = q(f"SELECT * FROM {ROLES[role]} WHERE email=?", (request.form["email"].strip(),), True)
        if u and C(u["password"], request.form["password"]):
            session.clear(); session.update(role=role, uid=u["id"], name=u["name"])
            return redirect(f"/{role}-dashboard")
        flash("Invalid email or password")
    return render_template("login.html", role=role)

@app.route("/logout")
def logout():
    session.clear(); return redirect("/")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        f = request.form
        if f["password"] != f["confirm"]:
            flash("Passwords do not match")
        else:
            try:
                q("INSERT INTO citizens(name,email,phone,area,password) VALUES(?,?,?,?,?)",
                  (f["name"], f["email"], f["phone"], f["area"], H(f["password"])))
                flash("Account created. Please login."); return redirect("/login/citizen")
            except sqlite3.IntegrityError:
                flash("Email already registered")
    fields = [fld("Full Name","name"), fld("Email","email","email"), fld("Phone Number","phone"), fld("Area / City","area"),
              fld("Password","password","password"), fld("Confirm Password","confirm","password")]
    return render_template("form.html", title="Citizen Registration", icon="🐾", sub="Create an account to report and adopt strays",
                           fields=fields, button="Create Account", action="/register")

# ---------- citizen ----------
@app.route("/citizen-dashboard")
@need("citizen")
def citizen_dashboard():
    return dash(f"Welcome, {session['name']}! 👋", "Help stray animals from one place.", [
        ("🚨","Report Stray","Report a stray animal you saw.","/report"),
        ("📋","My Reports","Track your reports.","/my-reports"),
        ("🐶","Adopt","Browse animals needing a home.","/animals"),
        ("❤️","My Adoptions","Track adoption requests.","/my-adoptions"),
        ("⭐","Feedback","Rate an NGO's work.","/feedback"),
        ("👤","My Profile","View your information.","/profile")])

@app.route("/report", methods=["GET", "POST"])
@need("citizen")
def report():
    if request.method == "POST":
        f = request.form
        q("INSERT INTO reports(citizen_id,species,location,description,rdate) VALUES(?,?,?,?,?)",
          (session["uid"], f["species"], f["location"], f["description"], str(date.today())))
        flash("Report submitted. An NGO will respond soon."); return redirect("/my-reports")
    fields = [fld("Animal Type","species","select",options=pairs(["Dog","Cat","Cow","Bird","Other"])),
              fld("Location (landmark / area)","location"), fld("Description / Condition","description","textarea")]
    return render_template("form.html", title="Report Stray Animal", icon="🚨", sub="Tell us where you saw the animal",
                           fields=fields, button="Submit Report", action="/report")

@app.route("/my-reports")
@need("citizen")
def my_reports():
    r = rows("SELECT id,rdate,species,location,status FROM reports WHERE citizen_id=? ORDER BY id DESC", (session["uid"],))
    return render_template("table.html", title="My Reports", icon="📋", sub="Track the animals you reported",
                           cols=["Report ID","Date","Animal","Location","Status"], rows=r, sidx=4)

@app.route("/animals")
@need("citizen")
def animals():
    a = q("SELECT a.*, n.name ngo FROM animals a LEFT JOIN ngos n ON n.id=a.ngo_id")
    return render_template("cards.html", animals=a)

@app.route("/adopt/<int:i>", methods=["POST"])
@need("citizen")
def adopt(i):
    q("INSERT INTO adoptions(citizen_id,animal_id,adate) VALUES(?,?,?)", (session["uid"], i, str(date.today())))
    flash("Adoption request sent"); return redirect("/my-adoptions")

@app.route("/my-adoptions")
@need("citizen")
def my_adoptions():
    r = rows("SELECT d.id,d.adate,a.name,a.species,n.name,d.status FROM adoptions d JOIN animals a ON a.id=d.animal_id "
             "LEFT JOIN ngos n ON n.id=a.ngo_id WHERE d.citizen_id=? ORDER BY d.id DESC", (session["uid"],))
    return render_template("table.html", title="My Adoptions", icon="❤️", sub="Your adoption requests",
                           cols=["ID","Date","Animal","Type","NGO","Status"], rows=r, sidx=5)

@app.route("/feedback", methods=["GET", "POST"])
@need("citizen")
def feedback():
    if request.method == "POST":
        f = request.form
        q("INSERT INTO feedback(citizen_id,ngo_id,rating,comment) VALUES(?,?,?,?)", (session["uid"], f["ngo"], f["rating"], f["comment"]))
        flash("Thank you! Feedback submitted.")
    ngos = [(n["id"], n["name"]) for n in q("SELECT id,name FROM ngos")]
    fields = [fld("NGO","ngo","select",options=ngos), fld("Rating","rating","select",options=[(i, f"{i} - {'⭐'*i}") for i in range(5,0,-1)]),
              fld("Feedback","comment","textarea")]
    return render_template("form.html", title="Feedback", icon="⭐", sub="Share your experience",
                           fields=fields, button="Submit Feedback", action="/feedback")

@app.route("/profile")
@need("citizen")
def profile():
    u = q("SELECT * FROM citizens WHERE id=?", (session["uid"],), True)
    fields = [fld("Name","n",value=u["name"],ro=True), fld("Email","e",value=u["email"],ro=True),
              fld("Phone","p",value=u["phone"],ro=True), fld("Area","a",value=u["area"],ro=True)]
    return render_template("form.html", title="My Profile", icon="👤", sub="Your information", fields=fields, button=None)

# ---------- NGO ----------
@app.route("/ngo-dashboard")
@need("ngo")
def ngo_dashboard():
    return dash(f"Welcome, {session['name']}! 👋", "Manage rescues and adoptions.", [
        ("🏢","NGO Profile","View NGO details.","/ngo-profile"),
        ("🐕","Our Animals","Animals under your care.","/ngo-animals"),
        ("🚨","Reports","Stray reports from citizens.","/ngo-reports"),
        ("❤️","Adoption Requests","Approve or reject requests.","/ngo-adoptions")])

@app.route("/ngo-profile")
@need("ngo")
def ngo_profile():
    u = q("SELECT * FROM ngos WHERE id=?", (session["uid"],), True)
    fields = [fld(l, k, value=u[k], ro=True) for l, k in [("NGO Name","name"),("Contact Person","contact"),("Email","email"),("Phone","phone"),("Location","location")]]
    return render_template("form.html", title="NGO Profile", icon="🏢", sub="Your organisation", fields=fields, button=None)

@app.route("/ngo-animals")
@need("ngo")
def ngo_animals():
    r = rows("SELECT id,name,species,location,health,status FROM animals WHERE ngo_id=?", (session["uid"],))
    return render_template("table.html", title="Our Animals", icon="🐕", sub="Animals under your care",
                           cols=["ID","Name","Type","Location","Health","Status"], rows=r, sidx=5)

def report_table(role):
    r = rows("SELECT r.id,r.rdate,c.name,c.phone,r.species,r.location,r.description,r.status FROM reports r "
             "JOIN citizens c ON c.id=r.citizen_id ORDER BY r.id DESC")
    return render_template("table.html", title="Stray Reports", icon="🚨", sub="Update rescue status",
                           cols=["ID","Date","Citizen","Phone","Animal","Location","Details","Status"], rows=r, sidx=7,
                           upd=("/report-status", ["Pending","Rescued","Closed"]))

@app.route("/ngo-reports")
@need("ngo")
def ngo_reports(): return report_table("ngo")

@app.route("/admin-reports")
@need("admin")
def admin_reports(): return report_table("admin")

@app.route("/report-status", methods=["POST"])
@need("ngo", "admin")
def report_status():
    q("UPDATE reports SET status=?, ngo_id=COALESCE(?,ngo_id) WHERE id=?",
      (request.form["status"], session["uid"] if session["role"] == "ngo" else None, request.form["id"]))
    flash("Status updated"); return redirect(f"/{session['role']}-reports")

@app.route("/ngo-adoptions")
@need("ngo")
def ngo_adoptions():
    r = rows("SELECT d.id,d.adate,c.name,c.phone,a.name,d.status FROM adoptions d JOIN animals a ON a.id=d.animal_id "
             "JOIN citizens c ON c.id=d.citizen_id WHERE a.ngo_id=? ORDER BY d.id DESC", (session["uid"],))
    return render_template("table.html", title="Adoption Requests", icon="❤️", sub="Approve or reject",
                           cols=["ID","Date","Citizen","Phone","Animal","Status"], rows=r, sidx=5,
                           upd=("/adoption-status", ["Pending","Approved","Rejected"]))

@app.route("/adoption-status", methods=["POST"])
@need("ngo")
def adoption_status():
    s, i = request.form["status"], request.form["id"]
    q("UPDATE adoptions SET status=? WHERE id=?", (s, i))
    if s == "Approved":
        q("UPDATE animals SET status='Adopted' WHERE id=(SELECT animal_id FROM adoptions WHERE id=?)", (i,))
    flash("Status updated"); return redirect("/ngo-adoptions")

# ---------- admin ----------
@app.route("/admin-dashboard")
@need("admin")
def admin_dashboard():
    return dash(f"Welcome, {session['name']}! 👋", "Manage the Stray Animal Tracker.", [
        ("🧑","Citizens","View registered citizens.","/admin-citizens"),
        ("🏢","NGOs","View registered NGOs.","/admin-ngos"),
        ("🐾","Animals","Add, edit and manage animals.","/admin-animals"),
        ("🚨","Reports","View and update reports.","/admin-reports")])

@app.route("/admin-citizens")
@need("admin")
def admin_citizens():
    return render_template("table.html", title="Citizens", icon="🧑", sub="Registered citizens",
        cols=["ID","Name","Email","Phone","Area"], rows=rows("SELECT id,name,email,phone,area FROM citizens"))

@app.route("/admin-ngos")
@need("admin")
def admin_ngos():
    return render_template("table.html", title="NGOs", icon="🏢", sub="Registered NGOs",
        cols=["ID","NGO","Contact","Email","Phone","Location"], rows=rows("SELECT id,name,contact,email,phone,location FROM ngos"))

@app.route("/admin-animals")
@need("admin")
def admin_animals():
    r = rows("SELECT a.id,a.name,a.species,a.location,a.health,n.name,a.status FROM animals a LEFT JOIN ngos n ON n.id=a.ngo_id")
    return render_template("table.html", title="Animals", icon="🐾", sub="Animals in the system",
        cols=["ID","Name","Type","Location","Health","NGO","Status"], rows=r, sidx=6, edit=True)

def animal_form(i=None):
    a = q("SELECT * FROM animals WHERE id=?", (i,), True) if i else None
    if request.method == "POST":
        f = request.form
        v = (f["name"], f["species"], f["location"], f["health"], f["ngo"], f["status"])
        if i: q("UPDATE animals SET name=?,species=?,location=?,health=?,ngo_id=?,status=? WHERE id=?", v + (i,))
        else: q("INSERT INTO animals(name,species,location,health,ngo_id,status) VALUES(?,?,?,?,?,?)", v)
        flash("Saved"); return redirect("/admin-animals")
    g_ = lambda k: a[k] if a else ""
    ngos = [(n["id"], n["name"]) for n in q("SELECT id,name FROM ngos")]
    fields = [fld("Name","name",value=g_("name")), fld("Species","species","select",g_("species"),pairs(["Dog","Cat","Cow","Bird","Other"])),
              fld("Last Seen Location","location",value=g_("location")), fld("Health Condition","health",value=g_("health")),
              fld("NGO","ngo","select",g_("ngo_id"),ngos), fld("Status","status","select",g_("status"),pairs(["Available","Under Treatment","Adopted"]))]
    return render_template("form.html", title="Edit Animal" if i else "Add Animal", icon="✏️" if i else "🐾",
                           sub="Animal details", fields=fields, button="Update" if i else "Add Animal")

@app.route("/admin-add-animal", methods=["GET", "POST"])
@need("admin")
def admin_add_animal(): return animal_form()

@app.route("/admin-edit-animal/<int:i>", methods=["GET", "POST"])
@need("admin")
def admin_edit_animal(i): return animal_form(i)

@app.route("/admin-delete-animal/<int:i>")
@need("admin")
def admin_delete_animal(i):
    q("DELETE FROM animals WHERE id=?", (i,)); flash("Deleted"); return redirect("/admin-animals")

init()
if __name__ == "__main__":
    app.run(debug=True)
