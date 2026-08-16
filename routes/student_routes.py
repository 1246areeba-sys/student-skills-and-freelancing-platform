"""Student routes: dashboard, profile, skills, portfolio, certificates,
assessments, resume builder, applications, earnings and wishlist."""
from datetime import datetime, date

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from sqlalchemy import func, or_

from extensions import db
from models.user import User
from models.student import StudentProfile, StudentSkill
from models.skill import Skill
from models.category import Category
from models.portfolio import Portfolio
from models.certificate import Certificate
from models.assessment import Assessment, AssessmentResult
from models.project import Project, Hire
from models.proposal import Proposal
from models.payment import Payment, Withdrawal
from models.review import Review
from models.wishlist import Wishlist
from models.message import Message
from models.notification import Notification
from utils import save_upload, notify, profile_completion_percentage

student_bp = Blueprint("student", __name__, url_prefix="/student")


def get_student():
    """Return the current user's student profile or abort."""
    if not current_user.is_student:
        abort(403)
    profile = current_user.student_profile
    if not profile:
        profile = StudentProfile(user_id=current_user.id)
        db.session.add(profile)
        db.session.commit()
    return profile


@student_bp.route("/dashboard")
@login_required
def dashboard():
    student = get_student()

    total_projects = student.hires.count()
    active_projects = student.hires.filter(Hire.status == "active").count()
    completed_projects = student.hires.filter(Hire.status == "completed").count()

    total_earnings = db.session.query(
        func.coalesce(func.sum(Payment.student_amount), 0)
    ).filter(Payment.student_id == student.id, Payment.status == "paid").scalar() or 0

    avg_rating = db.session.query(func.avg(Review.rating)).filter(
        Review.reviewed_user_id == current_user.id
    ).scalar() or 0

    proposals_sent = student.proposals.count()
    proposals_accepted = student.proposals.filter(Proposal.status == "accepted").count()

    saved_projects = Wishlist.query.filter_by(
        user_id=current_user.id, item_type="project"
    ).count()

    notifications = Notification.query.filter_by(
        user_id=current_user.id
    ).order_by(Notification.created_at.desc()).limit(5).all()

    recent_messages = Message.query.filter(
        or_(Message.sender_id == current_user.id, Message.receiver_id == current_user.id)
    ).order_by(Message.created_at.desc()).limit(5).all()

    # Recommended projects based on skill matching
    recommended = []
    student_skills = set(student.skill_names)
    if student_skills:
        open_projects = Project.query.filter_by(status="open").order_by(
            Project.created_at.desc()
        ).limit(30).all()
        scored = []
        for p in open_projects:
            p_skills = set(p.skill_names)
            if p_skills:
                matched = len(p_skills & student_skills)
                score = round((matched / len(p_skills)) * 100)
                scored.append((score, p))
        scored.sort(key=lambda x: x[0], reverse=True)
        recommended = [p for _, p in scored[:6]]

    return render_template(
        "student/dashboard.html",
        student=student,
        total_projects=total_projects,
        active_projects=active_projects,
        completed_projects=completed_projects,
        total_earnings=float(total_earnings or 0),
        avg_rating=round(float(avg_rating or 0), 1),
        proposals_sent=proposals_sent,
        proposals_accepted=proposals_accepted,
        saved_projects=saved_projects,
        notifications=notifications,
        recent_messages=recent_messages,
        recommended=recommended,
        completion=profile_completion_percentage(student),
    )


@student_bp.route("/profile")
@login_required
def profile():
    student = get_student()
    reviews = Review.query.filter_by(reviewed_user_id=current_user.id).order_by(
        Review.created_at.desc()
    ).all()
    avg_rating = db.session.query(func.avg(Review.rating)).filter(
        Review.reviewed_user_id == current_user.id
    ).scalar() or 0
    return render_template(
        "student/profile.html",
        student=student,
        reviews=reviews,
        avg_rating=round(float(avg_rating or 0), 1),
    )


