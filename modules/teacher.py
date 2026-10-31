from functools import wraps
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from database import (
    verify_teacher, get_teacher_students, 
    mark_attendance, get_attendance_for_date, 
    save_exam_marks, get_exam_marks, get_exams
)

teacher_bp = Blueprint("teacher", __name__, url_prefix="/teacher")

def teacher_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "teacher_id" not in session:
            return redirect(url_for("teacher.login"))
        return f(*args, **kwargs)
    return wrapper

@teacher_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")
        
        teacher = verify_teacher(phone, password)
        if teacher:
            session["teacher_id"] = teacher["id"]
            session["teacher_name"] = teacher["name"]
            session["teacher_class"] = teacher["assigned_class"]
            session["teacher_section"] = teacher["assigned_section"] or ""
            return redirect(url_for("teacher.dashboard"))
        flash("Galat phone number ya password", "error")
        
    return render_template("teacher/login.html")

@teacher_bp.route("/logout")
def logout():
    for key in ["teacher_id", "teacher_name", "teacher_class", "teacher_section"]:
        session.pop(key, None)
    return redirect(url_for("teacher.login"))

@teacher_bp.route("/dashboard")
@teacher_required
def dashboard():
    students = get_teacher_students(session["teacher_class"], session["teacher_section"])
    return render_template("teacher/dashboard.html", students=students)

@teacher_bp.route("/attendance", methods=["GET", "POST"])
@teacher_required
def attendance():
    class_name = session["teacher_class"]
    section = session["teacher_section"]
    date_str = request.args.get("date") or datetime.now().strftime("%Y-%m-%d")

    if request.method == "POST":
        for key, value in request.form.items():
            if key.startswith("mark_"):
                student_id = int(key.split("_")[1])
                mark_attendance(student_id, date_str, value, None)
        flash("Attendance successfully save ho gayi!", "success")
        return redirect(url_for("teacher.attendance", date=date_str))

    # Fetch students with existing attendance for selected date
    students_data = get_attendance_for_date(class_name, date_str)
    return render_template("teacher/attendance.html", students=students_data, date_str=date_str)

@teacher_bp.route("/marks/<int:exam_id>", methods=["GET", "POST"])
@teacher_required
def marks(exam_id):
    # Get exam details
    exams = get_exams(class_name=session["teacher_class"])
    exam = next((e for e in exams if e["id"] == exam_id), None)
    
    if not exam:
        flash("Exam nahi mila", "error")
        return redirect(url_for("teacher.dashboard"))

    if request.method == "POST":
        for key, val in request.form.items():
            if key.startswith("mark_") and val.strip() != "":
                student_id = int(key.split("_")[1])
                save_exam_marks(exam_id, student_id, val)
        flash("Marks successfully save ho gaye!", "success")
        return redirect(url_for("teacher.marks", exam_id=exam_id))

    students = get_teacher_students(session["teacher_class"], session["teacher_section"])
    marks_map = get_exam_marks(exam_id)

    return render_template("teacher/marks.html", exam=exam, students=students, marks_map=marks_map)
