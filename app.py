from flask import Flask, render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

app = Flask(__name__)
app.secret_key = "devsecretkey"

DATABASE = "rides.db"


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()

    # Users table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    # Rides table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS rides (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            origin TEXT NOT NULL,
            destination TEXT NOT NULL,
            budget INTEGER NOT NULL,
            status TEXT NOT NULL,
            rider_id INTEGER NOT NULL,
            driver_id INTEGER,
            FOREIGN KEY (rider_id) REFERENCES users (id),
            FOREIGN KEY (driver_id) REFERENCES users (id)
        )
    """)

    conn.commit()
    conn.close()


@app.route("/")
def home():
    conn = get_db_connection()

    rides = conn.execute("""
        SELECT rides.*, 
               rider.username AS rider_name,
               driver.username AS driver_name
        FROM rides
        JOIN users AS rider ON rides.rider_id = rider.id
        LEFT JOIN users AS driver ON rides.driver_id = driver.id
    """).fetchall()

    conn.close()

    return render_template("index.html", rides=rides)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = generate_password_hash(request.form["password"])

        conn = get_db_connection()
        try:
            conn.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, password)
            )
            conn.commit()
        except:
            conn.close()
            return "Username already exists"

        conn.close()
        return redirect("/login")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        user = conn.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        ).fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect("/")
        else:
            return "Invalid credentials"

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/create", methods=["GET", "POST"])
def create():
    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":
        origin = request.form["origin"]
        destination = request.form["destination"]
        budget = request.form["budget"]

        conn = get_db_connection()
        conn.execute(
            "INSERT INTO rides (origin, destination, budget, status, rider_id) VALUES (?, ?, ?, ?, ?)",
            (origin, destination, budget, "Pending", session["user_id"])
        )
        conn.commit()
        conn.close()

        return redirect("/")

    return render_template("create_ride.html")


@app.route("/accept/<int:ride_id>")
def accept_ride(ride_id):
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db_connection()
    conn.execute(
        "UPDATE rides SET status = ?, driver_id = ? WHERE id = ?",
        ("Accepted", session["user_id"], ride_id)
    )
    conn.commit()
    conn.close()

    return redirect("/")



# Temporary debug route
@app.route("/debug_tables")
def debug_tables():
    conn = get_db_connection()
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table';"
    ).fetchall()
    conn.close()
    return str(tables)


init_db()

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db_connection()

    posted_rides = conn.execute(
        "SELECT * FROM rides WHERE rider_id = ?",
        (session["user_id"],)
    ).fetchall()

    accepted_rides = conn.execute(
        "SELECT * FROM rides WHERE driver_id = ?",
        (session["user_id"],)
    ).fetchall()

    conn.close()

    return render_template(
        "dashboard.html",
        posted_rides=posted_rides,
        accepted_rides=accepted_rides
    )

@app.route("/cancel/<int:ride_id>")
def cancel_ride(ride_id):
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db_connection()

    ride = conn.execute(
        "SELECT * FROM rides WHERE id = ?",
        (ride_id,)
    ).fetchone()

    if ride and ride["rider_id"] == session["user_id"]:
        conn.execute(
            "DELETE FROM rides WHERE id = ?",
            (ride_id,)
        )
        conn.commit()

    conn.close()

    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)

