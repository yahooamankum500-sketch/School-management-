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
# TEMPORARY ROUTE: First Admin Setup (Fixed)
# ============================================================
@app.route("/setup-admin-xyz")
def setup_admin_xyz():
    try:
        from database import db_select, db_insert
        from werkzeug.security import generate_password_hash
        
        # 1. Check karo ki admin pehle se bana hai ya nahi
        rows = db_select("admins", {"username": "admin"})
        if rows:
            return "Admin pehle se bana hua hai! Ab is route ko delete kar dena."
        
        # 2. Direct admin insert karo
        db_insert("admins", {
            "username": "admin",
            "password_hash": generate_password_hash("admin123"),
            "full_name": "Principal",
            "role": "super_admin",
            "is_active": True
        })
        
        return "✅ Admin successfully ban gaya!<br>Username: admin<br>Password: admin123<br><br><b>Ab is route ko app.py se hata dena!</b>"
    
    except Exception as e:
        import traceback
        return f"""
        <h2>❌ Error Aaya:</h2>
        <p style="color:red; font-weight:bold;">{str(e)}</p>
        <h3>Full Details:</h3>
        <pre style="background:#f4f4f4; padding:10px;">{traceback.format_exc()}</pre>
        """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
