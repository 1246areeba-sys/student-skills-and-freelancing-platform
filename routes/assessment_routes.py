"""Assessment routes: admin management of assessments and questions."""
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user

from extensions import db
from models.assessment import Assessment, AssessmentQuestion
from models.skill import Skill
from utils import admin_required

assessment_bp = Blueprint("assessment", __name__, url_prefix="/assessments")


@assessment_bp.route("/admin")
@login_required
@admin_required
def admin_list():
    assessments = Assessment.query.order_by(Assessment.created_at.desc()).all()
    return render_template("admin/assessments.html", assessments=assessments)


@assessment_bp.route("/admin/create", methods=["GET", "POST"])
@login_required
@admin_required
def create():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        if not title:
            flash("Assessment title is required.", "danger")
            return redirect(url_for("assessment.create"))
        a = Assessment(
            title=title,
            description=request.form.get("description", "").strip(),
            skill_id=request.form.get("skill_id") or None,
            passing_score=request.form.get("passing_score", 70, type=int) or 70,
            duration_minutes=request.form.get("duration_minutes", 15, type=int) or 15,
            is_active=request.form.get("is_active") == "on",
        )
        db.session.add(a)
        db.session.commit()
        flash("Assessment created. Now add questions.", "success")
        return redirect(url_for("assessment.edit", assessment_id=a.id))
    return render_template(
        "admin/assessment_form.html",
        skills=Skill.query.order_by(Skill.name).all(),
        assessment=None,
    )


@assessment_bp.route("/admin/<int:assessment_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def edit(assessment_id):
    a = Assessment.query.get_or_404(assessment_id)
    if request.method == "POST":
        a.title = request.form.get("title", "").strip()
        a.description = request.form.get("description", "").strip()
        a.skill_id = request.form.get("skill_id") or None
        a.passing_score = request.form.get("passing_score", 70, type=int) or 70
        a.duration_minutes = request.form.get("duration_minutes", 15, type=int) or 15
        a.is_active = request.form.get("is_active") == "on"
        db.session.commit()
        flash("Assessment updated.", "success")
        return redirect(url_for("assessment.admin_list"))
    return render_template(
        "admin/assessment_form.html",
        skills=Skill.query.order_by(Skill.name).all(),
        assessment=a,
    )


@assessment_bp.route("/admin/<int:assessment_id>/add-question", methods=["POST"])
@login_required
@admin_required
def add_question(assessment_id):
    a = Assessment.query.get_or_404(assessment_id)
    question = request.form.get("question", "").strip()
    option_a = request.form.get("option_a", "").strip()
    option_b = request.form.get("option_b", "").strip()
    option_c = request.form.get("option_c", "").strip()
    option_d = request.form.get("option_d", "").strip()
    correct = request.form.get("correct_answer", "A").upper()
    if not question or not option_a or not option_b:
        flash("Question and at least options A and B are required.", "danger")
        return redirect(url_for("assessment.edit", assessment_id=assessment_id))
    if correct not in ("A", "B", "C", "D"):
        correct = "A"
    db.session.add(AssessmentQuestion(
        assessment_id=a.id,
        question=question,
        option_a=option_a,
        option_b=option_b,
        option_c=option_c,
        option_d=option_d,
        correct_answer=correct,
    ))
    db.session.commit()
    flash("Question added.", "success")
    return redirect(url_for("assessment.edit", assessment_id=assessment_id))


@assessment_bp.route("/admin/<int:assessment_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete(assessment_id):
    a = Assessment.query.get_or_404(assessment_id)
    db.session.delete(a)
    db.session.commit()
    flash("Assessment deleted.", "info")
    return redirect(url_for("assessment.admin_list"))
