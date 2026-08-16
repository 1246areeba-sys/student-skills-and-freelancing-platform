"""Project routes: marketplace, detail, search, workspace and tracking."""
from datetime import datetime, date

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from sqlalchemy import or_

from extensions import db
from models.project import Project, ProjectSkill, Hire
from models.student import StudentProfile
from models.skill import Skill
from models.category import Category
from models.proposal import Proposal
from models.milestone import Milestone
from models.payment import Payment
from models.message import Message
from models.review import Review
from models.wishlist import Wishlist
from utils import save_upload, notify, project_match_for_student

project_bp = Blueprint("projects", __name__, url_prefix="/projects")


@project_bp.route("/")
def projects():
    """Project marketplace with search, filters, sorting and pagination."""
    page = request.args.get("page", 1, type=int)
    q = request.args.get("q", "").strip()
    category_id = request.args.get("category", type=int)
    skill_id = request.args.get("skill", type=int)
    budget_max = request.args.get("budget_max", type=float)
    project_type = request.args.get("project_type", "")
    location_type = request.args.get("location_type", "")
    sort = request.args.get("sort", "newest")

    query = Project.query.filter(Project.status.in_(["open", "in_progress"]))

    if q:
        query = query.filter(or_(
            Project.title.ilike(f"%{q}%"),
            Project.description.ilike(f"%{q}%"),
        ))
    if category_id:
        query = query.filter(Project.category_id == category_id)
    if skill_id:
        query = query.join(ProjectSkill).filter(ProjectSkill.skill_id == skill_id)
    if budget_max:
        query = query.filter(Project.budget <= budget_max)
    if project_type:
        query = query.filter(Project.project_type == project_type)
    if location_type:
        query = query.filter(Project.location_type == location_type)

    if sort == "budget_high":
        query = query.order_by(Project.budget.desc())
    elif sort == "budget_low":
        query = query.order_by(Project.budget.asc())
    elif sort == "deadline":
        query = query.order_by(Project.deadline.asc())
    else:
        query = query.order_by(Project.created_at.desc())

    pagination = query.paginate(page=page, per_page=9, error_out=False)

    return render_template(
        "projects/projects.html",
        pagination=pagination,
        projects=pagination.items,
        categories=Category.query.order_by(Category.name).all(),
        skills=Skill.query.order_by(Skill.name).all(),
        filters={
            "q": q,
            "category": category_id,
            "skill": skill_id,
            "budget_max": budget_max,
            "project_type": project_type,
            "location_type": location_type,
            "sort": sort,
        },
    )


@project_bp.route("/<int:project_id>")
def detail(project_id):
    project = Project.query.get_or_404(project_id)
    proposals = project.proposals.order_by(Proposal.created_at.desc()).all()
    match = None
    already_applied = False
    is_hired = False
    if current_user.is_authenticated and current_user.is_student:
        student = current_user.student_profile
        if student:
            match = project_match_for_student(student, project)
            already_applied = Proposal.query.filter_by(
                project_id=project.id, student_id=student.id
            ).first() is not None
            is_hired = Hire.query.filter_by(
                project_id=project.id, student_id=student.id, status="active"
            ).first() is not None
    return render_template(
        "projects/project_detail.html",
        project=project,
        proposals=proposals,
        match=match,
        already_applied=already_applied,
        is_hired=is_hired,
    )


@project_bp.route("/students")
def students():
    """Student marketplace with search, filters, sorting and pagination."""
    page = request.args.get("page", 1, type=int)
    q = request.args.get("q", "").strip()
    skill_id = request.args.get("skill", type=int)
    category_id = request.args.get("category", type=int)
    max_rate = request.args.get("max_rate", type=float)
    availability = request.args.get("availability", "")
    university = request.args.get("university", "").strip()
    sort = request.args.get("sort", "newest")

    from models.user import User
    from models.student import StudentSkill

    query = StudentProfile.query.join(User).filter(User.status == "active")

    if q:
        query = query.filter(or_(
            User.name.ilike(f"%{q}%"),
            StudentProfile.university.ilike(f"%{q}%"),
            StudentProfile.bio.ilike(f"%{q}%"),
        ))
    if skill_id:
        query = query.join(StudentSkill).filter(StudentSkill.skill_id == skill_id)
    if category_id:
        query = query.join(StudentSkill).join(Skill).filter(
            Skill.category_id == category_id
        )
    if max_rate:
        query = query.filter(StudentProfile.hourly_rate <= max_rate)
    if availability:
        query = query.filter(StudentProfile.availability == availability)
    if university:
        query = query.filter(StudentProfile.university.ilike(f"%{university}%"))

    if sort == "rate_low":
        query = query.order_by(StudentProfile.hourly_rate.asc())
    elif sort == "rate_high":
        query = query.order_by(StudentProfile.hourly_rate.desc())
    else:
        query = query.order_by(StudentProfile.created_at.desc())

    pagination = query.paginate(page=page, per_page=9, error_out=False)

    return render_template(
        "projects/students.html",
        pagination=pagination,
        students=pagination.items,
        categories=Category.query.order_by(Category.name).all(),
        skills=Skill.query.order_by(Skill.name).all(),
        filters={
            "q": q,
            "skill": skill_id,
            "category": category_id,
            "max_rate": max_rate,
            "availability": availability,
            "university": university,
            "sort": sort,
        },
    )


