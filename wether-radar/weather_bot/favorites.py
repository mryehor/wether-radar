import sqlite3
from contextlib import contextmanager
from pathlib import Path


DATABASE_PATH = Path(__file__).resolve().parent.parent / "favorites.sqlite3"


@contextmanager
def _connect():
    connection = sqlite3.connect(DATABASE_PATH, timeout=10)
    try:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS favorite_cities (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                city TEXT NOT NULL,
                UNIQUE (user_id, city)
            )
            """
        )
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def get_favorites(user_id):
    with _connect() as connection:
        return connection.execute(
            "SELECT id, city FROM favorite_cities WHERE user_id = ? ORDER BY city",
            (user_id,),
        ).fetchall()


def add_favorite(user_id, city):
    with _connect() as connection:
        cursor = connection.execute(
            """
            INSERT OR IGNORE INTO favorite_cities (user_id, city)
            VALUES (?, ?)
            """,
            (user_id, city),
        )
        return cursor.rowcount > 0


def remove_favorite(user_id, favorite_id):
    with _connect() as connection:
        cursor = connection.execute(
            "DELETE FROM favorite_cities WHERE user_id = ? AND id = ?",
            (user_id, favorite_id),
        )
        return cursor.rowcount > 0


def get_favorite(user_id, favorite_id):
    with _connect() as connection:
        return connection.execute(
            "SELECT city FROM favorite_cities WHERE user_id = ? AND id = ?",
            (user_id, favorite_id),
        ).fetchone()
