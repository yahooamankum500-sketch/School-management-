from flask import Blueprint, render_template, request, redirect, url_for, flash
from modules.auth import login_required
from database import (
    create_bus_route, get_bus_routes, create_bus_stop, 
    get_bus_stops, assign_transport, get_students_on_route, get_students
)

transport_bp = Blueprint("transport", __name__, url_prefix="/transport")

@transport_bp.route("/")
@login_required
def index():
    routes = get_bus_routes()
    return render_template("transport/index.html", routes=routes)

@transport_bp.route("/add-route", methods=["POST"])
@login_required
def add_route():
    data = request.form.to_dict()
    if data.get("route_name"):
        create_bus_route(data)
        flash("Bus route successfully add ho gaya!", "success")
    else:
        flash("Route name zaroori hai", "error")
    return redirect(url_for("transport.index"))

@transport_bp.route("/route/<int:route_id>")
@login_required
def view_route(route_id):
    # Get route details
    routes = get_bus_routes()
    route = next((r for r in routes if r["id"] == route_id), None)
    if not route:
        flash("Route nahi mila", "error")
        return redirect(url_for("transport.index"))
        
    stops = get_bus_stops(route_id)
    students = get_students_on_route(route_id)
    all_students = get_students() # Form ke liye
    
    return render_template("transport/view_route.html", 
                           route=route, stops=stops, 
                           students=students, all_students=all_students)

@transport_bp.route("/route/<int:route_id>/add-stop", methods=["POST"])
@login_required
def add_stop(route_id):
    data = request.form.to_dict()
    data["route_id"] = route_id
    if data.get("stop_name"):
        create_bus_stop(data)
        flash("Stop successfully add ho gaya!", "success")
    else:
        flash("Stop name zaroori hai", "error")
    return redirect(url_for("transport.view_route", route_id=route_id))

@transport_bp.route("/assign", methods=["POST"])
@login_required
def assign():
    student_id = request.form.get("student_id")
    route_id = request.form.get("route_id")
    stop_id = request.form.get("stop_id")
    
    try:
        assign_transport(student_id, route_id, stop_id)
        flash("Student ko bus mein assign kar diya gaya!", "success")
    except Exception as e:
        flash(f"Error: {str(e)}", "error")
        
    return redirect(url_for("transport.view_route", route_id=route_id))
