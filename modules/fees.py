from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from modules.auth import login_required
from database import (
    create_fee_structure, get_fee_structures, 
    create_fee_payment, get_recent_payments, 
    get_students, get_classes_list
)

fees_bp = Blueprint("fees", __name__, url_prefix="/fees")

@fees_bp.route("/")
@login_required
def index():
    payments = get_recent_payments()
    return render_template("fees/index.html", payments=payments)

@fees_bp.route("/structure", methods=["GET", "POST"])
@login_required
def structure():
    if request.method == "POST":
        class_name = request.form.get("class_name")
        fee_type = request.form.get("fee_type")
        amount = request.form.get("amount")
        frequency = request.form.get("frequency", "monthly")
        
        if class_name and fee_type and amount:
            create_fee_structure(class_name, fee_type, amount, frequency)
            flash("Fee Structure add ho gaya!", "success")
            return redirect(url_for("fees.structure"))
        else:
            flash("Saari fields bharna zaroori hai", "error")
            
    structures = get_fee_structures()
    classes = get_classes_list() # Jo list students module mein banayi thi
    return render_template("fees/structure.html", structures=structures, classes=classes)

@fees_bp.route("/collect", methods=["GET", "POST"])
@login_required
def collect():
    if request.method == "POST":
        student_id = request.form.get("student_id")
        fee_type = request.form.get("fee_type")
        amount = request.form.get("amount")
        month = request.form.get("month") or datetime.now().strftime("%Y-%m")
        mode = request.form.get("mode", "cash")
        
        if student_id and fee_type and amount:
            create_fee_payment(
                student_id, fee_type, amount, 
                month, mode, "", session["admin_id"]
            )
            flash("Payment record ho gayi!", "success")
            return redirect(url_for("fees.index"))
        else:
            flash("Student, Type aur Amount zaroori hai", "error")
            
    # Students fetch karo (dictionary format mein)
    students = get_students()
    return render_template("fees/collect.html", students=students, current_month=datetime.now().strftime("%Y-%m"))
