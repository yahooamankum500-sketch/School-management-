from flask import Blueprint, render_template, request, redirect, url_for, flash
from modules.auth import login_required
from database import create_student, get_students

students_bp = Blueprint("students", __name__, url_prefix="/students")

@students_bp.route("/")
@login_required
def index():
    students_list = get_students()
    return render_template("students/list.html", students=students_list)

@students_bp.route("/add", methods=["GET", "POST"])
@login_required
def add():
    if request.method == "POST":
        data = request.form.to_dict()
        if not data.get("name"):
            flash("Name zaroori hai", "error")
            return redirect(url_for("students.add"))
        
        create_student(data)
        flash("Student add ho gaya!", "success")
        return redirect(url_for("students.index"))
        
    return render_template("students/form.html")
