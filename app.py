import os
from flask import Flask, render_template, redirect, url_for, session, request
from flask_session import Session
from config import Config
from modules.auth import auth_bp, login_required

app = Flask(__name__)
app.config.from_object(Config)
Session(app)

# Register Auth Blueprint
app.register_blueprint(auth_bp)

@app.route("/")
def home():
    return redirect(url_for("auth.login"))

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
