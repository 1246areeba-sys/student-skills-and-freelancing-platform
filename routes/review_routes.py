"""Review routes: leave a review after project completion."""
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user

from extensions import db
from models.project import Project, Hire
from models.review import Review
from models.user import User
from utils import notify

review_bp = Blueprint("review", __name__, url_prefix="/reviews")


@review_bp.route("/projects/<int:project_id>/review", methods=["GET", "POST"])
@login_required
def leave_review(project_id):
    project = Project.query.get_or_404(project_id)

    # Determine the counterpart user to review
    hire = Hire.query.filter_by(project_id=project.id).first()
    if not hire:
        flash("No completed hire found for this project.", "warning")
        return redirect(url_for("projects.detail", project_id=project.id))

    if current_user.is_student and hire.student_id == current_user.student_profile.id:
        reviewed_user_id = project.client.user_id
        reviewer_role = "student"
    elif current_user.is_client and project.client_id == current_user.client_profile.id:
        reviewed_user_id = hire.student.user_id
        reviewer_role = "client"
    else:
        abort(403)

    # Prevent duplicate review
    existing = Review.query.filter_by(
        project_id=project.id,
        reviewer_id=current_user.id,
        reviewed_user_id=reviewed_user_id,
    ).first()
    if existing:
        flash("You have already reviewed this user for this project.", "info")
        return redirect(url_for("projects.detail", project_id=project.id))

    if request.method == "POST":
        rating = request.form.get("rating", 5, type=int)
        text = request.form.get("review", "").strip()
        if rating < 1 or rating > 5:
            rating = 5
        review = Review(
            project_id=project.id,
            reviewer_id=current_user.id,
            reviewed_user_id=reviewed_user_id,
            rating=rating,
            review=text,
        )
        db.session.add(review)
        notify(
            reviewed_user_id,
            "New Review Received",
            f"{current_user.name} left you a {rating}-star review on '{project.title}'.",
            "review",
            url_for("projects.detail", project_id=project.id),
        )
        db.session.commit()
        flash("Review submitted successfully. Thank you!", "success")
        return redirect(url_for("projects.detail", project_id=project.id))

    reviewed_user = User.query.get(reviewed_user_id)
    return render_template(
        "reviews/leave.html",
        project=project,
        reviewed_user=reviewed_user,
        reviewer_role=reviewer_role,
    )
