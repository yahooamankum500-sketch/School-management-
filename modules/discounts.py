from flask import Blueprint, render_template, request, redirect, url_for, flash
from modules.auth import login_required
from database import (
    add_discount, get_student_discounts, delete_discount,
    calculate_student_fee, get_students, get_student
)

discounts_bp = Blueprint("discounts", __name__, url_prefix="/discounts")

@discounts_bp.route("/", methods=["GET"])
@login_required
def index():
    # List of students jinke paas discount hai
    students = get_students()
    return render_template("discounts/index.html", students=students)

@discounts_bp.route("/student/<int:student_id>", methods=["GET", "POST"])
@login_required
def manage(student_id):
    student = get_student(student_id)
    if not student:
        flash("Student nahi mila", "error")
        return redirect(url_for("discounts.index"))

    if request.method == "POST":
        data = request.form.to_dict()
        if data.get("discount_name") and data.get("discount_value"):
            add_discount(
                student_id, 
                data.get("discount_name"), 
                data.get("discount_type", "fixed"), 
                data.get("discount_value")
            )
            flash("Discount successfully apply ho gaya!", "success")
        else:
            flash("Saari fields bharna zaroori hai", "error")
        return redirect(url_for("discounts.manage", student_id=student_id))

    discounts = get_student_discounts(student_id)
    fee_details = calculate_student_fee(student_id, student["class_name"])
    
    return render_template("discounts/manage.html", 
                           student=student, 
                           discounts=discounts, 
                           fee=fee_details)

@discounts_bp.route("/delete/<int:discount_id>", methods=["POST"])
@login_required
def delete(discount_id):
    student_id = request.form.get("student_id")
    delete_discount(discount_id)
    flash("Discount hata diya gaya!", "success")
    return redirect(url_for("discounts.manage", student_id=student_id))
