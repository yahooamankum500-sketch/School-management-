from flask import Blueprint, render_template, request, redirect, url_for, flash
from modules.auth import login_required
from database import get_settings, update_settings

settings_bp = Blueprint("settings", __name__, url_prefix="/settings")

@settings_bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    if request.method == "POST":
        data = request.form.to_dict()
        if data.get("school_name"):
            update_settings(data)
            flash("Settings successfully update ho gayi!", "success")
        else:
            flash("School name zaroori hai", "error")
        return redirect(url_for("settings.index"))
        
    current_settings = get_settings()
    return render_template("settings/index.html", settings=current_settings)
