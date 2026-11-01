from flask import Blueprint, render_template
from modules.auth import login_required
from database import get_audit_logs

audit_bp = Blueprint("audit", __name__, url_prefix="/audit-logs")

@audit_bp.route("/")
@login_required
def index():
    logs = get_audit_logs()
    return render_template("audit/index.html", logs=logs)
