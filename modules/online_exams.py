from flask import Blueprint, render_template, request, redirect, url_for, flash
from modules.auth import login_required
from database import (
    create_online_exam, get_online_exams, get_online_exam, delete_online_exam,
    toggle_exam_publish, add_exam_question, get_exam_questions, delete_exam_question,
    get_classes_list
)

online_exams_bp = Blueprint("online_exams", __name__, url_prefix="/online-exams")

@online_exams_bp.route("/")
@login_required
def index():
    exams = get_online_exams()
    return render_template("online_exams/index.html", exams=exams)

@online_exams_bp.route("/add", methods=["GET", "POST"])
@login_required
def add():
    if request.method == "POST":
        data = request.form.to_dict()
        if data.get("title") and data.get("class_name"):
            create_online_exam(data)
            flash("Exam successfully create ho gaya!", "success")
            return redirect(url_for("online_exams.index"))
        else:
            flash("Title aur Class zaroori hai", "error")
            
    classes = get_classes_list()
    return render_template("online_exams/form.html", classes=classes)

@online_exams_bp.route("/<int:exam_id>")
@login_required
def manage(exam_id):
    exam = get_online_exam(exam_id)
    if not exam:
        flash("Exam nahi mila", "error")
        return redirect(url_for("online_exams.index"))
        
    questions = get_exam_questions(exam_id)
    return render_template("online_exams/manage.html", exam=exam, questions=questions)

@online_exams_bp.route("/<int:exam_id>/add-question", methods=["POST"])
@login_required
def add_q(exam_id):
    data = request.form.to_dict()
    if data.get("question_text") and data.get("correct_option"):
        add_exam_question(exam_id, data)
        flash("Question add ho gaya!", "success")
    else:
        flash("Question aur Correct Option zaroori hai", "error")
    return redirect(url_for("online_exams.manage", exam_id=exam_id))

@online_exams_bp.route("/<int:exam_id>/delete-question/<int:q_id>", methods=["POST"])
@login_required
def remove_q(exam_id, q_id):
    delete_exam_question(q_id, exam_id)
    flash("Question delete ho gaya!", "success")
    return redirect(url_for("online_exams.manage", exam_id=exam_id))

@online_exams_bp.route("/<int:exam_id>/toggle", methods=["POST"])
@login_required
def toggle(exam_id):
    exam = get_online_exam(exam_id)
    new_status = not exam.get("is_published", False)
    toggle_exam_publish(exam_id, new_status)
    flash(f"Exam {'Publish' if new_status else 'Unpublish'} ho gaya!", "success")
    return redirect(url_for("online_exams.manage", exam_id=exam_id))

@online_exams_bp.route("/<int:exam_id>/delete", methods=["POST"])
@login_required
def delete(exam_id):
    delete_online_exam(exam_id)
    flash("Exam delete ho gaya!", "success")
    return redirect(url_for("online_exams.index"))
