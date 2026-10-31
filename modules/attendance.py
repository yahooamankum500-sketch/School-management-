from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from modules.auth import login_required
from database import get_attendance_for_date, mark_attendance, get_classes_list

attendance_bp = Blueprint("attendance", __name__, url_prefix="/attendance")

@attendance_bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    classes = get_classes_list()
    selected_class = request.args.get("class_name")
    date_str = request.args.get("date") or datetime.now().strftime("%Y-%m-%d")
    
    # Jab form submit ho (Save Attendance)
    if request.method == "POST":
        selected_class = request.form.get("class_name")
        date_str = request.form.get("date")
        
        for key, value in request.form.items():
            if key.startswith("mark_"):
                student_id = int(key.split("_")[1])
                mark_attendance(student_id, date_str, value, session["admin_id"])
                
        flash("Attendance successfully save ho gayi!", "success")
        return redirect(url_for("attendance.index", class_name=selected_class, date=date_str))

    students = []
    if selected_class:
        students = get_attendance_for_date(selected_class, date_str)

    return render_template("attendance/index.html", 
                           classes=classes, 
                           students=students, 
                           selected_class=selected_class, 
                           date_str=date_str)
