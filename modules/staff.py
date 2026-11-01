from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from modules.auth import login_required
from database import (
    create_staff, get_staff_list, 
    generate_monthly_salary, get_salary_records, mark_salary_paid
)

staff_bp = Blueprint("staff", __name__, url_prefix="/staff")

@staff_bp.route("/")
@login_required
def index():
    staff = get_staff_list()
    return render_template("staff/index.html", staff=staff)

@staff_bp.route("/add", methods=["POST"])
@login_required
def add():
    data = request.form.to_dict()
    if data.get("name") and data.get("role"):
        create_staff(data)
        flash("Staff member successfully add ho gaya!", "success")
    else:
        flash("Name aur Role zaroori hai", "error")
    return redirect(url_for("staff.index"))

@staff_bp.route("/salary", methods=["GET", "POST"])
@login_required
def salary():
    current_month = datetime.now().strftime("%Y-%m")
    selected_month = request.args.get("month") or current_month

    if request.method == "POST":
        # Generate Salary button dabaya gaya
        month = request.form.get("month")
        created = generate_monthly_salary(month)
        if created > 0:
            flash(f"{created} staff members ki salary generate ho gayi!", "success")
        else:
            flash("Is month ki salary pehle hi generate ho chuki hai.", "info")
        return redirect(url_for("staff.salary", month=month))

    records = get_salary_records(selected_month)
    
    # Total paid aur pending calculate karo
    total_paid = sum(r["amount"] for r in records if r["status"] == "paid")
    total_pending = sum(r["amount"] for r in records if r["status"] == "pending")

    return render_template("staff/salary.html", 
                           records=records, 
                           selected_month=selected_month,
                           total_paid=total_paid,
                           total_pending=total_pending)

@staff_bp.route("/salary/pay/<int:record_id>", methods=["POST"])
@login_required
def pay_salary(record_id):
    month = request.form.get("month")
    try:
        mark_salary_paid(record_id)
        flash("Salary successfully paid mark ho gayi!", "success")
    except Exception as e:
        flash(str(e), "error")
    return redirect(url_for("staff.salary", month=month))
