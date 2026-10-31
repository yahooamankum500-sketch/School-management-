from flask import Blueprint, render_template, request, redirect, url_for, flash
from modules.auth import login_required
from database import (
    create_hostel, get_hostels, create_hostel_room, 
    get_hostel_rooms, allocate_hostel_room, checkout_hostel, 
    get_hostel_inmates, get_students
)

hostel_bp = Blueprint("hostel", __name__, url_prefix="/hostel")

@hostel_bp.route("/")
@login_required
def index():
    hostels = get_hostels()
    return render_template("hostel/index.html", hostels=hostels)

@hostel_bp.route("/add", methods=["POST"])
@login_required
def add_hostel():
    data = request.form.to_dict()
    if data.get("name"):
        create_hostel(data)
        flash("Hostel successfully add ho gaya!", "success")
    else:
        flash("Hostel name zaroori hai", "error")
    return redirect(url_for("hostel.index"))

@hostel_bp.route("/<int:hostel_id>")
@login_required
def view_hostel(hostel_id):
    hostels = get_hostels()
    hostel = next((h for h in hostels if h["id"] == hostel_id), None)
    if not hostel:
        flash("Hostel nahi mila", "error")
        return redirect(url_for("hostel.index"))
        
    rooms = get_hostel_rooms(hostel_id)
    inmates = get_hostel_inmates(hostel_id)
    all_students = get_students() # Allocation form ke liye
    
    return render_template("hostel/view.html", 
                           hostel=hostel, rooms=rooms, 
                           inmates=inmates, all_students=all_students)

@hostel_bp.route("/<int:hostel_id>/add-room", methods=["POST"])
@login_required
def add_room(hostel_id):
    data = request.form.to_dict()
    if data.get("room_no"):
        try:
            create_hostel_room(hostel_id, data)
            flash("Room successfully add ho gaya!", "success")
        except Exception:
            flash("Room number pehle se exist karta hai.", "error")
    else:
        flash("Room number zaroori hai", "error")
    return redirect(url_for("hostel.view_hostel", hostel_id=hostel_id))

@hostel_bp.route("/allocate", methods=["POST"])
@login_required
def allocate():
    student_id = request.form.get("student_id")
    room_id = request.form.get("room_id")
    hostel_id = request.form.get("hostel_id")
    
    try:
        allocate_hostel_room(student_id, room_id)
        flash("Student ko room allocate ho gaya!", "success")
    except Exception as e:
        flash(str(e), "error")
        
    return redirect(url_for("hostel.view_hostel", hostel_id=hostel_id))

@hostel_bp.route("/checkout/<int:student_id>", methods=["POST"])
@login_required
def checkout(student_id):
    hostel_id = request.form.get("hostel_id")
    try:
        checkout_hostel(student_id)
        flash("Student checkout ho gaya!", "success")
    except Exception as e:
        flash(str(e), "error")
    return redirect(url_for("hostel.view_hostel", hostel_id=hostel_id))
