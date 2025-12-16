from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3

app = Flask(__name__)
app.secret_key = "ewaste_secret_key"

# ---------------- DATABASE ----------------
def get_db():
    return sqlite3.connect("database.db")

def init_db():
    db = get_db()
    c = db.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        city TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS admins(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS requests(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        product TEXT,
        city TEXT,
        query TEXT,
        status TEXT,
        response TEXT
    )""")

    c.execute("INSERT OR IGNORE INTO admins VALUES(1,'admin','admin123')")
    db.commit()
    db.close()

init_db()

# ---------------- DISPOSAL CENTERS ----------------
centers = {
    "Bangalore": {
        "Mobile": "E-Parisaraa, Doddaballapur Road",
        "Battery": "TES-AMM Recycling, Peenya",
        "Laptop": "Saahas Zero Waste, Whitefield"
    },
    "Mysore": {
        "Mobile": "KSPCB Center, Hebbal",
        "Battery": "Eco Battery Hub",
        "Laptop": "EcoReco Mysuru"
    }
}

# ---------------- ROUTES ----------------
@app.route("/")
def home():
    return render_template("home.html")

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        try:
            db = get_db()
            db.execute("INSERT INTO users(username,password,city) VALUES(?,?,?)",
                       (request.form["username"], request.form["password"], request.form["city"]))
            db.commit()
            db.close()
            flash("Registration successful", "success")
            return redirect(url_for("user_login"))
        except:
            flash("Username already exists", "error")
    return render_template("register.html")

@app.route("/user_login", methods=["GET","POST"])
def user_login():
    if request.method == "POST":
        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (request.form["username"], request.form["password"])
        ).fetchone()
        db.close()
        if user:
            session["user_id"] = user[0]
            session["city"] = user[3]
            session["role"] = "user"
            return redirect(url_for("user_dashboard"))
        flash("Invalid credentials", "error")
    return render_template("user_login.html")

@app.route("/admin_login", methods=["GET","POST"])
def admin_login():
    if request.method == "POST":
        db = get_db()
        admin = db.execute(
            "SELECT * FROM admins WHERE username=? AND password=?",
            (request.form["username"], request.form["password"])
        ).fetchone()
        db.close()
        if admin:
            session["role"] = "admin"
            return redirect(url_for("admin_dashboard"))
        flash("Invalid admin credentials", "error")
    return render_template("admin_login.html")

@app.route("/user_dashboard")
def user_dashboard():
    if session.get("role") != "user":
        return redirect(url_for("user_login"))
    return render_template("user_dashboard.html")

@app.route("/request", methods=["GET","POST"])
def request_form():
    if session.get("role") != "user":
        return redirect(url_for("user_login"))

    if request.method == "POST":
        db = get_db()
        db.execute("""INSERT INTO requests
            (user_id,product,city,query,status,response)
            VALUES(?,?,?,?,?,?)""",
            (session["user_id"], request.form["product"],
             session["city"], request.form["query"],
             "Pending", ""))
        db.commit()
        db.close()
        return redirect(url_for("my_requests"))
    return render_template("request_form.html")

@app.route("/my_requests")
def my_requests():
    db = get_db()
    data = db.execute(
        "SELECT * FROM requests WHERE user_id=?",
        (session["user_id"],)
    ).fetchall()
    db.close()
    return render_template("my_requests.html", data=data, centers=centers)

@app.route("/admin_dashboard", methods=["GET","POST"])
def admin_dashboard():
    if session.get("role") != "admin":
        return redirect(url_for("admin_login"))

    db = get_db()
    if request.method == "POST":
        db.execute(
            "UPDATE requests SET status=?, response=? WHERE id=?",
            (request.form["status"], request.form["response"], request.form["id"])
        )
        db.commit()

    data = db.execute("""
        SELECT r.id, u.username, r.product, r.city, r.query, r.status
        FROM requests r JOIN users u ON r.user_id=u.id
    """).fetchall()
    db.close()
    return render_template("admin_dashboard.html", data=data)

@app.route("/awareness")
def awareness():
    return render_template("awareness.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(debug=True)
