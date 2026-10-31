from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from database import (
    create_parent_account, verify_parent, get_children_for_parent,
    get_child_attendance_summary, get_child_pending_fees,
    get_exam_marks, get_exams, get_notices
)

parent_bp = Blueprint("parent", __name__, url_prefix="/parent")

def parent_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "parent_phone" not in session:
            return redirect(url_for("parent.login"))
        return f(*args, **kwargs)
    return wrapper

@parent_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")
        name = request.form.get("name", "").strip()

        if len(password) < 6:
            flash("Password kam se kam 6 characters ka hona chahiye", "error")
        else:
            try:
                create_parent_account(phone, password, name)
                flash("Account ban gaya! Ab login karo.", "success")
                return redirect(url_for("parent.login"))
            except Exception:
                flash("Ye phone number pehle se registered hai.", "error")
                
    return render_template("parent/register.html")

@parent_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")
        
        parent = verify_parent(phone, password)
        if parent:
            session["parent_phone"] = parent["phone"]
            session["parent_name"] = parent["name"] or parent["phone"]
            return redirect(url_for("parent.dashboard"))
        flash("Galat phone number ya password", "error")
        
    return render_template("parent/login.html")

@parent_bp.route("/logout")
def logout():
    session.pop("parent_phone", None)
    session.pop("parent_name", None)
    return redirect(url_for("parent.login"))

@parent_bp.route("/dashboard")
@parent_required
def dashboard():
    phone = session.get("parent_phone")
    children = get_children_for_parent(phone)
    
    if not children:
        flash("Aapke phone number se koi student record nahi mila. School se sampark karein.", "error")
        return render_template("parent/dashboard.html", children=[])
        
    # Har bachche ka data calculate karo
    children_data = []
    for child in children:
        att = get_child_attendance_summary(child["id"])
        pending_fees = get_child_pending_fees(child["id"])
        
        # Recent marks (latest exam)
        exams = get_exams(class_name=child["class_name"], limit=1)
        recent_marks = {}
        if exams:
            exam = exams[0]
            marks_map = get_exam_marks(exam["id"])
            if str(child["id"]) in marks_map:
                recent_marks = {"exam": exam["name"], "marks": marks_map[str(child["id"])]}
                
        child["attendance"] = att
        child["pending_fees"] = pending_fees
        child["recent_marks"] = recent_marks
        children_data.append(child)

    # Notice board bhi dikhao
    notices = get_notices(limit=3)
    
    return render_template("parent/dashboard.html", children=children_data, notices=notices)
