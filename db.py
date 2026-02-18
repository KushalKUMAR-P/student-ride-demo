import sqlite3

DATABASE = "rides.db"

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

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
