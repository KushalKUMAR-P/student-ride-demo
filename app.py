import os
from dotenv import load_dotenv

load_dotenv()

from flask import Flask, render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_db_connection, init_db

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

init_db()

@app.route("/", methods=["GET"])
def home():
    conn = get_db_connection()

    search_origin = request.args.get("origin")
    search_destination = request.args.get("destination")
    sort_order = request.args.get("sort")
    page = request.args.get("page", 1, type=int)

    per_page = 6
    offset = (page - 1) * per_page

    base_query = """
        FROM rides
        JOIN users AS rider ON rides.rider_id = rider.id
        LEFT JOIN users AS driver ON rides.driver_id = driver.id
    """

    filters = []
    params = []

    if search_origin:
        filters.append("rides.origin LIKE ?")
        params.append(f"%{search_origin}%")

    if search_destination:
        filters.append("rides.destination LIKE ?")
        params.append(f"%{search_destination}%")

    if filters:
        base_query += " WHERE " + " AND ".join(filters)

    order_clause = ""
    if sort_order == "low":
        order_clause = " ORDER BY rides.budget ASC"
    elif sort_order == "high":
        order_clause = " ORDER BY rides.budget DESC"

    count_query = "SELECT COUNT(*) " + base_query
    total_rides = conn.execute(count_query, params).fetchone()[0]

    final_query = """
        SELECT rides.*, 
               rider.username AS rider_name,
               driver.username AS driver_name
    """ + base_query + order_clause + " LIMIT ? OFFSET ?"

    rides = conn.execute(
        final_query,
        params + [per_page, offset]
    ).fetchall()

    total_users = conn.execute(
        "SELECT COUNT(*) FROM users"
    ).fetchone()[0]

    completed_rides = conn.execute(
        "SELECT COUNT(*) FROM rides WHERE status = 'Completed'"
    ).fetchone()[0]

    conn.close()

    total_pages = (total_rides + per_page - 1) // per_page

    return render_template(
        "index.html",
        rides=rides,
        total_rides=total_rides,
        page=page,
        total_pages=total_pages,
        total_users=total_users,
        completed_rides=completed_rides
    )



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

@app.route("/complete/<int:ride_id>")
def complete_ride(ride_id):
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db_connection()

    ride = conn.execute(
        "SELECT * FROM rides WHERE id = ?",
        (ride_id,)
    ).fetchone()

    if ride:
        # Only rider or driver can complete
        if ride["rider_id"] == session["user_id"] or ride["driver_id"] == session["user_id"]:
            conn.execute(
                "UPDATE rides SET status = ? WHERE id = ?",
                ("Completed", ride_id)
            )
            conn.commit()

    conn.close()

    return redirect("/")

if __name__ == "__main__":
    init_db()
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", 5000)),
        debug=os.getenv("FLASK_ENV") == "development"
    )