@project_bp.route("/students/<int:student_id>")
def student_public(student_id):
    from models.review import Review
    from sqlalchemy import func
    student = StudentProfile.query.get_or_404(student_id)
    reviews = Review.query.filter_by(reviewed_user_id=student.user_id).order_by(
        Review.created_at.desc()
    ).all()
    avg_rating = db.session.query(func.avg(Review.rating)).filter(
        Review.reviewed_user_id == student.user_id
    ).scalar() or 0
    return render_template(
        "projects/student_public.html",
        student=student,
        reviews=reviews,
        avg_rating=round(float(avg_rating or 0), 1),
    )


@project_bp.route("/workspace/<int:project_id>")
@login_required
def workspace(project_id):
    project = Project.query.get_or_404(project_id)
    hire = Hire.query.filter_by(project_id=project.id, status="active").first()
    if not hire:
        flash("This project has no active workspace.", "warning")
        return redirect(url_for("projects.detail", project_id=project.id))

    is_client = current_user.is_client and project.client_id == current_user.client_profile.id
    is_student = current_user.is_student and hire.student_id == current_user.student_profile.id
    if not (is_client or is_student):
        abort(403)

    milestones = project.milestones.order_by(Milestone.created_at.asc()).all()
    messages = Message.query.filter_by(project_id=project.id).order_by(
        Message.created_at.asc()
    ).all()
    payment = Payment.query.filter_by(project_id=project.id).first()

    # Progress estimate based on milestones
    progress = 0
    if milestones:
        done = sum(1 for m in milestones if m.status in ("approved", "completed"))
        progress = round((done / len(milestones)) * 100)
    elif project.status == "completed":
        progress = 100
    elif project.status == "in_progress":
        progress = 25

    return render_template(
        "projects/workspace.html",
        project=project,
        hire=hire,
        milestones=milestones,
        messages=messages,
        payment=payment,
        progress=progress,
        is_client=is_client,
        is_student=is_student,
    )


@project_bp.route("/workspace/<int:project_id>/milestone/add", methods=["POST"])
@login_required
def add_milestone(project_id):
    project = Project.query.get_or_404(project_id)
    if not (current_user.is_client and project.client_id == current_user.client_profile.id):
        abort(403)
    title = request.form.get("title", "").strip()
    if not title:
        flash("Milestone title is required.", "danger")
        return redirect(url_for("projects.workspace", project_id=project.id))
    milestone = Milestone(
        project_id=project.id,
        title=title,
        description=request.form.get("description", "").strip(),
        amount=request.form.get("amount", 0, type=float) or 0,
    )
    deadline = request.form.get("deadline")
    if deadline:
        try:
            milestone.deadline = datetime.strptime(deadline, "%Y-%m-%d").date()
        except ValueError:
            pass
    db.session.add(milestone)
    db.session.commit()
    flash("Milestone added successfully.", "success")
    return redirect(url_for("projects.workspace", project_id=project.id))


@project_bp.route("/workspace/<int:project_id>/milestone/<int:milestone_id>/status", methods=["POST"])
@login_required
def update_milestone_status(project_id, milestone_id):
    project = Project.query.get_or_404(project_id)
    milestone = Milestone.query.filter_by(id=milestone_id, project_id=project.id).first_or_404()
    new_status = request.form.get("status", "")
    allowed = {"pending", "in_progress", "submitted", "approved", "revision", "completed"}
    if new_status not in allowed:
        flash("Invalid status.", "danger")
        return redirect(url_for("projects.workspace", project_id=project.id))

    if current_user.is_student and new_status in ("in_progress", "submitted"):
        milestone.status = new_status
    elif current_user.is_client and new_status in ("approved", "revision", "completed"):
        milestone.status = new_status
        if new_status in ("approved", "completed"):
            milestone.payment_status = "paid"
    else:
        abort(403)

    db.session.commit()
    flash("Milestone updated.", "success")
    return redirect(url_for("projects.workspace", project_id=project.id))


