from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from modules.auth import login_required
from database import (
    create_exam, get_exams, get_exam, delete_exam,
    save_exam_marks, get_exam_marks, get_students, get_classes_list
)

exams_bp = Blueprint("exams", __name__, url_prefix="/exams")

@exams_bp.route("/")
@login_required
def index():
    selected_class = request.args.get("class_name", "").strip()
    exams = get_exams(class_name=selected_class or None)
    classes = get_classes_list()
    return render_template("exams/index.html", exams=exams, classes=classes, selected_class=selected_class)

@exams_bp.route("/add", methods=["GET", "POST"])
@login_required
def add():
    if request.method == "POST":
        data = request.form.to_dict()
        if not data.get("name") or not data.get("class_name"):
            flash("Exam Name aur Class zaroori hai", "error")
            return redirect(url_for("exams.add"))
            
        create_exam(data)
        flash("Exam successfully create ho gaya!", "success")
        return redirect(url_for("exams.index"))
        
    classes = get_classes_list()
    return render_template("exams/form.html", classes=classes)

@exams_bp.route("/<int:exam_id>/marks", methods=["GET", "POST"])
@login_required
def marks_entry(exam_id):
    exam = get_exam(exam_id)
    if not exam:
        flash("Exam nahi mila", "error")
        return redirect(url_for("exams.index"))

    if request.method == "POST":
        for key, val in request.form.items():
            if key.startswith("mark_") and val.strip() != "":
                student_id = int(key.split("_")[1])
                save_exam_marks(exam_id, student_id, val)
        flash("Marks successfully save ho gaye!", "success")
        return redirect(url_for("exams.marks_entry", exam_id=exam_id))

    # Class ke students nikaalo
    students = get_students(class_name=exam['class_name'])
    
    # Existing marks map nikaalo
    marks_map = get_exam_marks(exam_id)

    return render_template("exams/marks_entry.html", exam=exam, students=students, marks_map=marks_map)

@exams_bp.route("/<int:exam_id>/delete", methods=["POST"])
@login_required
def delete(exam_id):
    delete_exam(exam_id)
    flash("Exam delete ho gaya!", "success")
    return redirect(url_for("exams.index"))
