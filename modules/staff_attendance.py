from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from modules.auth import login_required
from database import (
    mark_staff_attendance, get_staff_attendance_for_date,
    apply_leave, get_leave_requests, update_leave_status, get_staff_list
)

staff_att_bp = Blueprint("staff_attendance", __name__, url_prefix="/staff-attendance")

@staff_att_bp.route("/", methods=["GET", "POST"])
@login_required
def attendance():
    date_str = request.args.get("date") or datetime.now().strftime("%Y-%m-%d")

    if request.method == "POST":
        for key, value in request.form.items():
            if key.startswith("mark_"):
                staff_id = int(key.split("_")[1])
                mark_staff_attendance(staff_id, date_str, value)
        flash("Staff attendance successfully save ho gayi!", "success")
        return redirect(url_for("staff_attendance.attendance", date=date_str))

    staff_data = get_staff_attendance_for_date(date_str)
    return render_template("staff_attendance/index.html", staff=staff_data, date_str=date_str)

@staff_att_bp.route("/leaves")
@login_required
def leaves():
    requests = get_leave_requests()
    return render_template("staff_attendance/leaves.html", requests=requests)

@staff_att_bp.route("/leaves/<int:leave_id>/<status>", methods=["POST"])
@login_required
def update_leave(leave_id, status):
    if status in ["approved", "rejected"]:
        update_leave_status(leave_id, status)
        flash(f"Leave {status} ho gayi!", "success")
    return redirect(url_for("staff_attendance.leaves"))
