import os
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not set")


def get_db_connection():
    return psycopg2.connect(DATABASE_URL, sslmode="require")


def init_db():
    conn = get_db_connection()
    cur = conn.cursor()

    # 🔥 RESET TABLES (DEV ONLY)
    cur.execute("DROP TABLE IF EXISTS ratings CASCADE;")
    cur.execute("DROP TABLE IF EXISTS rides CASCADE;")
    cur.execute("DROP TABLE IF EXISTS users CASCADE;")

    # USERS TABLE
    cur.execute("""
        CREATE TABLE users (
            id SERIAL PRIMARY KEY,
            username TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            is_verified BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)

    # RIDES TABLE
    cur.execute("""
        CREATE TABLE rides (
            id SERIAL PRIMARY KEY,
            origin TEXT NOT NULL,
            destination TEXT NOT NULL,
            budget INTEGER NOT NULL,
            status TEXT DEFAULT 'Pending',
            rider_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            driver_id INTEGER REFERENCES users(id),
            accepted_at TIMESTAMP,
            completed_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)

    # RATINGS TABLE
    cur.execute("""
        CREATE TABLE ratings (
            id SERIAL PRIMARY KEY,
            ride_id INTEGER REFERENCES rides(id) ON DELETE CASCADE,
            rider_id INTEGER REFERENCES users(id),
            driver_id INTEGER REFERENCES users(id),
            rating INTEGER CHECK (rating >= 1 AND rating <= 5),
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)

    conn.commit()
    cur.close()
    conn.close()

    print("Database initialized successfully.")