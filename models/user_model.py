from db import get_db_connection
from psycopg2.extras import RealDictCursor


def create_user(username, email, password_hash):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute(
        """
        INSERT INTO users (username, email, password, is_verified, created_at)
        VALUES (%s, %s, %s, TRUE, NOW())
        RETURNING id, username, email, is_verified
        """,
        (username, email, password_hash)
    )

    user = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    return user


def get_user_by_email(email):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute(
        "SELECT * FROM users WHERE email = %s",
        (email,)
    )

    user = cur.fetchone()

    cur.close()
    conn.close()

    return user


def get_user_by_id(user_id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute(
        "SELECT * FROM users WHERE id = %s",
        (user_id,)
    )

    user = cur.fetchone()

    cur.close()
    conn.close()

    return user
