from flask import Blueprint, render_template, request, redirect, url_for, flash
from modules.auth import login_required
from database import (
    create_notice, get_notices, delete_notice,
    create_event, get_events, delete_event, get_classes_list
)

notices_bp = Blueprint("notices", __name__, url_prefix="/notices")

@notices_bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    if request.method == "POST":
        if "add_notice" in request.form:
            data = {
                "title": request.form.get("title"),
                "content": request.form.get("content"),
                "priority": request.form.get("priority"),
                "target_class": request.form.get("target_class")
            }
            if data["title"] and data["content"]:
                create_notice(data)
                flash("Notice successfully publish ho gaya!", "success")
            else:
                flash("Title aur Content zaroori hai", "error")
                
        elif "add_event" in request.form:
            data = {
                "title": request.form.get("event_title"),
                "description": request.form.get("event_desc"),
                "event_date": request.form.get("event_date"),
                "venue": request.form.get("event_venue")
            }
            if data["title"] and data["event_date"]:
                create_event(data)
                flash("Event successfully add ho gaya!", "success")
            else:
                flash("Event Title aur Date zaroori hai", "error")
                
        return redirect(url_for("notices.index"))

    all_notices = get_notices()
    all_events = get_events()
    classes = get_classes_list()
    
    return render_template("notices/index.html", 
                           notices=all_notices, 
                           events=all_events, 
                           classes=classes)

@notices_bp.route("/notice/delete/<int:notice_id>", methods=["POST"])
@login_required
def delete_notice_route(notice_id):
    delete_notice(notice_id)
    flash("Notice delete ho gaya", "success")
    return redirect(url_for("notices.index"))

@notices_bp.route("/event/delete/<int:event_id>", methods=["POST"])
@login_required
def delete_event_route(event_id):
    delete_event(event_id)
    flash("Event delete ho gaya", "success")
    return redirect(url_for("notices.index"))
