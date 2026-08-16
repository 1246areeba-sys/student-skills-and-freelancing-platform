"""Client routes: dashboard, profile, post project, my projects,
proposals, hired students and payments."""
from datetime import datetime

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from sqlalchemy import func

from extensions import db
from models.user import User
from models.client import ClientProfile
from models.project import Project, ProjectSkill, Hire
from models.skill import Skill
from models.category import Category
from models.proposal import Proposal
from models.payment import Payment
from models.review import Review
from models.notification import Notification
from utils import save_upload, notify

client_bp = Blueprint("client", __name__, url_prefix="/client")


def get_client():
    """Return the current user's client profile or abort."""
    if not current_user.is_client:
        abort(403)
    profile = current_user.client_profile
    if not profile:
        profile = ClientProfile(user_id=current_user.id)
        db.session.add(profile)
        db.session.commit()
    return profile


@client_bp.route("/dashboard")
@login_required
def dashboard():
    client = get_client()
    projects = client.projects.order_by(Project.created_at.desc()).all()
    total_posted = client.projects.count()
    active = client.projects.filter(Project.status.in_(["open", "in_progress"])).count()
    completed = client.projects.filter_by(status="completed").count()
    received_proposals = Proposal.query.join(Project).filter(
        Project.client_id == client.id
    ).count()
    hired_count = Hire.query.filter_by(client_id=client.id, status="active").count()

    total_spent = db.session.query(
        func.coalesce(func.sum(Payment.amount), 0)
    ).filter(Payment.client_id == client.id, Payment.status == "paid").scalar() or 0

    avg_rating = db.session.query(func.avg(Review.rating)).filter(
        Review.reviewed_user_id == current_user.id
    ).scalar() or 0

    pending_proposals = Proposal.query.join(Project).filter(
        Project.client_id == client.id,
        Proposal.status == "pending",
    ).order_by(Proposal.created_at.desc()).limit(5).all()

    recent_notifications = Notification.query.filter_by(
        user_id=current_user.id
    ).order_by(Notification.created_at.desc()).limit(5).all()

    return render_template(
        "client/dashboard.html",
        client=client,
        projects=projects,
        total_posted=total_posted,
        active=active,
        completed=completed,
        received_proposals=received_proposals,
        hired_count=hired_count,
        total_spent=float(total_spent or 0),
        avg_rating=round(float(avg_rating or 0), 1),
        pending_proposals=pending_proposals,
        recent_notifications=recent_notifications,
    )


@client_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    client = get_client()
    if request.method == "POST":
        current_user.name = request.form.get("name", "").strip()
        current_user.phone = request.form.get("phone", "").strip()
        current_user.city = request.form.get("city", "").strip()
        client.company_name = request.form.get("company", "").strip()
        client.description = request.form.get("description", "").strip()
        picture = request.files.get("profile_picture")
        if picture and picture.filename:
            pic = save_upload(picture, "profiles")
            if pic:
                current_user.profile_picture = pic
        db.session.commit()
        flash("Profile updated successfully.", "success")
        return redirect(url_for("client.profile"))
    return render_template("client/profile.html", client=client)


@client_bp.route("/projects/post", methods=["GET", "POST"])
@login_required
def post_project():
    client = get_client()
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        budget = request.form.get("budget", 0, type=float)
        if not title or not description:
            flash("Project title and description are required.", "danger")
            return redirect(url_for("client.post_project"))

        project = Project(
            client_id=client.id,
            title=title,
            description=description,
            budget=budget or 0,
            category_id=request.form.get("category_id") or None,
            project_type=request.form.get("project_type", "Fixed"),
            location_type=request.form.get("location_type", "Remote"),
            location=request.form.get("location", "").strip(),
            freelancers_needed=request.form.get("freelancers_needed", 1, type=int) or 1,
            status=request.form.get("status", "open"),
        )
        deadline = request.form.get("deadline")
        if deadline:
            try:
                project.deadline = datetime.strptime(deadline, "%Y-%m-%d").date()
            except ValueError:
                pass
        attachment = request.files.get("attachment")
        if attachment and attachment.filename:
            att = save_upload(attachment, "general")
            if att:
                project.attachment = att
        db.session.add(project)
        db.session.flush()

        # Required skills
        for skill_id in request.form.getlist("skills"):
            skill = Skill.query.get(skill_id)
            if skill:
                db.session.add(ProjectSkill(project_id=project.id, skill_id=skill.id))

        db.session.commit()

        # Notify matching students
        from models.student import StudentProfile, StudentSkill
        skill_ids = [int(s) for s in request.form.getlist("skills") if s.isdigit()]
        if skill_ids:
            candidates = (
                StudentSkill.query.filter(StudentSkill.skill_id.in_(skill_ids))
                .with_entities(StudentSkill.student_id)
                .distinct()
                .all()
            )
            for (sid,) in candidates:
                student = StudentProfile.query.get(sid)
                if student:
                    notify(
                        student.user_id,
                        "New Matching Project",
                        f"A new project '{title}' matches your skills.",
                        "project",
                        url_for("projects.detail", project_id=project.id),
                    )
            db.session.commit()

        flash("Project posted successfully.", "success")
        return redirect(url_for("client.my_projects"))
    return render_template(
        "client/post_project.html",
        categories=Category.query.order_by(Category.name).all(),
        skills=Skill.query.order_by(Skill.name).all(),
    )


@client_bp.route("/projects")
@login_required
def my_projects():
    client = get_client()
    projects = client.projects.order_by(Project.created_at.desc()).all()
    return render_template("client/my_projects.html", projects=projects)


