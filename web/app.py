from flask import Flask, render_template, request, redirect, url_for

app = Flask("%Krutoy_VPN%")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        value = request.form.get("%field%")
    return render_template(
        "login.html",
        title = "LogIn Page"
    )


@app.route("/user/config", methods=["GET", "POST"])
def pagex():


@app.route("/")
def mainpage():


@app.route("/user/<int:id>")
def get_user(id: int):
    return url_for(page, id=user_id)



if __name__ == "__main__":
    app.run()