@student_bp.route("/profile/edit", methods=["GET", "POST"])
@login_required
def edit_profile():
    student = get_student()
    if request.method == "POST":
        student.bio = request.form.get("bio", "").strip()
        student.university = request.form.get("university", "").strip()
        student.education = request.form.get("education", "").strip()
        student.experience = request.form.get("experience", "Entry Level")
        student.hourly_rate = request.form.get("hourly_rate", 0) or 0
        student.availability = request.form.get("availability", "Full Time")
        student.languages = request.form.get("languages", "English").strip()
        student.student_id = request.form.get("student_id", "").strip()
        student.university_email = request.form.get("university_email", "").strip()

        current_user.phone = request.form.get("phone", "").strip()
        current_user.city = request.form.get("city", "").strip()

        picture = request.files.get("profile_picture")
        if picture and picture.filename:
            pic = save_upload(picture, "profiles")
            if pic:
                current_user.profile_picture = pic
            else:
                flash("Invalid image file.", "danger")

        db.session.commit()
        flash("Profile updated successfully.", "success")
        return redirect(url_for("student.profile"))

    return render_template("student/edit_profile.html", student=student)


@student_bp.route("/skills", methods=["GET", "POST"])
@login_required
def skills():
    student = get_student()
    if request.method == "POST":
        skill_id = request.form.get("skill_id")
        level = request.form.get("skill_level", "Intermediate")
        if skill_id:
            existing = StudentSkill.query.filter_by(
                student_id=student.id, skill_id=skill_id
            ).first()
            if existing:
                existing.skill_level = level
                flash("Skill level updated.", "success")
            else:
                db.session.add(StudentSkill(
                    student_id=student.id, skill_id=skill_id, skill_level=level
                ))
                flash("Skill added successfully.", "success")
            db.session.commit()
        return redirect(url_for("student.skills"))

    all_skills = Skill.query.order_by(Skill.name).all()
    categories = Category.query.order_by(Category.name).all()
    return render_template(
        "student/skills.html",
        student=student,
        all_skills=all_skills,
        categories=categories,
    )


@student_bp.route("/skills/remove/<int:skill_id>", methods=["POST"])
@login_required
def remove_skill(skill_id):
    student = get_student()
    link = StudentSkill.query.filter_by(
        student_id=student.id, skill_id=skill_id
    ).first()
    if link:
        db.session.delete(link)
        db.session.commit()
        flash("Skill removed.", "info")
    return redirect(url_for("student.skills"))


@student_bp.route("/portfolio")
@login_required
def portfolio():
    student = get_student()
    return render_template("student/portfolio.html", student=student)


@student_bp.route("/portfolio/add", methods=["GET", "POST"])
@login_required
def add_portfolio():
    student = get_student()
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        if not title:
            flash("Project title is required.", "danger")
            return redirect(url_for("student.add_portfolio"))
        image = request.files.get("image")
        img_path = save_upload(image, "portfolio") if image and image.filename else None
        item = Portfolio(
            student_id=student.id,
            title=title,
            description=request.form.get("description", "").strip(),
            image=img_path,
            technologies=request.form.get("technologies", "").strip(),
            project_url=request.form.get("project_url", "").strip(),
            github_url=request.form.get("github_url", "").strip(),
            category_id=request.form.get("category_id") or None,
        )
        comp = request.form.get("completion_date")
        if comp:
            try:
                item.completion_date = datetime.strptime(comp, "%Y-%m-%d").date()
            except ValueError:
                pass
        db.session.add(item)
        db.session.commit()
        flash("Portfolio item added successfully.", "success")
        return redirect(url_for("student.portfolio"))

    categories = Category.query.order_by(Category.name).all()
    return render_template("student/add_portfolio.html", categories=categories)


@student_bp.route("/portfolio/edit/<int:item_id>", methods=["GET", "POST"])
@login_required
def edit_portfolio(item_id):
    student = get_student()
    item = Portfolio.query.filter_by(id=item_id, student_id=student.id).first_or_404()
    if request.method == "POST":
        item.title = request.form.get("title", "").strip()
        item.description = request.form.get("description", "").strip()
        item.technologies = request.form.get("technologies", "").strip()
        item.project_url = request.form.get("project_url", "").strip()
        item.github_url = request.form.get("github_url", "").strip()
        item.category_id = request.form.get("category_id") or None
        image = request.files.get("image")
        if image and image.filename:
            img_path = save_upload(image, "portfolio")
            if img_path:
                item.image = img_path
        comp = request.form.get("completion_date")
        if comp:
            try:
                item.completion_date = datetime.strptime(comp, "%Y-%m-%d").date()
            except ValueError:
                pass
        db.session.commit()
        flash("Portfolio item updated successfully.", "success")
        return redirect(url_for("student.portfolio"))
    categories = Category.query.order_by(Category.name).all()
    return render_template(
        "student/add_portfolio.html", item=item, categories=categories, editing=True
    )


