# database.py
import sqlite3
from flask import g

DB_PATH = "escapex.db"

def get_db():
    """Get a connection stored on the Flask `g` object."""
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    """Close the DB at the end of the request."""
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_db(app):
    """Call this from app.py to register teardown + create tables."""
    app.teardown_appcontext(close_db)
    with app.app_context():
        db = get_db()
        create_tables(db)
        db.commit()

def create_tables(db):
    """Create tables if they don't exist."""
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT,
            password TEXT NOT NULL
        );

        -- progress per user per language
        CREATE TABLE IF NOT EXISTS progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            lang TEXT NOT NULL,
            level INTEGER NOT NULL,
            completed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, lang, level),
            FOREIGN KEY(user_id) REFERENCES users(id)
        );

        -- optional scores table
        CREATE TABLE IF NOT EXISTS scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            lang TEXT NOT NULL,
            total_score INTEGER NOT NULL DEFAULT 0,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, lang),
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        """
    )

# ---------- USER HELPERS ----------

def create_user(username, email, password_hash):
    db = get_db()
    db.execute(
        "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
        (username, email, password_hash),
    )
    db.commit()
    return get_user_by_username(username)

def get_user_by_username(username):
    db = get_db()
    cur = db.execute(
        "SELECT * FROM users WHERE username = ?",
        (username,),
    )
    return cur.fetchone()

def get_user_by_id(user_id):
    db = get_db()
    cur = db.execute(
        "SELECT * FROM users WHERE id = ?",
        (user_id,),
    )
    return cur.fetchone()

def get_user_by_username_and_password(username, password):
    db = get_db()
    cur = db.execute(
        "SELECT * FROM users WHERE username = ? AND password = ?",
        (username, password),
    )
    return cur.fetchone()

# ---------- PROGRESS HELPERS ----------

def mark_level_completed(user_id, lang, level):
    """Insert progress row if not exists."""
    db = get_db()
    db.execute(
        """
        INSERT OR IGNORE INTO progress (user_id, lang, level)
        VALUES (?, ?, ?)
        """,
        (user_id, lang, level),
    )
    db.commit()

def get_progress_for_user(user_id):
    """
    Return dict like:
    {
      "c": {1: True, 2: True},
      "cpp": {1: True},
      ...
    }
    """
    db = get_db()
    cur = db.execute(
        "SELECT lang, level FROM progress WHERE user_id = ?",
        (user_id,),
    )
    rows = cur.fetchall()
    result = {}
    for r in rows:
        lang = r["lang"]
        level = r["level"]
        result.setdefault(lang, {})[level] = True
    return result

def get_total_levels_completed(user_id):
    db = get_db()
    cur = db.execute(
        "SELECT COUNT(*) AS c FROM progress WHERE user_id = ?",
        (user_id,),
    )
    row = cur.fetchone()
    return row["c"] if row else 0

# ---------- SCORE HELPERS ----------

def add_score(user_id, lang, points):
    """
    Increase total_score for a language.
    """
    db = get_db()
    db.execute(
        """
        INSERT INTO scores (user_id, lang, total_score)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id, lang)
        DO UPDATE SET total_score = total_score + excluded.total_score,
                      updated_at = CURRENT_TIMESTAMP
        """,
        (user_id, lang, points),
    )
    db.commit()

def get_scores_for_user(user_id):
    db = get_db()
    cur = db.execute(
        "SELECT lang, total_score FROM scores WHERE user_id = ?",
        (user_id,),
    )
    return cur.fetchall()

def get_leaderboard(limit=20):
    """
    Return top users by total score across all languages.
    """
    db = get_db()
    cur = db.execute(
        """
        SELECT u.username,
               SUM(s.total_score) AS score
        FROM users u
        JOIN scores s ON u.id = s.user_id
        GROUP BY u.id
        ORDER BY score DESC
        LIMIT ?
        """,
        (limit,),
    )
    return cur.fetchall()


def get_total_score_by_username(username):
    """
    Return total score (sum across languages) for a username.
    If the user has no scores, returns 0.
    """
    db = get_db()
    cur = db.execute(
        """
        SELECT SUM(s.total_score) AS score
        FROM users u
        JOIN scores s ON u.id = s.user_id
        WHERE u.username = ?
        """,
        (username,),
    )
    row = cur.fetchone()
    return int(row["score"]) if row and row["score"] is not None else 0
