from flask import Blueprint, Response
from modules.auth import login_required
from database import get_full_backup

backup_bp = Blueprint("backup", __name__, url_prefix="/backup")

@backup_bp.route("/download")
@login_required
def download():
    data = get_full_backup()
    return Response(
        data,
        mimetype="application/json",
        headers={"Content-Disposition": "attachment; filename=school_backup.json"}
    )