@student_bp.route("/portfolio/delete/<int:item_id>", methods=["POST"])
@login_required
def delete_portfolio(item_id):
    student = get_student()
    item = Portfolio.query.filter_by(id=item_id, student_id=student.id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    flash("Portfolio item deleted.", "info")
    return redirect(url_for("student.portfolio"))


@student_bp.route("/certificates", methods=["GET", "POST"])
@login_required
def certificates():
    student = get_student()
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        if not title:
            flash("Certificate title is required.", "danger")
            return redirect(url_for("student.certificates"))
        cert_file = request.files.get("certificate_file")
        file_path = save_upload(cert_file, "certificates") if cert_file and cert_file.filename else None
        cert = Certificate(
            student_id=student.id,
            title=title,
            organization=request.form.get("organization", "").strip(),
            credential_id=request.form.get("credential_id", "").strip(),
            certificate_file=file_path,
            verification_url=request.form.get("verification_url", "").strip(),
        )
        issue = request.form.get("issue_date")
        if issue:
            try:
                cert.issue_date = datetime.strptime(issue, "%Y-%m-%d").date()
            except ValueError:
                pass
        db.session.add(cert)
        db.session.commit()
        flash("Certificate added successfully.", "success")
        return redirect(url_for("student.certificates"))
    return render_template("student/certificates.html", student=student)


@student_bp.route("/certificates/delete/<int:cert_id>", methods=["POST"])
@login_required
def delete_certificate(cert_id):
    student = get_student()
    cert = Certificate.query.filter_by(id=cert_id, student_id=student.id).first_or_404()
    db.session.delete(cert)
    db.session.commit()
    flash("Certificate deleted.", "info")
    return redirect(url_for("student.certificates"))


@student_bp.route("/assessments")
@login_required
def assessments():
    student = get_student()
    assessments = Assessment.query.filter_by(is_active=True).order_by(Assessment.title).all()
    results = {r.assessment_id: r for r in student.assessment_results}
    return render_template(
        "student/assessments.html",
        assessments=assessments,
        results=results,
    )


@student_bp.route("/assessments/take/<int:assessment_id>", methods=["GET", "POST"])
@login_required
def take_assessment(assessment_id):
    student = get_student()
    assessment = Assessment.query.filter_by(id=assessment_id, is_active=True).first_or_404()
    existing = AssessmentResult.query.filter_by(
        student_id=student.id, assessment_id=assessment.id
    ).first()
    if existing:
        flash("You have already completed this assessment.", "info")
        return redirect(url_for("student.assessments"))

    if request.method == "POST":
        questions = assessment.questions.all()
        score = 0
        for q in questions:
            answer = request.form.get(f"q_{q.id}", "").upper()
            if answer == q.correct_answer:
                score += 1
        total = len(questions)
        percentage = round((score / total) * 100) if total else 0
        passed = percentage >= assessment.passing_score
        result = AssessmentResult(
            student_id=student.id,
            assessment_id=assessment.id,
            score=score,
            percentage=percentage,
            passed=passed,
        )
        db.session.add(result)
        db.session.commit()
        if passed:
            notify(
                current_user.id,
                "Assessment Passed!",
                f"You passed the {assessment.title} assessment with {percentage}%.",
                "assessment",
                url_for("student.assessments"),
            )
            db.session.commit()
        flash(
            f"Assessment completed! Score: {score}/{total} ({percentage}%).",
            "success" if passed else "danger",
        )
        return redirect(url_for("student.assessments"))

    return render_template("student/take_assessment.html", assessment=assessment)


@student_bp.route("/resume")
@login_required
def resume_builder():
    student = get_student()
    return render_template("student/resume_builder.html", student=student)


@student_bp.route("/resume/view")
@login_required
def resume_view():
    student = get_student()
    reviews = Review.query.filter_by(reviewed_user_id=current_user.id).order_by(
        Review.created_at.desc()
    ).all()
    avg_rating = db.session.query(func.avg(Review.rating)).filter(
        Review.reviewed_user_id == current_user.id
    ).scalar() or 0
    return render_template(
        "student/resume_view.html",
        student=student,
        reviews=reviews,
        avg_rating=round(float(avg_rating or 0), 1),
    )


@student_bp.route("/resume/print")
@login_required
def resume_print():
    student = get_student()
    return render_template("student/resume_print.html", student=student)


@student_bp.route("/applications")
@login_required
def applications():
    student = get_student()
    proposals = student.proposals.order_by(Proposal.created_at.desc()).all()
    return render_template("student/applications.html", proposals=proposals)


@student_bp.route("/earnings")
@login_required
def earnings():
    student = get_student()
    payments = Payment.query.filter_by(student_id=student.id).order_by(
        Payment.created_at.desc()
    ).all()
    total_earned = db.session.query(
        func.coalesce(func.sum(Payment.student_amount), 0)
    ).filter(Payment.student_id == student.id, Payment.status == "paid").scalar() or 0
    pending = db.session.query(
        func.coalesce(func.sum(Payment.student_amount), 0)
    ).filter(Payment.student_id == student.id, Payment.status.in_(["pending", "processing"])).scalar() or 0
    withdrawn = db.session.query(
        func.coalesce(func.sum(Withdrawal.amount), 0)
    ).filter(Withdrawal.student_id == student.id, Withdrawal.status == "paid").scalar() or 0
    fees = db.session.query(
        func.coalesce(func.sum(Payment.platform_fee), 0)
    ).filter(Payment.student_id == student.id, Payment.status == "paid").scalar() or 0
    available = float(total_earned or 0) - float(withdrawn or 0)
    withdrawals = Withdrawal.query.filter_by(student_id=student.id).order_by(
        Withdrawal.created_at.desc()
    ).all()
    return render_template(
        "student/earnings.html",
        payments=payments,
        total_earned=float(total_earned or 0),
        pending=float(pending or 0),
        withdrawn=float(withdrawn or 0),
        fees=float(fees or 0),
        available=available,
        withdrawals=withdrawals,
    )


@student_bp.route("/earnings/withdraw", methods=["POST"])
@login_required
def withdraw():
    student = get_student()
    amount = request.form.get("amount", 0, type=float)
    method = request.form.get("method", "Bank Transfer")
    account = request.form.get("account_details", "").strip()
    total_earned = db.session.query(
        func.coalesce(func.sum(Payment.student_amount), 0)
    ).filter(Payment.student_id == student.id, Payment.status == "paid").scalar() or 0
    withdrawn = db.session.query(
        func.coalesce(func.sum(Withdrawal.amount), 0)
    ).filter(Withdrawal.student_id == student.id, Withdrawal.status == "paid").scalar() or 0
    available = float(total_earned or 0) - float(withdrawn or 0)
    if not amount or amount <= 0:
        flash("Please enter a valid amount.", "danger")
    elif amount > available:
        flash("Amount exceeds your available balance.", "danger")
    else:
        db.session.add(Withdrawal(
            student_id=student.id,
            amount=amount,
            method=method,
            account_details=account,
        ))
        db.session.commit()
        flash("Withdrawal request submitted successfully.", "success")
    return redirect(url_for("student.earnings"))


@student_bp.route("/wishlist")
@login_required
def wishlist():
    items = Wishlist.query.filter_by(user_id=current_user.id).order_by(
        Wishlist.created_at.desc()
    ).all()
    return render_template("student/wishlist.html", items=items)


@student_bp.route("/wishlist/remove/<int:item_id>", methods=["POST"])
@login_required
def remove_wishlist(item_id):
    item = Wishlist.query.filter_by(id=item_id, user_id=current_user.id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    flash("Item removed from wishlist.", "info")
    return redirect(url_for("student.wishlist"))