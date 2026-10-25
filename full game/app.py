from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from database import (
    init_db,
    create_user,
    get_user_by_username,
    get_user_by_username_and_password,
    add_score,
    get_leaderboard,
    get_total_score_by_username,
)

app = Flask(__name__)
app.secret_key = "escapex-secret"

# =========================
# INIT DATABASE
# =========================
init_db(app)

# =========================
# MONGODB CONFIG
# =========================
client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=2000)
db = client["escapex"]
users = db["users"]


def get_mongo_user_by_username(username):
    try:
        return users.find_one({"username": username})
    except PyMongoError:
        app.logger.warning("MongoDB unavailable while reading signup data.")
        return None


def get_mongo_user_by_credentials(username, password):
    try:
        return users.find_one({"username": username, "password": password})
    except PyMongoError:
        app.logger.warning("MongoDB unavailable while checking login data.")
        return None


def sync_user_to_mongo(username, email, password):
    try:
        users.update_one(
            {"username": username},
            {"$set": {"email": email, "password": password}},
            upsert=True,
        )
    except PyMongoError:
        app.logger.warning("MongoDB unavailable while syncing auth user.")

# =========================
# AUTH ROUTES
# =========================

@app.route("/")
@app.route("/auth")
def auth():
    return render_template("auth.html", mode=request.args.get("mode", "login"))


@app.route("/signup", methods=["POST"])
def signup():
    username = request.form.get("username")
    email = request.form.get("email")
    password = request.form.get("password")

    if not username or not email or not password:
        flash("All fields are required.")
        return redirect(url_for("auth", mode="signup"))

    try:
        existing_sql_user = get_user_by_username(username)
        existing_mongo_user = get_mongo_user_by_username(username)

        if existing_sql_user or existing_mongo_user:
            flash("Username already exists.")
            return redirect(url_for("auth", mode="signup"))

        sql_user = create_user(username, email, password)
        sync_user_to_mongo(username, email, password)

        session["user_id"] = sql_user["id"]
        session["username"] = username

        return redirect(url_for("main_menu"))

    except Exception:
        app.logger.exception("Signup error")
        flash("Internal server error during signup. Try again later.")
        return redirect(url_for("auth", mode="signup"))


@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username")
    password = request.form.get("password")

    if not username or not password:
        flash("Username and password are required.")
        return redirect(url_for("auth"))

    try:
        sql_user = get_user_by_username_and_password(username, password)
        mongo_user = get_mongo_user_by_credentials(username, password)

        if not sql_user and not mongo_user:
            flash("Invalid username or password.")
            return redirect(url_for("auth"))

        if not sql_user:
            sql_user = create_user(username, mongo_user.get("email", ""), password)

        sync_user_to_mongo(username, sql_user["email"], password)
        session["user_id"] = sql_user["id"]
        session["username"] = username

        return redirect(url_for("main_menu"))

    except Exception:
        app.logger.exception("Login error")
        flash("Internal server error during login. Try again later.")
        return redirect(url_for("auth"))

# =========================
# MAIN PAGES
# =========================

@app.route("/main-menu")
def main_menu():
    return render_template("main-menu.html")


@app.route("/levels")
def levels():
    languages = [
        {"name": "C", "route": "c_quiz"},
        {"name": "C++", "route": "cpp_quiz"},
        {"name": "Java", "route": "java_quiz"},
        {"name": "PHP", "route": "php_quiz"},
        {"name": "Python", "route": "python_quiz"},
    ]
    return render_template("levels.html", languages=languages, total_levels=20)


@app.route("/option")
def option():
    return render_template("option.html")


@app.route("/exit")
def exit_page():
    return render_template("exit.html")


# =========================
# AI LEADERBOARD
# =========================

@app.route("/ai-leaderboard")
def ai_leaderboard():
    # Try to read usernames from MongoDB and get their scores from SQLite.
    leaders_list = []
    try:
        mongo_users = list(users.find({}, {"username": 1, "_id": 0}))
        for mu in mongo_users:
            username = mu.get("username")
            if not username:
                continue
            score = get_total_score_by_username(username)
            leaders_list.append({"username": username, "score": score})

        # If there are no MongoDB users, fallback to SQLite leaderboard
        if not leaders_list:
            sqlite_rows = get_leaderboard(limit=20)
            for row in sqlite_rows:
                leaders_list.append({"username": row["username"], "score": row["score"] or 0})

    except Exception:
        # If MongoDB is unreachable or any error occurs, fall back to SQLite
        sqlite_rows = get_leaderboard(limit=20)
        for row in sqlite_rows:
            leaders_list.append({"username": row["username"], "score": row["score"] or 0})

    # Final fallback demo data if still empty
    if not leaders_list:
        leaders_list = [
            {"username": "Gnanaprasad", "score": 150},
            {"username": "Player2", "score": 120},
            {"username": "Player3", "score": 100},
        ]

    # Sort and limit
    leaders_list = sorted(leaders_list, key=lambda x: x["score"], reverse=True)[:20]
    return render_template("ai-leaderboard.html", leaders=leaders_list)


@app.route("/api/submit-score", methods=["POST"])
def submit_score():
    if "user_id" not in session:
        return "Unauthorized", 401

    data = request.get_json(silent=True) or {}
    lang = data.get("lang")
    score = data.get("score")

    if not lang or not isinstance(score, int):
        return "Bad Request", 400

    add_score(session["user_id"], lang, score)
    return jsonify(ok=True)

# =========================
# QUIZ ROUTES
# =========================

@app.route("/c-quiz")
def c_quiz():
    return render_template("c_quiz.html")


@app.route("/cpp-quiz")
def cpp_quiz():
    return render_template("cpp_quiz.html")


@app.route("/java-quiz")
def java_quiz():
    return render_template("java_quiz.html")


@app.route("/python-quiz")
def python_quiz():
    return render_template("python_quiz.html")


@app.route("/php-quiz")
def php_quiz():
    return render_template("php_quiz.html")

# =========================
# RUN SERVER
# =========================

if __name__ == "__main__":
    app.run(debug=True)
