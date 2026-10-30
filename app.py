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
@app.route("/setup-admin-xyz")
def setup_admin_xyz():
    try:
        from database import create_admin, get_admin_by_username
        
        if get_admin_by_username("admin"):
            return "Admin pehle se bana hua hai! Ab is route ko delete kar dena."
        
        create_admin("admin", "admin123", "Principal")
        return "✅ Admin successfully ban gaya!<br>Username: admin<br>Password: admin123"
    
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        return f"""
        <h2>❌ Error Aaya:</h2>
        <p style="color:red; font-weight:bold;">{str(e)}</p>
        <h3>Full Details (Screenshot bhejna):</h3>
        <pre style="background:#f4f4f4; padding:10px;">{error_details}</pre>
        """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
