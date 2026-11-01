from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from modules.auth import login_required
from database import create_expense, get_expenses, get_pnl

expenses_bp = Blueprint("expenses", __name__, url_prefix="/expenses")

@expenses_bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    current_month = datetime.now().strftime("%Y-%m")
    selected_month = request.args.get("month") or current_month

    if request.method == "POST":
        data = request.form.to_dict()
        if data.get("category") and data.get("amount"):
            create_expense(data)
            flash("Expense successfully record ho gaya!", "success")
            return redirect(url_for("expenses.index", month=selected_month))
        else:
            flash("Category aur Amount zaroori hai", "error")

    expenses = get_expenses(selected_month)
    total_expense = sum(float(e.get("amount") or 0) for e in expenses)
    
    return render_template("expenses/index.html", 
                           expenses=expenses, 
                           selected_month=selected_month,
                           total_expense=total_expense,
                           today=datetime.now().strftime("%Y-%m-%d"))

@expenses_bp.route("/pnl")
@login_required
def pnl():
    current_month = datetime.now().strftime("%Y-%m")
    selected_month = request.args.get("month") or current_month
    
    data = get_pnl(selected_month)
    
    return render_template("expenses/pnl.html", p=data)
