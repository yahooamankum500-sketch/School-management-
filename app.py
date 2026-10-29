import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_session import Session
from database import verify_admin

# Blueprints import karo
from modules.students import students_bp
from modules.fees import fees_bp
from modules.auth import login_required

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-change-me")
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Blueprint Register karo
app.register_blueprint(students_bp)
app.register_blueprint(fees_bp)

@app.route("/")
def home():
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        admin = verify_admin(username, password)
        
        if admin:
            session["admin_id"] = admin["id"]
            session["admin_name"] = admin["full_name"] or admin["username"]
            return redirect(url_for("dashboard"))
            
        flash("Galat Username ya Password", "error")
        
    return render_template("login.html")

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
