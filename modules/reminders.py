from datetime import datetime
from urllib.parse import quote
from flask import Blueprint, render_template, request
from modules.auth import login_required
from database import get_fee_defaulters_data

reminders_bp = Blueprint("reminders", __name__, url_prefix="/reminders")

@reminders_bp.route("/")
@login_required
def index():
    month = request.args.get("month") or datetime.now().strftime("%Y-%m")
    defaulters = get_fee_defaulters_data(month)
    
    # Har defaulter ke liye WhatsApp link generate karo
    for d in defaulters:
        # Phone number saaf karo (spaces aur dash hatao)
        phone = str(d.get("parent_phone") or "").strip().replace(" ", "").replace("-", "")
        
        # Agar 10 digit ka number hai, toh aage 91 laga do (India code)
        if len(phone) == 10:
            phone = "91" + phone
            
        d["clean_phone"] = phone
        
        # Message tayar karo
        msg = (
            f"Namaste, {d['name']} (Class {d['class_name']}) ke parent.\n"
            f"School fees for {month} is pending: ₹{d['pending']:.0f}.\n"
            f"Kindly clear the dues at your earliest.\n"
            f"Thank you. - School ERP"
        )
        
        # WhatsApp URL encode karke link banao
        d["wa_link"] = f"https://wa.me/{phone}?text={quote(msg)}"

    return render_template("reminders/index.html", defaulters=defaulters, month=month)
