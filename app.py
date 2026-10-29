import os
from flask import Flask, render_template
from flask_session import Session
from config import Config
from modules.auth import auth_bp, login_required

app = Flask(__name__)
app.config.from_object(Config)
Session(app)

# Register blueprints
app.register_blueprint(auth_bp)

# ---------- Public routes ----------
@app.route("/")
def home():
    return render_template("home.html")

@app.route("/health")
def health():
    return {"status": "ok", "app": "School Management"}

# ---------- Protected routes ----------
@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
