from flask import Blueprint, render_template, request, redirect, url_for, flash
from modules.auth import login_required
from database import (
    create_book, get_books, issue_book, return_book, 
    get_active_issues, get_students
)

library_bp = Blueprint("library", __name__, url_prefix="/library")

@library_bp.route("/")
@login_required
def index():
    books = get_books()
    active_issues = get_active_issues()
    students = get_students() # Issue form ke liye
    return render_template("library/index.html", books=books, issues=active_issues, students=students)

@library_bp.route("/add", methods=["POST"])
@login_required
def add_book():
    data = request.form.to_dict()
    if data.get("title"):
        create_book(data)
        flash("Book successfully add ho gayi!", "success")
    else:
        flash("Book ka title zaroori hai", "error")
    return redirect(url_for("library.index"))

@library_bp.route("/issue", methods=["POST"])
@login_required
def issue():
    book_id = request.form.get("book_id")
    student_id = request.form.get("student_id")
    try:
        issue_book(book_id, student_id)
        flash("Book successfully issue ho gayi!", "success")
    except Exception as e:
        flash(str(e), "error")
    return redirect(url_for("library.index"))

@library_bp.route("/return/<int:issue_id>", methods=["POST"])
@login_required
def return_book_route(issue_id):
    try:
        return_book(issue_id)
        flash("Book return ho gayi!", "success")
    except Exception as e:
        flash(str(e), "error")
    return redirect(url_for("library.index"))
