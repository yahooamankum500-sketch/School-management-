import os
from flask import Flask, render_template, redirect, url_for, session, request
from flask_session import Session
from config import Config

# Supabase और Config Validation
from supabase_client import init_supabase

# Modules Imports
from modules.auth import auth_bp, login_required
from modules.students import students_bp
from modules.fees import fees_bp
from modules.attendance import attendance_bp
from modules.exams import exams_bp
from modules.notices import notices_bp
from modules.parent import parent_bp
from modules.teacher import teacher_bp

# 1. Config Validate (SECRET_KEY चेक करने के लिए)
Config.validate()

app = Flask(__name__)
app.config.from_object(Config)

# Flask-Session के लिए SESSION_TYPE सेट करना जरूरी है
app.config['SESSION_TYPE'] = 'filesystem' # अगर आप Redis यूज़ कर रहे हैं तो 'redis' करें
Session(app)

# 2. Initialize Supabase
init_supabase()

# Register Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(students_bp)
app.register_blueprint(fees_bp)
app.register_blueprint(attendance_bp)
app.register_blueprint(exams_bp)
app.register_blueprint(notices_bp)
app.register_blueprint(parent_bp)
app.register_blueprint(teacher_bp)

# ============================================================
# ROOT ROUTE (यह 404 एरर खत्म करेगा)
# ============================================================
@app.route("/")
def index():
    # यहाँ हम मुख्य पेज को डैशबोर्ड पर रीडायरेक्ट कर रहे हैं
    # अगर आपका लॉगिन पेज है, तो url_for('auth.login') कर सकते हैं
    return redirect(url_for('dashboard'))

# ============================================================
# DIRECT ROUTES
# ============================================================
@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")

@app.route("/setup-teacher")
def setup_teacher():
    try:
        from database import create_teacher_account
        # ध्यान दें: यह फंक्शन database.py में होना चाहिए
        create_teacher_account("Test Teacher", "9999999999", "teacher123", "5", "A")
        return "✅ Teacher Account ban gaya!<br>Phone: 9999999999<br>Pass: teacher123<br>Class: 5A"
    except Exception as e:
        # यहाँ Syntax Error था, जिसे ठीक कर दिया गया है
        return f"Error: {e}"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