@project_bp.route("/workspace/<int:project_id>/submit", methods=["POST"])
@login_required
def submit_work(project_id):
    project = Project.query.get_or_404(project_id)
    hire = Hire.query.filter_by(project_id=project.id, status="active").first()
    if not hire or not (current_user.is_student and hire.student_id == current_user.student_profile.id):
        abort(403)
    project.status = "submitted"
    db.session.commit()
    notify(
        project.client.user_id,
        "Work Submitted",
        f"{current_user.name} submitted work for '{project.title}'. Please review.",
        "project",
        url_for("projects.workspace", project_id=project.id),
    )
    db.session.commit()
    flash("Work submitted for client review.", "success")
    return redirect(url_for("projects.workspace", project_id=project.id))


@project_bp.route("/workspace/<int:project_id>/approve", methods=["POST"])
@login_required
def approve_work(project_id):
    project = Project.query.get_or_404(project_id)
    if not (current_user.is_client and project.client_id == current_user.client_profile.id):
        abort(403)
    project.status = "completed"
    for hire in project.hires:
        hire.status = "completed"
    payment = Payment.query.filter_by(project_id=project.id).first()
    if payment:
        payment.status = "paid"
    db.session.commit()
    notify(
        project.hires.first().student.user_id,
        "Project Completed",
        f"'{project.title}' has been marked as completed. Payment released.",
        "project",
        url_for("projects.workspace", project_id=project.id),
    )
    db.session.commit()
    flash("Project completed successfully. Payment released.", "success")
    return redirect(url_for("projects.workspace", project_id=project.id))


@project_bp.route("/workspace/<int:project_id>/revision", methods=["POST"])
@login_required
def request_revision(project_id):
    project = Project.query.get_or_404(project_id)
    if not (current_user.is_client and project.client_id == current_user.client_profile.id):
        abort(403)
    project.status = "revision"
    db.session.commit()
    notify(
        project.hires.first().student.user_id,
        "Revision Requested",
        f"The client requested revisions on '{project.title}'.",
        "project",
        url_for("projects.workspace", project_id=project.id),
    )
    db.session.commit()
    flash("Revision requested.", "info")
    return redirect(url_for("projects.workspace", project_id=project.id))


@project_bp.route("/workspace/<int:project_id>/message", methods=["POST"])
@login_required
def workspace_message(project_id):
    project = Project.query.get_or_404(project_id)
    hire = Hire.query.filter_by(project_id=project.id, status="active").first()
    if not hire:
        abort(404)
    is_client = current_user.is_client and project.client_id == current_user.client_profile.id
    is_student = current_user.is_student and hire.student_id == current_user.student_profile.id
    if not (is_client or is_student):
        abort(403)

    text = request.form.get("message", "").strip()
    attachment = request.files.get("attachment")
    att_path = save_upload(attachment, "messages") if attachment and attachment.filename else None
    if not text and not att_path:
        flash("Message cannot be empty.", "danger")
        return redirect(url_for("projects.workspace", project_id=project.id))

    receiver_id = project.client.user_id if is_student else hire.student.user_id
    msg = Message(
        sender_id=current_user.id,
        receiver_id=receiver_id,
        project_id=project.id,
        message=text,
        attachment=att_path,
    )
    db.session.add(msg)
    notify(receiver_id, "New Message", f"{current_user.name} sent you a message.", "message",
           url_for("projects.workspace", project_id=project.id))
    db.session.commit()
    flash("Message sent.", "success")
    return redirect(url_for("projects.workspace", project_id=project.id))


@project_bp.route("/wishlist/toggle", methods=["POST"])
@login_required
def toggle_wishlist():
    item_type = request.form.get("item_type", "")
    item_id = request.form.get("item_id", type=int)
    if item_type not in ("student", "project") or not item_id:
        flash("Invalid wishlist item.", "danger")
        return redirect(request.referrer or url_for("home.index"))
    existing = Wishlist.query.filter_by(
        user_id=current_user.id, item_type=item_type, item_id=item_id
    ).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
        flash("Removed from wishlist.", "info")
    else:
        db.session.add(Wishlist(user_id=current_user.id, item_type=item_type, item_id=item_id))
        db.session.commit()
        flash("Saved to wishlist.", "success")
    return redirect(request.referrer or url_for("home.index"))
