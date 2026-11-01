from flask import Blueprint, render_template, request, redirect, url_for, flash
from modules.auth import login_required
from database import create_homework, get_homework, delete_homework, get_classes_list

homework_bp = Blueprint("homework", __name__, url_prefix="/homework")

@homework_bp.route("/")
@login_required
def index():
    selected_class = request.args.get("class_name", "").strip()
    all_homework = get_homework(selected_class or None)
    classes = get_classes_list()
    return render_template("homework/index.html", 
                           homework=all_homework, 
                           classes=classes, 
                           selected_class=selected_class)

@homework_bp.route("/add", methods=["GET", "POST"])
@login_required
def add():
    if request.method == "POST":
        data = request.form.to_dict()
        if data.get("class_name") and data.get("subject") and data.get("title"):
            create_homework(data)
            flash("Homework successfully post ho gaya!", "success")
            return redirect(url_for("homework.index"))
        else:
            flash("Class, Subject, aur Title zaroori hai", "error")

    classes = get_classes_list()
    return render_template("homework/form.html", classes=classes)

@homework_bp.route("/<int:homework_id>/delete", methods=["POST"])
@login_required
def delete(homework_id):
    delete_homework(homework_id)
    flash("Homework delete ho gaya!", "success")
    return redirect(url_for("homework.index"))
