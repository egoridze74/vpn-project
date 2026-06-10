from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import hashlib
import secrets
from datetime import datetime
from database.db import Database
from models.users import Users


app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

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

def register_user(username: str, password: str) -> dict:
    try:
        existing = db.fetchone('SELECT * FROM "Users" WHERE "Username" = ?', (username,))
        if existing:
            return {"success": False, "error": "Пользователь уже существует"}

        user = Users(db)
        user.Username = username
        user.Password = hash_password(password)
        user.HashType = "sha256"
        user.UserRoleID = 1
        user.Author = "system"
        user.Created_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        user.Last_editor = "system"
        user.Last_change = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        user.Change_cnt = 0
        user.dbInsert()

        return {"success": True, "user_id": user.ID, "error": None}
    except Exception as e:
        return {"success": False, "error": str(e)}

def authenticate_user(username: str, password: str) -> dict:
    try:
        password_hash = hash_password(password)
        row = db.fetchone(
            'SELECT * FROM "Users" WHERE "Username" = ? AND "Password" = ?',
            (username, password_hash)
        )
        
        if row:
            return {"success": True, "user_id": row["ID"], "error": None}
        else:
            return {"success": False, "error": "Неверный логин или пароль"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.route("/")
def mainpage():
    user = get_current_user()
    if not user:
        return redirect(url_for("login"))
    return render_template(
        "main.html",
        heading="Главная 🐘",
        message=f"Привет, слон {user.Username}!",
        is_logged=True
    )

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if not username or not password:
            return render_template("register.html", error="Заполните логин и пароль")

        if len(password) < 6:
            return render_template("register.html", error="Пароль должен быть минимум 6 символов")

        # Используем единую функцию регистрации
        result = register_user(username, password)
        
        if result["success"]:
            session["user_id"] = result["user_id"]
            session["username"] = username
            return redirect(url_for("mainpage"))
        else:
            return render_template("register.html", error=result["error"])

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if not username or not password:
            return render_template("login.html", error="Заполните логин и пароль")

        # Используем единую функцию аутентификации
        result = authenticate_user(username, password)
        
        if result["success"]:
            session["user_id"] = result["user_id"]
            session["username"] = username
            return redirect(url_for("mainpage"))
        else:
            return render_template("login.html", error=result["error"])

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/api/vpn/register", methods=["POST"])
def api_vpn_register():
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    
    if not username or not password:
        return jsonify({"error": "Заполните логин и пароль"}), 400
    
    if len(password) < 6:
        return jsonify({"error": "Пароль должен быть минимум 6 символов"}), 400
    
    result = register_user(username, password)
    
    if result["success"]:
        return jsonify({
            "status": "ok",
            "message": "Регистрация успешна",
            "user_id": result["user_id"]
        })
    else:
        return jsonify({"error": result["error"]}), 400

@app.route("/api/vpn/auth", methods=["POST"])
def api_vpn_auth():
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    
    if not username or not password:
        return jsonify({"error": "Заполните логин и пароль"}), 400
    
    result = authenticate_user(username, password)
    
    if result["success"]:
        token = secrets.token_hex(32)
        return jsonify({
            "status": "ok",
            "message": "Аутентификация успешна",
            "token": token,
            "user_id": result["user_id"],
            "username": username
        })
    else:
        return jsonify({"error": result["error"]}), 401

@app.route("/api/vpn/status", methods=["GET"])
def api_vpn_status():
    return jsonify({
        "status": "running",
        "server": "СЛОНЯРСКИЙ VPN 🐘",
    })

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

@app.route("/api/vpn/client/config")
def vpn_client_config():
    user = get_current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    
    return jsonify({
        "server": "vpn.service.local",
        "port": 1194,
        "username": user.Username,
        "protocol": "udp",
        "encryption": "xor"
    })

@app.route("/api/vpn/test", methods=["POST"])
def test_vpn_auth():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    user = db.fetchone(
        'SELECT * FROM "Users" WHERE "Username" = ? AND "Password" = ?',
        (username, password_hash)
    )
    
    if user:
        return jsonify({"status": "success", "message": "VPN authentication would work"})
    else:
        return jsonify({"status": "error", "message": "Invalid credentials"}), 401


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=False, use_reloader=False)