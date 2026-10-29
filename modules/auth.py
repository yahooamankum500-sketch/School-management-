from functools import wraps
from flask import (
    Blueprint, render_template, request, redirect,
    url_for, session, flash
)
from database import verify_admin

auth_bp = Blueprint("auth", __name__)

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "admin_id" not in session:
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return wrapper

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if "admin_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        admin = verify_admin(username, password)
        if admin:
            session["admin_id"] = admin["id"]
            session["admin_name"] = admin["full_name"] or admin["username"]
            return redirect(url_for("dashboard"))
        flash("Galat username ya password", "error")

    return render_template("login.html")

@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
