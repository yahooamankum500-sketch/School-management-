import csv
import io
from datetime import datetime
from flask import Blueprint, render_template, request, Response
from modules.auth import login_required
from database import get_fee_defaulters_data, get_fee_collection_data

reports_bp = Blueprint("reports", __name__, url_prefix="/reports")

@reports_bp.route("/")
@login_required
def index():
    return render_template("reports/index.html")

# ================= DEFAULTEERS REPORT =================
@reports_bp.route("/defaulters")
@login_required
def defaulters():
    month = request.args.get("month") or datetime.now().strftime("%Y-%m")
    data = get_fee_defaulters_data(month)
    
    total_pending = sum(d["pending"] for d in data)
    return render_template("reports/defaulters.html", data=data, month=month, total_pending=total_pending)

@reports_bp.route("/defaulters/download")
@login_required
def download_defaulters():
    month = request.args.get("month") or datetime.now().strftime("%Y-%m")
    data = get_fee_defaulters_data(month)
    
    # CSV banane ka logic
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Student Name", "Class", "Section", "Parent Phone", "Total Fee", "Paid", "Pending"])
    
    for d in data:
        writer.writerow([d["name"], d["class_name"], d["section"], d["parent_phone"], d["total_fee"], d["paid"], d["pending"]])
        
    output.seek(0)
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename=defaulters_{month}.csv"}
    )

# ================= FEE COLLECTION REPORT =================
@reports_bp.route("/fees")
@login_required
def fees():
    month = request.args.get("month") or datetime.now().strftime("%Y-%m")
    data = get_fee_collection_data(month)
    
    total_collected = sum(float(d["amount"]) for d in data)
    return render_template("reports/fees.html", data=data, month=month, total_collected=total_collected)

@reports_bp.route("/fees/download")
@login_required
def download_fees():
    month = request.args.get("month") or datetime.now().strftime("%Y-%m")
    data = get_fee_collection_data(month)
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Receipt No", "Date", "Student Name", "Class", "Fee Type", "Amount", "Mode"])
    
    for d in data:
        writer.writerow([d["receipt_no"], d["date"], d["student_name"], d["class_name"], d["fee_type"], d["amount"], d["mode"]])
        
    output.seek(0)
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename=fee_collection_{month}.csv"}
  )
