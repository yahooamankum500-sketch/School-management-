from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from database import (
    create_parent_account, verify_parent, get_children_for_parent,
    get_child_attendance_summary, get_child_pending_fees,
    get_exam_marks, get_exams, get_notices
)
from database import (
    # ... purane imports ...
    get_published_exams_for_class, get_exam_attempt, 
    start_exam_attempt, submit_exam_attempt, get_exam_attempt_details,
    get_exam_questions, get_online_exam # Ye pehle se ho sakte hain
)
from database import (
    # ... purane imports ...
    get_homework_for_class
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
    # ============================================================
# ONLINE EXAMS (PARENT PORTAL)
# ============================================================
@parent_bp.route("/online-exams")
@parent_required
def online_exams():
    children = get_children_for_parent(session["parent_phone"])
    if not children:
        flash("Koi student record nahi mila.", "error")
        return redirect(url_for("parent.dashboard"))
        
    child_id = request.args.get("child_id", type=int)
    selected_child = next((c for c in children if c["id"] == child_id), children[0])
    
    # Us child ki class ke published exams
    exams = get_published_exams_for_class(selected_child["class_name"])
    
    # Har exam ke liye check karo ki attempt hua hai ya nahi
    for e in exams:
        attempt = get_exam_attempt(e["id"], selected_child["id"])
        e["attempt"] = attempt
        
    return render_template("parent/online_exams.html", 
                           children=children, 
                           selected_child=selected_child, 
                           exams=exams)

@parent_bp.route("/online-exams/start/<int:exam_id>")
@parent_required
def start_online_exam(exam_id):
    children = get_children_for_parent(session["parent_phone"])
    child_id = request.args.get("child_id", type=int)
    selected_child = next((c for c in children if c["id"] == child_id), children[0])
    
    exam = get_online_exam(exam_id)
    if not exam or exam["class_name"] != selected_child["class_name"]:
        flash("Ye exam aapke bachche ke liye nahi hai.", "error")
        return redirect(url_for("parent.online_exams"))
        
    attempt = get_exam_attempt(exam_id, selected_child["id"])
    
    if attempt and attempt["status"] == "submitted":
        flash("Aap ye exam de chuke hain.", "error")
        return redirect(url_for("parent.online_exams", child_id=selected_child["id"]))
        
    if not attempt:
        start_exam_attempt(exam_id, selected_child["id"])
        
    return redirect(url_for("parent.take_online_exam", exam_id=exam_id, child_id=selected_child["id"]))

@parent_bp.route("/online-exams/take/<int:exam_id>", methods=["GET", "POST"])
@parent_required
def take_online_exam(exam_id):
    children = get_children_for_parent(session["parent_phone"])
    child_id = request.args.get("child_id", type=int)
    selected_child = next((c for c in children if c["id"] == child_id), children[0])
    
    exam = get_online_exam(exam_id)
    attempt = get_exam_attempt(exam_id, selected_child["id"])
    
    if not exam or not attempt or attempt["status"] == "submitted":
        return redirect(url_for("parent.online_exams", child_id=selected_child["id"]))

    if request.method == "POST":
        # Form se answers collect karo (q_id -> option)
        answers = {}
        for key, val in request.form.items():
            if key.startswith("q_"):
                answers[key.split("_")[1]] = val
                
        score = submit_exam_attempt(attempt["id"], exam_id, selected_child["id"], answers)
        flash(f"Exam submit ho gaya! Score: {score}/{exam['total_marks']}", "success")
        return redirect(url_for("parent.online_exams", child_id=selected_child["id"]))

    questions = get_exam_questions(exam_id)
    return render_template("parent/take_exam.html", exam=exam, questions=questions, child=selected_child)

@parent_bp.route("/online-exams/result/<int:attempt_id>")
@parent_required
def exam_result(attempt_id):
    details = get_exam_attempt_details(attempt_id)
    if not details["attempt"]:
        flash("Result nahi mila", "error")
        return redirect(url_for("parent.dashboard"))
        
    return render_template("parent/exam_result.html", 
                           attempt=details["attempt"], 
                           exam=details["exam"], 
                           answers=details["answers"])
    # ============================================================
# HOMEWORK (PARENT VIEW)
# ============================================================
@parent_bp.route("/homework")
@parent_required
def homework():
    children = get_children_for_parent(session["parent_phone"])
    if not children:
        flash("Koi student record nahi mila.", "error")
        return redirect(url_for("parent.dashboard"))
        
    child_id = request.args.get("child_id", type=int)
    selected_child = next((c for c in children if c["id"] == child_id), children[0])
    
    homework_list = get_homework_for_class(
        selected_child["class_name"], 
        selected_child.get("section")
    )
    
    # Due date status assign karo
    from datetime import date
    today = date.today().isoformat()
    for h in homework_list:
        if h.get("due_date"):
            h["status"] = "overdue" if h["due_date"] < today else ("today" if h["due_date"] == today else "upcoming")
        else:
            h["status"] = "no_due"
    
    return render_template("parent/homework.html", 
                           children=children, 
                           selected_child=selected_child, 
                           homework=homework_list)
