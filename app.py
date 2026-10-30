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
    # ============================================================
# TEMPORARY ROUTE: First Admin Setup (No Shell Needed)
# ============================================================
@app.route("/setup-admin-xyz")
def setup_admin_xyz():
    from database import create_admin, get_admin_by_username
    
    # Check karo ki admin pehle se toh nahi hai
    if get_admin_by_username("admin"):
        return "Admin pehle se bana hua hai! Ab is route ko delete kar dena."
    
    try:
        # Naya admin banao
        create_admin("admin", "admin123", "Principal")
        return "✅ Admin successfully ban gaya!<br>Username: admin<br>Password: admin123<br><br><b>Ab is route ko app.py se hata dena!</b>"
    except Exception as e:
        return f"❌ Error: {str(e)}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
