import argparse
import getpass
import os
import sqlite3
from pymongo import MongoClient

DB_PATH = os.path.join(os.path.dirname(__file__), "escapex.db")
MONGO_URI = "mongodb://localhost:27017/"


def ensure_sqlite_users_table(conn):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT,
            password TEXT NOT NULL
        );
        """
    )
    conn.commit()


def add_sqlite_user(username, email, password):
    conn = sqlite3.connect(DB_PATH)
    ensure_sqlite_users_table(conn)
    cur = conn.execute("SELECT id FROM users WHERE username = ?", (username,))
    if cur.fetchone():
        conn.close()
        return False, "exists"
    conn.execute(
        "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
        (username, email, password),
    )
    conn.commit()
    conn.close()
    return True, None


def add_mongo_user(username, email, password):
    client = MongoClient(MONGO_URI)
    db = client["escapex"]
    users = db["users"]
    if users.find_one({"username": username}):
        return False, "exists"
    users.insert_one({"username": username, "email": email, "password": password})
    return True, None


def main():
    parser = argparse.ArgumentParser(description="Add a user to MongoDB and SQLite")
    parser.add_argument("--username", "-u", help="username")
    parser.add_argument("--email", "-e", help="email", default="")
    parser.add_argument("--password", "-p", help="password (will prompt if omitted)")
    args = parser.parse_args()

    username = args.username or input("Username: ")
    email = args.email
    password = args.password
    if not password:
        password = getpass.getpass("Password: ")

    # Add to MongoDB
    try:
        ok, reason = add_mongo_user(username, email, password)
    except Exception as e:
        ok = False
        reason = str(e)

    if not ok:
        if reason == "exists":
            print("MongoDB: user already exists")
        else:
            print(f"MongoDB: failed to add user: {reason}")
    else:
        print("MongoDB: user added")

    # Add to SQLite
    try:
        ok2, reason2 = add_sqlite_user(username, email, password)
    except Exception as e:
        ok2 = False
        reason2 = str(e)

    if not ok2:
        if reason2 == "exists":
            print("SQLite: user already exists")
        else:
            print(f"SQLite: failed to add user: {reason2}")
    else:
        print("SQLite: user added to", DB_PATH)


if __name__ == "__main__":
    main()