@client_bp.route("/projects/<int:project_id>/proposals")
@login_required
def proposals(project_id):
    client = get_client()
    project = Project.query.filter_by(id=project_id, client_id=client.id).first_or_404()
    proposals = project.proposals.order_by(Proposal.created_at.desc()).all()
    return render_template(
        "client/proposals.html", project=project, proposals=proposals
    )


@client_bp.route("/proposals/all")
@login_required
def all_proposals():
    client = get_client()
    proposals = (
        Proposal.query.join(Project)
        .filter(Project.client_id == client.id)
        .order_by(Proposal.created_at.desc())
        .all()
    )
    return render_template("client/proposals_all.html", proposals=proposals)


@client_bp.route("/proposals/<int:proposal_id>/accept", methods=["POST"])
@login_required
def accept_proposal(proposal_id):
    client = get_client()
    proposal = Proposal.query.filter_by(id=proposal_id).first_or_404()
    if proposal.project.client_id != client.id:
        abort(403)

    # Reject all other pending proposals for this project
    for other in proposal.project.proposals:
        if other.id != proposal.id and other.status == "pending":
            other.status = "rejected"
            notify(
                other.student.user_id,
                "Proposal Not Selected",
                f"Your proposal for '{proposal.project.title}' was not selected.",
                "proposal",
                url_for("student.applications"),
            )

    proposal.status = "accepted"
    proposal.project.status = "in_progress"
    hire = Hire(
        project_id=proposal.project_id,
        student_id=proposal.student_id,
        client_id=client.id,
        proposal_id=proposal.id,
        status="active",
    )
    db.session.add(hire)
    db.session.flush()

    # Create a pending payment record
    amount = float(proposal.proposed_price or proposal.project.budget or 0)
    fee = round(amount * 0.10, 2)
    payment = Payment(
        project_id=proposal.project_id,
        client_id=client.id,
        student_id=proposal.student_id,
        amount=amount,
        platform_fee=fee,
        student_amount=round(amount - fee, 2),
        status="pending",
        payment_method="Platform Balance",
    )
    db.session.add(payment)

    notify(
        proposal.student.user_id,
        "You Were Hired!",
        f"Congratulations! You have been hired for '{proposal.project.title}'.",
        "hire",
        url_for("projects.workspace", project_id=proposal.project_id),
    )
    db.session.commit()

    flash("Student hired successfully. A workspace has been created.", "success")
    return redirect(url_for("projects.workspace", project_id=proposal.project_id))


@client_bp.route("/proposals/<int:proposal_id>/reject", methods=["POST"])
@login_required
def reject_proposal(proposal_id):
    client = get_client()
    proposal = Proposal.query.filter_by(id=proposal_id).first_or_404()
    if proposal.project.client_id != client.id:
        abort(403)
    proposal.status = "rejected"
    notify(
        proposal.student.user_id,
        "Proposal Not Selected",
        f"Your proposal for '{proposal.project.title}' was not selected.",
        "proposal",
        url_for("student.applications"),
    )
    db.session.commit()
    flash("Proposal rejected.", "info")
    return redirect(url_for("client.proposals", project_id=proposal.project_id))


@client_bp.route("/hired")
@login_required
def hired_students():
    client = get_client()
    hires = Hire.query.filter_by(client_id=client.id).order_by(Hire.hired_at.desc()).all()
    return render_template("client/hired_students.html", hires=hires)


@client_bp.route("/payments")
@login_required
def payments():
    client = get_client()
    payments = Payment.query.filter_by(client_id=client.id).order_by(
        Payment.created_at.desc()
    ).all()
    total_spent = db.session.query(
        func.coalesce(func.sum(Payment.amount), 0)
    ).filter(Payment.client_id == client.id, Payment.status == "paid").scalar() or 0
    pending = db.session.query(
        func.coalesce(func.sum(Payment.amount), 0)
    ).filter(Payment.client_id == client.id, Payment.status == "pending").scalar() or 0
    return render_template(
        "client/payments.html",
        payments=payments,
        total_spent=float(total_spent or 0),
        pending=float(pending or 0),
    )


@client_bp.route("/payments/<int:payment_id>/mark-paid", methods=["POST"])
@login_required
def mark_paid(payment_id):
    client = get_client()
    payment = Payment.query.filter_by(id=payment_id, client_id=client.id).first_or_404()
    payment.status = "paid"
    notify(
        payment.student.user_id,
        "Payment Received",
        f"Payment of ${float(payment.student_amount):,.2f} has been released for '{payment.project.title}'.",
        "payment",
        url_for("student.earnings"),
    )
    db.session.commit()
    flash("Payment marked as paid.", "success")
    return redirect(url_for("client.payments"))


@client_bp.route("/projects/<int:project_id>/complete", methods=["POST"])
@login_required
def complete_project(project_id):
    client = get_client()
    project = Project.query.filter_by(id=project_id, client_id=client.id).first_or_404()
    if project.status != "in_progress":
        flash("Only in-progress projects can be completed.", "warning")
        return redirect(url_for("projects.workspace", project_id=project.id))
    project.status = "completed"
    for hire in project.hires:
        hire.status = "completed"
    for payment in project.payments:
        if payment.status == "pending":
            payment.status = "processing"
    db.session.commit()
    flash("Project marked as completed. You can now release payment and leave a review.", "success")
    return redirect(url_for("projects.workspace", project_id=project.id))
