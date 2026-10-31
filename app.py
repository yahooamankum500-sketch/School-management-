import os
from flask import Flask, render_template, redirect, url_for, session, request
from flask_session import Session
from config import Config

# Modules Imports
from modules.auth import auth_bp, login_required
from modules.students import students_bp
from modules.fees import fees_bp
from modules.attendance import attendance_bp
app = Flask(__name__)
app.config.from_object(Config)
Session(app)

# Register Blueprints (Add naye modules yahan aage aayenge)
app.register_blueprint(auth_bp)
app.register_blueprint(students_bp)
app.register_blueprint(fees_bp)
app.register_blueprint(attendance_bp)
# ============================================================
# DIRECT ROUTES
# ============================================================
@app.route("/")
def home():
    return redirect(url_for("auth.login"))

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
