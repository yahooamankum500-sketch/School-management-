import os
from flask import Flask, render_template, redirect, url_for, session, request
from flask_session import Session
from config import Config
from modules.auth import auth_bp, login_required
from modules.students import students_bp
from modules.fees import fees_bp
from modules.attendance import attendance_bp
from modules.exams import exams_bp
from modules.notices import notices_bp
from modules.parent import parent_bp
from modules.teacher import teacher_bp
from modules.library import library_bp
from modules.transport import transport_bp
from modules.hostel import hostel_bp
from modules.staff import staff_bp
from modules.expenses import expenses_bp

app = Flask(__name__)
app.config.from_object(Config)
Session(app)

# Register Auth Blueprint
app.register_blueprint(auth_bp)
app.register_blueprint(students_bp)
app.register_blueprint(fees_bp)
app.register_blueprint(attendance_bp)
app.register_blueprint(exams_bp)
app.register_blueprint(notices_bp)
app.register_blueprint(parent_bp)
app.register_blueprint(teacher_bp)
app.register_blueprint(library_bp)
app.register_blueprint(transport_bp)
app.register_blueprint(hostel_bp)
app.register_blueprint(staff_bp)
app.register_blueprint(expenses_bp)

@app.route("/")
def home():
    return redirect(url_for("auth.login"))
    from database import get_dashboard_stats

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
