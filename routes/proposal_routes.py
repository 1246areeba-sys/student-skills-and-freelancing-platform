"""Proposal routes: submit, withdraw, view applications."""
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user

from extensions import db
from models.project import Project
from models.proposal import Proposal
from utils import notify

proposal_bp = Blueprint("proposal", __name__, url_prefix="/proposals")


@proposal_bp.route("/projects/<int:project_id>/apply", methods=["GET", "POST"])
@login_required
def apply(project_id):
    if not current_user.is_student:
        flash("Only students can apply to projects.", "warning")
        return redirect(url_for("projects.detail", project_id=project_id))

    project = Project.query.get_or_404(project_id)
    if not project.is_open:
        flash("This project is no longer accepting proposals.", "warning")
        return redirect(url_for("projects.detail", project_id=project_id))

    student = current_user.student_profile
    existing = Proposal.query.filter_by(
        project_id=project.id, student_id=student.id
    ).first()
    if existing:
        flash("You have already submitted a proposal for this project.", "info")
        return redirect(url_for("student.applications"))

    if request.method == "POST":
        cover_letter = request.form.get("cover_letter", "").strip()
        proposed_price = request.form.get("proposed_price", 0, type=float)
        delivery_time = request.form.get("delivery_time", 7, type=int)
        if not cover_letter:
            flash("Cover letter is required.", "danger")
            return redirect(url_for("proposal.apply", project_id=project.id))

        proposal = Proposal(
            project_id=project.id,
            student_id=student.id,
            cover_letter=cover_letter,
            proposed_price=proposed_price or 0,
            delivery_time=delivery_time or 7,
            relevant_skills=request.form.get("relevant_skills", "").strip(),
            portfolio_samples=request.form.get("portfolio_samples", "").strip(),
        )
        db.session.add(proposal)
        db.session.flush()

        notify(
            project.client.user_id,
            "New Proposal Received",
            f"{current_user.name} submitted a proposal for '{project.title}'.",
            "proposal",
            url_for("client.proposals", project_id=project.id),
        )
        db.session.commit()
        flash("Proposal submitted successfully.", "success")
        return redirect(url_for("student.applications"))

    return render_template("proposal/apply.html", project=project)


@proposal_bp.route("/<int:proposal_id>/withdraw", methods=["POST"])
@login_required
def withdraw(proposal_id):
    proposal = Proposal.query.get_or_404(proposal_id)
    if proposal.student_id != current_user.student_profile.id:
        abort(403)
    if proposal.status != "pending":
        flash("Only pending proposals can be withdrawn.", "warning")
        return redirect(url_for("student.applications"))
    proposal.status = "withdrawn"
    db.session.commit()
    flash("Proposal withdrawn.", "info")
    return redirect(url_for("student.applications"))
