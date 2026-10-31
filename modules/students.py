from flask import Blueprint, render_template, request, redirect, url_for, flash
from modules.auth import login_required
from database import create_student, get_students, get_student, update_student, delete_student

students_bp = Blueprint("students", __name__, url_prefix="/students")

@students_bp.route("/")
@login_required
def index():
    search = request.args.get("q", "").strip()
    students = get_students(search=search or None)
    return render_template("students/list.html", students=students, search=search)

@students_bp.route("/add", methods=["GET", "POST"])
@login_required
def add():
    if request.method == "POST":
        data = request.form.to_dict()
        if not data.get("name") or not data.get("class_name"):
            flash("Name aur Class zaroori hai", "error")
            return redirect(url_for("students.add"))
        create_student(data)
        flash("Student successfully add ho gaya!", "success")
        return redirect(url_for("students.index"))
    return render_template("students/form.html", student=None)

@students_bp.route("/<int:student_id>/edit", methods=["GET", "POST"])
@login_required
def edit(student_id):
    student = get_student(student_id)
    if not student:
        flash("Student nahi mila", "error")
        return redirect(url_for("students.index"))
        
    if request.method == "POST":
        data = request.form.to_dict()
        update_student(student_id, data)
        flash("Student update ho gaya!", "success")
        return redirect(url_for("students.index"))
        
    return render_template("students/form.html", student=student)

@students_bp.route("/<int:student_id>/delete", methods=["POST"])
@login_required
def delete(student_id):
    delete_student(student_id)
    flash("Student delete ho gaya!", "success")
    return redirect(url_for("students.index"))
