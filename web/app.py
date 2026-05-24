from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import hashlib
import secrets
from database.db import Database
from models.users import Users


app = Flask(__name__)
app.secret_key = secrets.token_hex(32)  # Генерирует случайный ключ при запуске

db = Database("db.sqlite")

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def get_current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    try:
        return Users(db, user_id)
    except ValueError:
        session.clear()
        return None

@app.route("/")
def mainpage():
    user = get_current_user()
    if not user:
        return redirect(url_for("login"))
    return render_template(
        "main.html",
        heading="Главная",
        message=f"Привет, слон {user.Username}!",
        is_logged=True
    )

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if not username or not password:
            return render_template("register.html", error="Please fill in both username and password")

        # Проверка длины пароля
        if len(password) < 6:
            return render_template("register.html", error="Password must be at least 6 characters long")

        # Проверка существования пользователя
        existing = db.fetchone('SELECT * FROM "Users" WHERE "Username" = ?', (username,))
        if existing:
            return render_template("register.html", error="Username already exists")

        try:
            user = Users(db)
            user.Username = username
            user.Password = hash_password(password)
            user.HashType = "sha256"
            user.UserRoleID = 1
            user.Author = "system"
            user.Created_date = None
            user.Last_editor = "system"
            user.Last_change = None
            user.Change_cnt = 0
            user.dbInsert()

            session["user_id"] = user.ID
            session["username"] = user.Username
            return redirect(url_for("mainpage"))
        except Exception as e:
            return render_template("register.html", error=f"Registration failed: {str(e)}")

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if not username or not password:
            return render_template("login.html", error="Please fill in both fields")

        row = db.fetchone('SELECT * FROM "Users" WHERE "Username" = ?', (username,))
        if not row or row["Password"] != hash_password(password):
            return render_template("login.html", error="Invalid username or password")

        session["user_id"] = row["ID"]
        session["username"] = row["Username"]
        return redirect(url_for("mainpage"))

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/user/<int:id>")
def get_user(id: int):
    user = get_current_user()
    if not user:
        return jsonify({"error": "not authenticated"}), 401

    if user.ID != id:
        return jsonify({"error": "forbidden"}), 403

    return jsonify({
        "ID": user.ID,
        "Username": user.Username,
        "HashType": user.HashType,
        "UserRoleID": user.UserRoleID,
        "Author": user.Author,
        "Created_date": user.Created_date,
        "Last_editor": user.Last_editor,
        "Last_change": user.Last_change,
        "Change_cnt": user.Change_cnt,
    })

@app.route("/user/config")
def user_config():
    user = get_current_user()
    if not user:
        return redirect(url_for("login"))

    return jsonify({
        "ID": user.ID,
        "Username": user.Username,
        "UserRoleID": user.UserRoleID,
        "HashType": user.HashType
    })

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=False, use_reloader=False)
