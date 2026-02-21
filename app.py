import os
from dotenv import load_dotenv

load_dotenv()

from flask import Flask, render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
from psycopg2.extras import RealDictCursor

from db import get_db_connection, init_db
from models.user_model import create_user, get_user_by_email


app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY") or "dev-permanent-secret-123"
print("SECRET KEY LOADED:", app.secret_key)


# ✅ Initialize DB safely on startup (works for Gunicorn)
with app.app_context():
    try:
        init_db()
        print("Database initialized successfully.")
    except Exception as e:
        print("Database initialization error:", e)


@app.route("/health")
def health():
    return "OK"


@app.route("/", methods=["GET"])
def home():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

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
        filters.append("rides.origin ILIKE %s")
        params.append(f"%{search_origin}%")

    if search_destination:
        filters.append("rides.destination ILIKE %s")
        params.append(f"%{search_destination}%")

    if filters:
        base_query += " WHERE " + " AND ".join(filters)

    order_clause = ""
    if sort_order == "low":
        order_clause = " ORDER BY rides.budget ASC"
    elif sort_order == "high":
        order_clause = " ORDER BY rides.budget DESC"

    # Total rides count
    count_query = "SELECT COUNT(*) " + base_query
    cur.execute(count_query, params)
    total_rides = cur.fetchone()["count"]

    # Fetch rides
    final_query = """
        SELECT rides.*,
               rider.username AS rider_name,
               driver.username AS driver_name
    """ + base_query + order_clause + " LIMIT %s OFFSET %s"

    cur.execute(final_query, params + [per_page, offset])
    rides = cur.fetchall()

    # ⭐ Add Driver Rating Data Per Ride
    for ride in rides:
        if ride["driver_id"]:
            cur.execute("""
                SELECT AVG(rating) AS avg_rating, COUNT(*) AS total
                FROM ratings
                WHERE driver_id = %s
            """, (ride["driver_id"],))

            result = cur.fetchone()

            ride["avg_rating"] = round(result["avg_rating"], 1) if result["avg_rating"] else None
            ride["total_ratings"] = result["total"]
        else:
            ride["avg_rating"] = None
            ride["total_ratings"] = 0

    # 📊 Platform Metrics
    cur.execute("SELECT COUNT(*) FROM users")
    total_users = cur.fetchone()["count"]

    cur.execute("SELECT COUNT(*) FROM rides WHERE status = 'Completed'")
    completed_rides = cur.fetchone()["count"]

    cur.execute("SELECT AVG(rating) AS avg_rating FROM ratings")
    rating_result = cur.fetchone()

    if rating_result and rating_result["avg_rating"]:
        average_rating = round(rating_result["avg_rating"], 1)
    else:
        average_rating = 0

    cur.close()
    conn.close()

    total_pages = (total_rides + per_page - 1) // per_page

    return render_template(
        "index.html",
        rides=rides,
        total_rides=total_rides,
        page=page,
        total_pages=total_pages,
        total_users=total_users,
        completed_rides=completed_rides,
        average_rating=average_rating
    )

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])

        if not email.endswith(".edu"):
            return "Only .edu emails allowed"

        existing_user = get_user_by_email(email)
        if existing_user:
            return "Email already registered"

        create_user(username, email, password)
        return redirect("/login")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        print("FORM DATA:", request.form)
        email = request.form["email"]
        password = request.form["password"]

        user = get_user_by_email(email)

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["user_verified"] = user["is_verified"]
            return redirect("/")
        else:
            return "Invalid credentials"

    return render_template("login.html")

@app.route("/user/<int:user_id>")
def user_profile(user_id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Get user info
    cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cur.fetchone()

    if not user:
        cur.close()
        conn.close()
        return "User not found"

    # Average rating
    cur.execute("""
        SELECT AVG(rating) AS avg_rating, COUNT(*) AS total
        FROM ratings
        WHERE driver_id = %s
    """, (user_id,))
    rating_data = cur.fetchone()

    avg_rating = round(rating_data["avg_rating"], 1) if rating_data["avg_rating"] else 0
    total_ratings = rating_data["total"]

    # Completed rides
    cur.execute("""
        SELECT COUNT(*) AS total_completed
        FROM rides
        WHERE driver_id = %s AND status = 'Completed'
    """, (user_id,))
    completed_data = cur.fetchone()
    total_completed = completed_data["total_completed"]

    # Recent rides
    cur.execute("""
        SELECT origin, destination, completed_at
        FROM rides
        WHERE driver_id = %s AND status = 'Completed'
        ORDER BY completed_at DESC
        LIMIT 5
    """, (user_id,))
    recent_rides = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "profile.html",
        user=user,
        avg_rating=avg_rating,
        total_ratings=total_ratings,
        total_completed=total_completed,
        recent_rides=recent_rides
    )

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/create", methods=["GET", "POST"])
def create():
    if "user_id" not in session or not session.get("user_verified"):
        return redirect("/login")

    if request.method == "POST":
        origin = request.form["origin"]
        destination = request.form["destination"]
        budget = request.form["budget"]

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO rides (origin, destination, budget, rider_id)
            VALUES (%s, %s, %s, %s)
            """,
            (origin, destination, budget, session["user_id"])
        )

        conn.commit()
        cur.close()
        conn.close()

        return redirect("/")

    return render_template("create_ride.html")


@app.route("/accept/<int:ride_id>")
def accept_ride(ride_id):
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE rides
        SET status = 'Accepted',
            driver_id = %s,
            accepted_at = NOW()
        WHERE id = %s AND status = 'Pending'
        """,
        (session["user_id"], ride_id)
    )

    conn.commit()
    cur.close()
    conn.close()

    return redirect("/")


@app.route("/complete/<int:ride_id>")
def complete_ride(ride_id):
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("SELECT * FROM rides WHERE id = %s", (ride_id,))
    ride = cur.fetchone()

    if ride and (
        ride["rider_id"] == session["user_id"] or
        ride["driver_id"] == session["user_id"]
    ):
        cur.execute(
            """
            UPDATE rides
            SET status = 'Completed',
                completed_at = NOW()
            WHERE id = %s
            """,
            (ride_id,)
        )
        conn.commit()

    cur.close()
    conn.close()

    return redirect("/")


@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute(
        "SELECT * FROM rides WHERE rider_id = %s",
        (session["user_id"],)
    )
    posted_rides = cur.fetchall()

    cur.execute(
        "SELECT * FROM rides WHERE driver_id = %s",
        (session["user_id"],)
    )
    accepted_rides = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "dashboard.html",
        posted_rides=posted_rides,
        accepted_rides=accepted_rides
    )


@app.route("/rate/<int:ride_id>", methods=["POST"])
def rate_driver(ride_id):
    if "user_id" not in session:
        return redirect("/login")

    rating_value = int(request.form["rating"])

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute(
        "SELECT * FROM rides WHERE id = %s",
        (ride_id,)
    )
    ride = cur.fetchone()

    if not ride:
        return "Ride not found"

    # Only rider can rate after completion
    if ride["rider_id"] != session["user_id"] or ride["status"] != "Completed":
        return "Not allowed"

    cur.execute("""
        INSERT INTO ratings (ride_id, rider_id, driver_id, rating)
        VALUES (%s, %s, %s, %s)
    """, (ride_id, session["user_id"], ride["driver_id"], rating_value))

    conn.commit()
    cur.close()
    conn.close()

    return redirect("/dashboard")

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", 5000)),
        debug=os.getenv("FLASK_ENV") == "development"
    )
