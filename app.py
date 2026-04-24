from flask import Flask, request, redirect, session
import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "secret123"

def db():
    return sqlite3.connect("radar.db")

# ------------------ INIT DB ------------------
def init():
    conn = db()
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE,
        password TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS registry (
        plate TEXT PRIMARY KEY,
        owner TEXT,
        email TEXT,
        phone TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS violations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        plate TEXT,
        speed INTEGER,
        limit_speed INTEGER,
        time TEXT
    )""")

    cars = [
        ('IS-01-ABC','Daria','daria@mail.com','0712345678'),
        ('B-123-AAA','Ion Popescu','ion@mail.com','0722222222'),
        ('CJ-99-XYZ','Maria Ionescu','maria@mail.com','0733333333'),
        ('TM-10-BCD','Alex Georgescu','alex@mail.com','0744444444'),
        ('IS17IDE','Ignea Daria','minjianapark@gmail.com','0773932825')
    ]

    for car in cars:
        c.execute("INSERT OR IGNORE INTO registry VALUES (?,?,?,?)", car)

    conn.commit()
    conn.close()

init()

# ------------------ REGISTER ------------------
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        conn = db()
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (email,password) VALUES (?,?)",
                      (request.form["email"],
                       generate_password_hash(request.form["password"])))
            conn.commit()
        except:
            return "User exists"
        conn.close()
        return redirect("/login")

    return """<html><head><meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{font-family:Arial;background:linear-gradient(to right,#fbc2eb,#a6c1ee);display:flex;justify-content:center;align-items:center;height:100vh;margin:0;}
.box{background:white;padding:25px;border-radius:12px;width:90%;max-width:320px;text-align:center;}
input{width:100%;padding:10px;margin:8px 0;}
button{width:100%;padding:10px;background:#2ecc71;color:white;border:none;border-radius:6px;}
</style></head>
<body><div class="box">
<h2>📝 Register</h2>
<form method="post">
<input name="email" placeholder="Email">
<input type="password" name="password" placeholder="Password">
<button>Register</button>
</form>
<a href="/login">Back</a>
</div></body></html>"""

# ------------------ LOGIN ------------------
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        conn = db()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email=?", (request.form["email"],))
        user = c.fetchone()
        conn.close()

        if user and check_password_hash(user[2], request.form["password"]):
            session["user"] = request.form["email"]
            return redirect("/")
        return "Invalid login"

    return """<html><head><meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{font-family:Arial;background:linear-gradient(to right,#74ebd5,#ACB6E5);display:flex;justify-content:center;align-items:center;height:100vh;margin:0;}
.box{background:white;padding:25px;border-radius:12px;width:90%;max-width:320px;text-align:center;}
input{width:100%;padding:10px;margin:8px 0;}
button{width:100%;padding:10px;background:#3498db;color:white;border:none;border-radius:6px;}
</style></head>
<body><div class="box">
<h2>🔐 Login</h2>
<form method="post">
<input name="email" placeholder="Email">
<input type="password" name="password" placeholder="Password">
<button>Login</button>
</form>
<a href="/register">Create account</a>
</div></body></html>"""

# ------------------ LOGOUT ------------------
@app.route("/logout")
def logout():
    session.pop("user",None)
    return redirect("/login")

# ------------------ HOME ------------------
@app.route("/")
def home():
    if "user" not in session:
        return redirect("/login")

    search = request.args.get("search","").lower()

    conn = db()
    c = conn.cursor()

    c.execute("""
    SELECT r.plate,r.owner,r.email,r.phone,
           v.speed,v.limit_speed,v.time
    FROM registry r
    LEFT JOIN violations v ON r.plate=v.plate
    ORDER BY r.plate
    """)

    rows = c.fetchall()
    grouped = {}

    for r in rows:
        plate,owner,email,phone,speed,limit,time = r

        if search and search not in plate.lower() and (owner is None or search not in owner.lower()):
            continue

        if plate not in grouped:
            grouped[plate] = {"owner":owner,"email":email,"phone":phone,"violations":[]}

        if speed:
            grouped[plate]["violations"].append((speed,limit,time))

    html = f"""
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{{font-family:Arial;background:#eef2f3;margin:0;display:flex;justify-content:center;}}
.container{{width:95%;max-width:900px;margin-top:20px;}}
.card{{background:white;padding:15px;margin-bottom:10px;border-radius:10px;}}
.good{{color:green;font-weight:bold;}}
.bad{{color:red;font-weight:bold;}}
summary{{display:flex;justify-content:space-between;align-items:center;}}
button{{margin-left:5px;}}
</style>
</head>
<body>
<div class="container">

<h1>🚗 RadarViteza</h1>
Logged in as {session["user"]} | <a href="/logout">Logout</a>

<form method="get">
<input name="search" placeholder="Search" value="{search}">
<button>🔍</button>
</form>

<h3>Add / Update Car</h3>
<form method="post" action="/add">
<input name="plate" placeholder="Plate" required>
<input name="owner" placeholder="Owner">
<input name="email" placeholder="Email">
<input name="phone" placeholder="Phone">
<button>Save</button>
</form>
"""

    for plate,data in grouped.items():
        owner = data["owner"] or "UNKNOWN"
        email = data["email"] if data["email"] != "-" else "UNKNOWN"
        phone = data["phone"] if data["phone"] != "-" else "UNKNOWN"

        violations = data["violations"]
        count = len(violations)

        status_class = "bad" if count>0 else "good"
        status_icon = "🚨" if count>0 else "✅"

        html += f"""
<div class="card">
<details>
<summary>
<span><b>{plate}</b> ({owner})</span>
<span class="{status_class}">{status_icon} ({count})</span>

<span>
<a href="/send_email/{plate}"><button>📧</button></a>
<a href="/add_violation/{plate}"><button>➕</button></a>
<a href="/clear_violations/{plate}" onclick="return confirm('Clear violations?')"><button>🧹</button></a>
<a href="/delete/{plate}" onclick="return confirm('Delete?')"><button>🗑</button></a>
</span>
</summary>

<ul>
<li>👤 {owner}</li>
<li>📧 {email}</li>
<li>📞 {phone}</li>
"""

        if count == 0:
            html += "<li>✅ No violations</li>"
        else:
            for v in violations:
                html += f"<li>🚗 {v[0]} km/h (limit {v[1]}) at {v[2]}</li>"

        html += "</ul></details></div>"

    html += "</div></body></html>"
    conn.close()
    return html

# ------------------ ADD CAR ------------------
@app.route("/add", methods=["POST"])
def add():
    conn = db()
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO registry VALUES (?,?,?,?)",
              (request.form["plate"],request.form["owner"],request.form["email"],request.form["phone"]))
    conn.commit()
    conn.close()
    return redirect("/")

# ------------------ DELETE ------------------
@app.route("/delete/<plate>")
def delete(plate):
    conn = db()
    c = conn.cursor()
    c.execute("DELETE FROM registry WHERE plate=?", (plate,))
    c.execute("DELETE FROM violations WHERE plate=?", (plate,))
    conn.commit()
    conn.close()
    return redirect("/")

# ------------------ ADD VIOLATION ------------------
@app.route("/add_violation/<plate>")
def add_v(plate):
    conn = db()
    c = conn.cursor()
    c.execute("INSERT INTO violations VALUES (NULL,?,?,?,?)",
              (plate,90,60,datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()
    return redirect("/")

# ------------------ CLEAR VIOLATIONS ------------------
@app.route("/clear_violations/<plate>")
def clear_v(plate):
    conn = db()
    c = conn.cursor()
    c.execute("DELETE FROM violations WHERE plate=?", (plate,))
    conn.commit()
    conn.close()
    return redirect("/")

# ------------------ FAKE EMAIL ------------------
@app.route("/send_email/<plate>")
def mail(plate):
    conn = db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM violations WHERE plate=?", (plate,))
    count = c.fetchone()[0]
    conn.close()
    msg = "🚨 Ai amenda!" if count>0 else "✅ Totul bine!"
    return f"<h2 style='text-align:center'>{msg}<br>{plate}<br><a href='/'>Back</a></h2>"

# ------------------ EVENT ------------------
@app.route("/event", methods=["POST"])
def event():
    data = request.json
    conn = db()
    c = conn.cursor()
    c.execute("INSERT INTO violations VALUES (NULL,?,?,?,?)",
              (data["plate"],data["speed"],data["limit"],datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    c.execute("SELECT * FROM registry WHERE plate=?", (data["plate"],))
    if not c.fetchone():
        c.execute("INSERT INTO registry VALUES (?,?,?,?)",(data["plate"],"UNKNOWN","-","-"))
    conn.commit()
    conn.close()
    return {"status":"ok"}

# ------------------ RUN ------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
