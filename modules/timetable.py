from flask import Blueprint, render_template, request, redirect, url_for, flash
from modules.auth import login_required
from database import (
    create_timetable_entry, get_timetable, 
    delete_timetable_entry, get_classes_list
)

timetable_bp = Blueprint("timetable", __name__, url_prefix="/timetable")

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
PERIODS = [1, 2, 3, 4, 5, 6, 7, 8]

@timetable_bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    classes = get_classes_list()
    selected_class = request.args.get("class_name", "")
    
    if request.method == "POST":
        data = request.form.to_dict()
        if data.get("class_name") and data.get("subject"):
            try:
                create_timetable_entry(data)
                flash("Period successfully add ho gaya!", "success")
            except Exception:
                flash("Is period mein pehle se koi subject hai.", "error")
        else:
            flash("Saari fields bharna zaroori hai", "error")
        return redirect(url_for("timetable.index", class_name=data.get("class_name")))

    entries = []
    if selected_class:
        entries = get_timetable(selected_class)

    # Grid banane ke liye data organize karo (Day -> Period -> Subject)
    grid = {}
    for d in DAYS:
        grid[d] = {}
        for p in PERIODS:
            grid[d][p] = next((e for e in entries if e["day_of_week"] == d and e["period_number"] == p), None)

    return render_template("timetable/index.html", 
                           classes=classes, 
                           selected_class=selected_class,
                           days=DAYS, periods=PERIODS, grid=grid)

@timetable_bp.route("/delete/<int:entry_id>", methods=["POST"])
@login_required
def delete_entry(entry_id):
    class_name = request.form.get("class_name")
    delete_timetable_entry(entry_id)
    flash("Period delete ho gaya!", "success")
    return redirect(url_for("timetable.index", class_name=class_name))
