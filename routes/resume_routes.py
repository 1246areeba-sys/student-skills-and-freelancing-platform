"""Resume builder routes: render a printable professional resume."""
from flask import Blueprint, render_template, abort
from flask_login import login_required, current_user

from extensions import db
from models.student import StudentProfile
from models.review import Review
from sqlalchemy import func

resume_bp = Blueprint("resume", __name__, url_prefix="/resume")


@resume_bp.route("/")
@login_required
def view():
    if not current_user.is_student:
        abort(403)
    student = current_user.student_profile
    if not student:
        abort(404)
    reviews = Review.query.filter_by(reviewed_user_id=current_user.id).all()
    avg_rating = db.session.query(func.avg(Review.rating)).filter(
        Review.reviewed_user_id == current_user.id
    ).scalar() or 0
    return render_template(
        "student/resume_view.html",
        student=student,
        reviews=reviews,
        avg_rating=round(float(avg_rating or 0), 1),
    )


@resume_bp.route("/print")
@login_required
def print_resume():
    if not current_user.is_student:
        abort(403)
    student = current_user.student_profile
    if not student:
        abort(404)
    return render_template("student/resume_print.html", student=student)
