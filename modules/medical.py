from flask import Blueprint, render_template, request, redirect, url_for, flash
from modules.auth import login_required
from database import get_medical_record, save_medical_record, get_students, get_student

medical_bp = Blueprint("medical", __name__, url_prefix="/medical")

@medical_bp.route("/")
@login_required
def index():
    # Admin ko students ki list dikhao taaki wo select kar sake
    students = get_students()
    return render_template("medical/index.html", students=students)

@medical_bp.route("/<int:student_id>", methods=["GET", "POST"])
@login_required
def manage_record(student_id):
    student = get_student(student_id)
    if not student:
        flash("Student nahi mila", "error")
        return redirect(url_for("medical.index"))

    if request.method == "POST":
        data = request.form.to_dict()
        save_medical_record(student_id, data)
        flash("Medical record save ho gaya!", "success")
        return redirect(url_for("medical.manage_record", student_id=student_id))

    record = get_medical_record(student_id)
    return render_template("medical/record.html", student=student, record=record)
