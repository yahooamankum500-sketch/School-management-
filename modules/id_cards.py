from flask import Blueprint, render_template, abort
from modules.auth import login_required
from database import get_student

id_cards_bp = Blueprint("id_cards", __name__, url_prefix="/id-cards")

@id_cards_bp.route("/<int:student_id>")
@login_required
def generate_card(student_id):
    student = get_student(student_id)
    if not student:
        abort(404)
    
    # ID Card render karo (koi base.html extend nahi karna, ye ek standalone print page hai)
    return render_template("id_cards/card.html", student=student)

@id_cards_bp.route("/certificate/<int:student_id>")
@login_required
def generate_certificate(student_id):
    student = get_student(student_id)
    if not student:
        abort(404)
        
    # Certificate render karo
    return render_template("id_cards/certificate.html", student=student)
