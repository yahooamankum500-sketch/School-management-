from flask import Blueprint, render_template, request, redirect, url_for, flash
from modules.auth import login_required
from database import (
    log_visitor_in, log_visitor_out, 
    get_active_visitors, get_visitor_history
)

visitors_bp = Blueprint("visitors", __name__, url_prefix="/visitors")

@visitors_bp.route("/")
@login_required
def index():
    active = get_active_visitors()
    history = get_visitor_history()
    return render_template("visitors/index.html", active=active, history=history)

@visitors_bp.route("/check-in", methods=["POST"])
@login_required
def check_in():
    data = request.form.to_dict()
    if data.get("name") and data.get("purpose"):
        log_visitor_in(
            data.get("name"), 
            data.get("phone"), 
            data.get("purpose"), 
            data.get("meeting_with")
        )
        flash("Visitor checked in successfully!", "success")
    else:
        flash("Name aur Purpose zaroori hai", "error")
    return redirect(url_for("visitors.index"))

@visitors_bp.route("/check-out/<int:visitor_id>", methods=["POST"])
@login_required
def check_out(visitor_id):
    log_visitor_out(visitor_id)
    flash("Visitor checked out!", "success")
    return redirect(url_for("visitors.index"))
