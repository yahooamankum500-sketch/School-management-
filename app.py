import os
from flask import Flask, render_template, redirect, url_for, session, request, send_from_directory
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
from modules.id_cards import id_cards_bp
from modules.timetable import timetable_bp
from modules.discounts import discounts_bp
from modules.staff_attendance import staff_att_bp
from modules.events import events_bp
from modules.reports import reports_bp
from modules.reminders import reminders_bp
from modules.online_exams import online_exams_bp
from modules.visitors import visitors_bp
from modules.backup import backup_bp
from modules.settings import settings_bp
from modules.medical import medical_bp
from modules.audit import audit_bp
from modules.homework import homework_bp
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
app.register_blueprint(id_cards_bp)
app.register_blueprint(timetable_bp)
app.register_blueprint(discounts_bp)
app.register_blueprint(staff_att_bp)
app.register_blueprint(events_bp)
app.register_blueprint(reports_bp)
app.register_blueprint(reminders_bp)
app.register_blueprint(online_exams_bp)
app.register_blueprint(visitors_bp)
app.register_blueprint(backup_bp)
app.register_blueprint(settings_bp)
app.register_blueprint(medical_bp)
app.register_blueprint(audit_bp)
app.register_blueprint(homework_bp)
@app.route("/")
def home():
    return redirect(url_for("auth.login"))

# Upar imports mein add karo
from database import (
    get_dashboard_stats, get_fee_trend, 
    get_attendance_trend, get_class_distribution
)

@app.route("/dashboard")
@login_required
def dashboard():
    stats = get_dashboard_stats()
    fee_trend = get_fee_trend()
    att_trend = get_attendance_trend()
    class_dist = get_class_distribution()
    
    return render_template(
        "dashboard.html", 
        stats=stats, 
        fee_trend=fee_trend, 
        att_trend=att_trend, 
        class_dist=class_dist
    )
    
@app.route('/manifest.json')
def manifest():
    return send_from_directory('static', 'manifest.json')

@app.route('/sw.js')
def service_worker():
    resp = send_from_directory('static', 'sw.js')
    resp.headers['Service-Worker-Allowed'] = '/'
    return resp
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
