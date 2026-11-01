from flask import Blueprint, render_template, request, redirect, url_for, flash
from modules.auth import login_required
from database import create_event, get_events, delete_event

events_bp = Blueprint("events", __name__, url_prefix="/events")

@events_bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    if request.method == "POST":
        data = request.form.to_dict()
        if data.get("title") and data.get("event_date"):
            create_event(data)
            flash("Event successfully add ho gaya!", "success")
        else:
            flash("Title aur Date zaroori hai", "error")
        return redirect(url_for("events.index"))

    all_events = get_events()
    return render_template("events/index.html", events=all_events)

@events_bp.route("/delete/<int:event_id>", methods=["POST"])
@login_required
def delete(event_id):
    delete_event(event_id)
    flash("Event delete ho gaya!", "success")
    return redirect(url_for("events.index"))
