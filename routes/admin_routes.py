"""Admin routes: dashboard and full platform management."""
from datetime import datetime

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, current_app
from flask_login import login_required, current_user
from sqlalchemy import func

from extensions import db
from utils import admin_required, save_upload, notify
from models.site_setting import SiteSetting
from models.user import User
from models.student import StudentProfile, StudentSkill
from models.client import ClientProfile
from models.category import Category
from models.skill import Skill
from models.project import Project, ProjectSkill, Hire
from models.proposal import Proposal
from models.message import Message
from models.milestone import Milestone
from models.payment import Payment, Withdrawal
from models.review import Review
from models.notification import Notification
from models.certificate import Certificate
from models.assessment import Assessment
from models.wishlist import Wishlist
from models.banner import Banner

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
@admin_bp.route("/")
@login_required
@admin_required
def dashboard():
    total_students = User.query.filter_by(role="student").count()
    total_clients = User.query.filter_by(role="client").count()
    active_projects = Project.query.filter(Project.status.in_(["open", "in_progress"])).count()
    completed_projects = Project.query.filter_by(status="completed").count()
    total_proposals = Proposal.query.count()
    total_earnings = db.session.query(
        func.coalesce(func.sum(Payment.amount), 0)
    ).filter(Payment.status == "paid").scalar() or 0
    platform_revenue = db.session.query(
        func.coalesce(func.sum(Payment.platform_fee), 0)
    ).filter(Payment.status == "paid").scalar() or 0
    pending_withdrawals = Withdrawal.query.filter_by(status="pending").count()
    avg_rating = db.session.query(func.avg(Review.rating)).scalar() or 0

    recent_users = User.query.order_by(User.created_at.desc()).limit(8).all()
    recent_projects = Project.query.order_by(Project.created_at.desc()).limit(6).all()

    return render_template(
        "admin/dashboard.html",
        total_students=total_students,
        total_clients=total_clients,
        active_projects=active_projects,
        completed_projects=completed_projects,
        total_proposals=total_proposals,
        total_earnings=float(total_earnings or 0),
        platform_revenue=float(platform_revenue or 0),
        pending_withdrawals=pending_withdrawals,
        avg_rating=round(float(avg_rating or 0), 1),
        recent_users=recent_users,
        recent_projects=recent_projects,
    )


# ---------------------------------------------------------------------------
# User management
# ---------------------------------------------------------------------------
@admin_bp.route("/users")
@login_required
@admin_required
def users():
    role = request.args.get("role", "")
    q = request.args.get("q", "").strip()
    query = User.query
    if role:
        query = query.filter_by(role=role)
    if q:
        query = query.filter(User.name.ilike(f"%{q}%") | User.email.ilike(f"%{q}%"))
    users = query.order_by(User.created_at.desc()).all()
    return render_template("admin/users.html", users=users, role=role, q=q)


@admin_bp.route("/users/<int:user_id>/toggle-status", methods=["POST"])
@login_required
@admin_required
def toggle_user_status(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("You cannot suspend yourself.", "warning")
        return redirect(url_for("admin.users"))
    user.status = "suspended" if user.status == "active" else "active"
    db.session.commit()
    flash(f"User {user.name} is now {user.status}.", "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>/role", methods=["POST"])
@login_required
@admin_required
def change_role(user_id):
    user = User.query.get_or_404(user_id)
    new_role = request.form.get("role", "student")
    if new_role not in ("student", "client", "admin"):
        new_role = "student"
    user.role = new_role
    db.session.commit()
    flash(f"Role updated to {new_role}.", "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("You cannot delete yourself.", "warning")
        return redirect(url_for("admin.users"))
    db.session.delete(user)
    db.session.commit()
    flash("User deleted.", "info")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/add", methods=["GET", "POST"])
@login_required
@admin_required
def add_user():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()
        role = request.form.get("role", "student")
        if role not in ("student", "client", "admin"):
            role = "student"
        if not name or not email or not password:
            flash("Name, email and password are required.", "danger")
            return render_template("admin/user_form.html")
        if User.query.filter_by(email=email).first():
            flash("A user with that email already exists.", "warning")
            return render_template("admin/user_form.html")
        user = User(
            name=name,
            email=email,
            role=role,
            status=request.form.get("status", "active"),
            phone=request.form.get("phone", "").strip(),
            city=request.form.get("city", "").strip(),
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash("User created.", "success")
        return redirect(url_for("admin.users"))
    return render_template("admin/user_form.html")


@admin_bp.route("/users/<int:user_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    if request.method == "POST":
        user.name = request.form.get("name", "").strip() or user.name
        new_email = request.form.get("email", "").strip()
        if new_email and new_email != user.email:
            if User.query.filter_by(email=new_email).first():
                flash("That email is already in use.", "warning")
            else:
                user.email = new_email
        role = request.form.get("role", user.role)
        if role in ("student", "client", "admin"):
            user.role = role
        user.status = request.form.get("status", user.status)
        user.phone = request.form.get("phone", "").strip()
        user.city = request.form.get("city", "").strip()
        password = request.form.get("password", "").strip()
        if password:
            user.set_password(password)
        db.session.commit()
        flash("User updated.", "success")
        return redirect(url_for("admin.users"))
    return render_template("admin/user_form.html", user=user)


@admin_bp.route("/students")
@login_required
@admin_required
def students():
    students = StudentProfile.query.join(User).order_by(
        StudentProfile.created_at.desc()
    ).all()
    return render_template("admin/students.html", students=students)


@admin_bp.route("/students/add", methods=["GET", "POST"])
@login_required
@admin_required
def add_student():
    skills = Skill.query.order_by(Skill.name).all()
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        university = request.form.get("university", "").strip()
        education = request.form.get("education", "").strip()
        phone = request.form.get("phone", "").strip()
        city = request.form.get("city", "").strip()
        student_id = request.form.get("student_id", "").strip()
        university_email = request.form.get("university_email", "").strip().lower()
        bio = request.form.get("bio", "").strip()
        experience = request.form.get("experience", "Entry Level")
        hourly_rate = request.form.get("hourly_rate", 0, type=float) or 0
        availability = request.form.get("availability", "Full Time")
        languages = request.form.get("languages", "English").strip() or "English"
        verification_status = request.form.get("verification_status", "pending")
        skills_input = request.form.get("skills", "").strip()
        picture = request.files.get("profile_picture")

        errors = []
        if not name or not email or not password:
            errors.append("Name, email and password are required.")
        if "@" not in email or "." not in email.split("@")[-1]:
            errors.append("Please enter a valid email address.")
        if len(password) < 8:
            errors.append("Password must contain at least 8 characters.")
        if password != confirm:
            errors.append("Passwords do not match.")
        if User.query.filter_by(email=email).first():
            errors.append("An account with this email already exists.")
        if not university:
            errors.append("University/College is required.")

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("admin/student_add.html", skills=skills)

        user = User(name=name, email=email, role="student", phone=phone, city=city)
        user.set_password(password)
        pic = save_upload(picture, "profiles") if picture and picture.filename else None
        if pic:
            user.profile_picture = pic
        db.session.add(user)
        db.session.flush()

        profile = StudentProfile(
            user_id=user.id,
            university=university,
            education=education,
            bio=bio,
            experience=experience,
            hourly_rate=hourly_rate,
            availability=availability,
            languages=languages,
            student_id=student_id,
            university_email=university_email or email,
            verification_status=verification_status,
        )
        db.session.add(profile)
        db.session.flush()

        for skill_name in [s.strip() for s in skills_input.split(",") if s.strip()]:
            skill = Skill.query.filter(db.func.lower(Skill.name) == skill_name.lower()).first()
            if not skill:
                skill = Skill(name=skill_name)
                db.session.add(skill)
                db.session.flush()
            db.session.add(StudentSkill(student_id=profile.id, skill_id=skill.id))

        db.session.commit()
        flash(f"Student {name} created successfully.", "success")
        return redirect(url_for("admin.students"))

    return render_template("admin/student_add.html", skills=skills)


@admin_bp.route("/students/<int:student_id>/verify", methods=["POST"])
@login_required
@admin_required
def verify_student(student_id):
    student = StudentProfile.query.get_or_404(student_id)
    student.verification_status = "verified"
    db.session.commit()
    notify(student.user_id, "Verification Approved",
           "Your student profile has been verified.", "general",
           url_for("student.profile"))
    db.session.commit()
    flash("Student verified.", "success")
    return redirect(url_for("admin.students"))


@admin_bp.route("/students/<int:student_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def edit_student(student_id):
    student = StudentProfile.query.get_or_404(student_id)
    if request.method == "POST":
        student.university = request.form.get("university", "").strip()
        student.education = request.form.get("education", "").strip()
        student.bio = request.form.get("bio", "").strip()
        student.experience = request.form.get("experience", student.experience)
        student.hourly_rate = request.form.get("hourly_rate", 0, type=float) or 0
        student.availability = request.form.get("availability", student.availability)
        student.languages = request.form.get("languages", student.languages)
        student.verification_status = request.form.get("verification_status", student.verification_status)
        db.session.commit()
        flash("Student profile updated.", "success")
        return redirect(url_for("admin.students"))
    return render_template("admin/student_form.html", student=student)


@admin_bp.route("/students/<int:student_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_student(student_id):
    student = StudentProfile.query.get_or_404(student_id)
    user = student.user
    try:
        # Explicitly clear related rows that reference this user via NOT NULL
        # foreign keys (which have no ORM cascade) so deleting the user does
        # not violate integrity constraints and poison the DB session.
        if user:
            Message.query.filter(
                (Message.sender_id == user.id) | (Message.receiver_id == user.id)
            ).delete(synchronize_session=False)
            Notification.query.filter_by(user_id=user.id).delete(synchronize_session=False)
            Wishlist.query.filter_by(user_id=user.id).delete(synchronize_session=False)
            Review.query.filter(
                (Review.reviewer_id == user.id) | (Review.reviewed_user_id == user.id)
            ).delete(synchronize_session=False)
            Payment.query.filter_by(student_id=user.id).delete(synchronize_session=False)
            Milestone.query.filter_by(student_id=user.id).delete(synchronize_session=False)
            Project.query.filter_by(client_id=user.id).delete(synchronize_session=False)
        Proposal.query.filter_by(student_id=student_id).delete(synchronize_session=False)

        db.session.delete(student)
        if user:
            db.session.delete(user)
        db.session.commit()
        flash("Student and associated user deleted.", "info")
    except Exception as exc:
        db.session.rollback()
        flash(f"Could not delete student: {exc}", "danger")
    return redirect(url_for("admin.students"))


@admin_bp.route("/clients")
@login_required
@admin_required
def clients():
    clients = ClientProfile.query.join(User).order_by(
        ClientProfile.created_at.desc()
    ).all()
    return render_template("admin/clients.html", clients=clients)


@admin_bp.route("/clients/add", methods=["GET", "POST"])
@login_required
@admin_required
def add_client():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        company = request.form.get("company_name", "").strip()
        phone = request.form.get("phone", "").strip()
        city = request.form.get("city", "").strip()
        description = request.form.get("description", "").strip()
        picture = request.files.get("profile_picture")

        errors = []
        if not name or not email or not password:
            errors.append("Name, email and password are required.")
        if "@" not in email or "." not in email.split("@")[-1]:
            errors.append("Please enter a valid email address.")
        if len(password) < 8:
            errors.append("Password must contain at least 8 characters.")
        if password != confirm:
            errors.append("Passwords do not match.")
        if User.query.filter_by(email=email).first():
            errors.append("An account with this email already exists.")
        if not company:
            errors.append("Company/Organization is required.")

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("admin/client_add.html")

        user = User(name=name, email=email, role="client", phone=phone, city=city)
        user.set_password(password)
        pic = save_upload(picture, "profiles") if picture and picture.filename else None
        if pic:
            user.profile_picture = pic
        db.session.add(user)
        db.session.flush()

        db.session.add(ClientProfile(
            user_id=user.id,
            company_name=company,
            description=description,
            phone=phone,
            city=city,
        ))
        db.session.commit()
        flash(f"Client {name} created successfully.", "success")
        return redirect(url_for("admin.clients"))

    return render_template("admin/client_add.html")


@admin_bp.route("/clients/<int:client_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def edit_client(client_id):
    client = ClientProfile.query.get_or_404(client_id)
    if request.method == "POST":
        client.company_name = request.form.get("company_name", "").strip()
        client.description = request.form.get("description", "").strip()
        client.phone = request.form.get("phone", "").strip()
        client.city = request.form.get("city", "").strip()
        db.session.commit()
        flash("Client profile updated.", "success")
        return redirect(url_for("admin.clients"))
    return render_template("admin/client_form.html", client=client)


@admin_bp.route("/clients/<int:client_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_client(client_id):
    client = ClientProfile.query.get_or_404(client_id)
    user = client.user
    db.session.delete(client)
    if user:
        db.session.delete(user)
    db.session.commit()
    flash("Client and associated user deleted.", "info")
    return redirect(url_for("admin.clients"))


# ---------------------------------------------------------------------------
# Project management
# ---------------------------------------------------------------------------
@admin_bp.route("/projects")
@login_required
@admin_required
def projects():
    status = request.args.get("status", "")
    query = Project.query
    if status:
        query = query.filter_by(status=status)
    projects = query.order_by(Project.created_at.desc()).all()
    return render_template("admin/projects.html", projects=projects, status=status)

@admin_bp.route("/projects/create", methods=["GET", "POST"])
@login_required
@admin_required
def create_project():
    categories = Category.query.order_by(Category.name).all()
    clients = ClientProfile.query.join(User).order_by(User.name).all()
    skills = Skill.query.order_by(Skill.name).all()
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        client_id = request.form.get("client_id", type=int)
        if not title or not description:
            flash("Project title and description are required.", "warning")
            return render_template(
                "admin/project_create.html",
                categories=categories, clients=clients, skills=skills,
            )
        if not client_id:
            flash("Please select a client.", "warning")
            return render_template(
                "admin/project_create.html",
                categories=categories, clients=clients, skills=skills,
            )
        budget = request.form.get("budget", 0, type=float) or 0
        deadline = request.form.get("deadline", "").strip()
        cat = request.form.get("category_id") or None
        status = request.form.get("status", "open")
        project = Project(
            client_id=client_id,
            title=title,
            description=description,
            budget=budget,
            deadline=datetime.strptime(deadline, "%Y-%m-%d").date() if deadline else None,
            category_id=int(cat) if cat else None,
            status=status,
            project_type=request.form.get("project_type", "Fixed"),
            location_type=request.form.get("location_type", "Remote"),
            location=request.form.get("location", "").strip(),
            freelancers_needed=request.form.get("freelancers_needed", 1, type=int) or 1,
        )
        db.session.add(project)
        db.session.flush()
        for skill_id in request.form.getlist("skills"):
            skill = Skill.query.get(skill_id)
            if skill:
                db.session.add(ProjectSkill(project_id=project.id, skill_id=skill.id))
        db.session.commit()
        flash("Project created successfully.", "success")
        return redirect(url_for("admin.projects"))
    return render_template(
        "admin/project_create.html",
        categories=categories, clients=clients, skills=skills,
    )


@admin_bp.route("/projects/<int:project_id>")
@login_required
@admin_required
def view_project(project_id):
    project = Project.query.get_or_404(project_id)
    return render_template("admin/project_detail.html", project=project)



@admin_bp.route("/projects/<int:project_id>/status", methods=["POST"])
@login_required
@admin_required
def project_status(project_id):
    project = Project.query.get_or_404(project_id)
    new_status = request.form.get("status", project.status)
    project.status = new_status
    db.session.commit()
    flash("Project status updated.", "success")
    return redirect(url_for("admin.projects"))


@admin_bp.route("/projects/<int:project_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def edit_project(project_id):
    project = Project.query.get_or_404(project_id)
    categories = Category.query.order_by(Category.name).all()
    if request.method == "POST":
        project.title = request.form.get("title", "").strip() or project.title
        project.description = request.form.get("description", "").strip()
        project.budget = request.form.get("budget", 0, type=float) or 0
        project.project_type = request.form.get("project_type", project.project_type)
        project.location_type = request.form.get("location_type", project.location_type)
        project.location = request.form.get("location", "").strip()
        project.freelancers_needed = request.form.get("freelancers_needed", 1, type=int) or 1
        project.status = request.form.get("status", project.status)
        cat = request.form.get("category_id") or None
        project.category_id = int(cat) if cat else None
        deadline = request.form.get("deadline", "").strip()
        project.deadline = datetime.strptime(deadline, "%Y-%m-%d").date() if deadline else None
        db.session.commit()
        flash("Project updated.", "success")
        return redirect(url_for("admin.projects"))
    return render_template("admin/project_form.html", project=project, categories=categories)


@admin_bp.route("/projects/<int:project_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_project(project_id):
    project = Project.query.get_or_404(project_id)
    db.session.delete(project)
    db.session.commit()
    flash("Project deleted.", "info")
    return redirect(url_for("admin.projects"))


@admin_bp.route("/proposals")
@login_required
@admin_required
def proposals():
    proposals = Proposal.query.order_by(Proposal.created_at.desc()).all()
    return render_template("admin/proposals.html", proposals=proposals)


@admin_bp.route("/proposals/add", methods=["GET", "POST"])
@login_required
@admin_required
def add_proposal():
    projects = Project.query.order_by(Project.title).all()
    students = StudentProfile.query.join(User).order_by(User.name).all()
    if request.method == "POST":
        project_id = request.form.get("project_id", type=int)
        student_id = request.form.get("student_id", type=int)
        cover_letter = request.form.get("cover_letter", "").strip()
        if not project_id or not student_id or not cover_letter:
            flash("Project, student and cover letter are required.", "danger")
            return render_template(
                "admin/proposal_form.html", projects=projects, students=students
            )
        existing = Proposal.query.filter_by(
            project_id=project_id, student_id=student_id
        ).first()
        if existing:
            flash("This student already has a proposal for that project.", "warning")
            return render_template(
                "admin/proposal_form.html", projects=projects, students=students
            )
        proposal = Proposal(
            project_id=project_id,
            student_id=student_id,
            cover_letter=cover_letter,
            proposed_price=request.form.get("proposed_price", 0, type=float) or 0,
            delivery_time=request.form.get("delivery_time", 7, type=int) or 7,
            relevant_skills=request.form.get("relevant_skills", "").strip(),
            portfolio_samples=request.form.get("portfolio_samples", "").strip(),
            status=request.form.get("status", "pending"),
        )
        db.session.add(proposal)
        db.session.commit()
        flash("Proposal created successfully.", "success")
        return redirect(url_for("admin.proposals"))
    return render_template(
        "admin/proposal_form.html", projects=projects, students=students
    )


@admin_bp.route("/proposals/<int:proposal_id>/status", methods=["POST"])
@login_required
@admin_required
def proposal_status(proposal_id):
    proposal = Proposal.query.get_or_404(proposal_id)
    proposal.status = request.form.get("status", proposal.status)
    db.session.commit()
    flash("Proposal status updated.", "success")
    return redirect(url_for("admin.proposals"))


@admin_bp.route("/proposals/<int:proposal_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_proposal(proposal_id):
    proposal = Proposal.query.get_or_404(proposal_id)
    db.session.delete(proposal)
    db.session.commit()
    flash("Proposal deleted.", "info")
    return redirect(url_for("admin.proposals"))


@admin_bp.route("/proposals/<int:proposal_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def edit_proposal(proposal_id):
    proposal = Proposal.query.get_or_404(proposal_id)
    projects = Project.query.order_by(Project.title).all()
    students = StudentProfile.query.join(User).order_by(User.name).all()
    if request.method == "POST":
        proposal.project_id = request.form.get("project_id", type=int) or proposal.project_id
        proposal.student_id = request.form.get("student_id", type=int) or proposal.student_id
        proposal.cover_letter = request.form.get("cover_letter", "").strip() or proposal.cover_letter
        proposal.proposed_price = request.form.get("proposed_price", 0, type=float) or 0
        proposal.delivery_time = request.form.get("delivery_time", 7, type=int) or 7
        proposal.relevant_skills = request.form.get("relevant_skills", "").strip()
        proposal.portfolio_samples = request.form.get("portfolio_samples", "").strip()
        proposal.status = request.form.get("status", proposal.status)
        db.session.commit()
        flash("Proposal updated.", "success")
        return redirect(url_for("admin.proposals"))
    return render_template(
        "admin/proposal_edit.html", proposal=proposal, projects=projects, students=students
    )


@admin_bp.route("/hired")
@login_required
@admin_required
def hired():
    hires = Hire.query.order_by(Hire.hired_at.desc()).all()
    return render_template("admin/hired.html", hires=hires)


@admin_bp.route("/hired/add", methods=["GET", "POST"])
@login_required
@admin_required
def add_hire():
    projects = Project.query.order_by(Project.created_at.desc()).all()
    students = StudentProfile.query.join(User).order_by(User.name).all()
    clients = ClientProfile.query.join(User).order_by(User.name).all()
    if request.method == "POST":
        project_id = request.form.get("project_id", type=int)
        student_id = request.form.get("student_id", type=int)
        client_id = request.form.get("client_id", type=int)
        status = request.form.get("status", "active")
        amount = request.form.get("amount", type=float) or 0

        errors = []
        if not project_id:
            errors.append("Please select a project.")
        if not student_id:
            errors.append("Please select a student.")
        if not client_id:
            errors.append("Please select a client.")
        if amount <= 0:
            errors.append("Amount must be greater than zero.")

        project = Project.query.get(project_id) if project_id else None
        student = StudentProfile.query.get(student_id) if student_id else None
        client = ClientProfile.query.get(client_id) if client_id else None

        if project and student and Hire.query.filter_by(
            project_id=project.id, student_id=student.id
        ).first():
            errors.append("This student is already hired for this project.")

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template(
                "admin/hire_form.html",
                projects=projects, students=students, clients=clients,
            )

        # Mark project as in progress when a hire is created
        project.status = "in_progress"

        hire = Hire(
            project_id=project.id,
            student_id=student.id,
            client_id=client.id,
            status=status,
        )
        db.session.add(hire)
        db.session.flush()

        # Create a pending payment record (10% platform fee)
        fee = round(float(amount) * 0.10, 2)
        payment = Payment(
            project_id=project.id,
            client_id=client.id,
            student_id=student.id,
            amount=amount,
            platform_fee=fee,
            student_amount=round(float(amount) - fee, 2),
            status="pending",
            payment_method="Platform Balance",
        )
        db.session.add(payment)

        notify(
            student.user_id,
            "You Were Hired!",
            f"Congratulations! You have been hired for '{project.title}'.",
            "hire",
            url_for("projects.workspace", project_id=project.id),
        )
        db.session.commit()
        flash(f"{student.user.name} hired for '{project.title}'.", "success")
        return redirect(url_for("admin.hired"))

    return render_template(
        "admin/hire_form.html",
        projects=projects, students=students, clients=clients,
    )


@admin_bp.route("/hired/<int:hire_id>/status", methods=["POST"])
@login_required
@admin_required
def hire_status(hire_id):
    hire = Hire.query.get_or_404(hire_id)
    hire.status = request.form.get("status", hire.status)
    db.session.commit()
    flash("Hire status updated.", "success")
    return redirect(url_for("admin.hired"))


@admin_bp.route("/hired/<int:hire_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_hire(hire_id):
    hire = Hire.query.get_or_404(hire_id)
    db.session.delete(hire)
    db.session.commit()
    flash("Hire record deleted.", "info")
    return redirect(url_for("admin.hired"))


@admin_bp.route("/hired/<int:hire_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def edit_hire(hire_id):
    hire = Hire.query.get_or_404(hire_id)
    projects = Project.query.order_by(Project.title).all()
    students = StudentProfile.query.join(User).order_by(User.name).all()
    clients = ClientProfile.query.join(User).order_by(User.name).all()
    if request.method == "POST":
        hire.project_id = request.form.get("project_id", type=int) or hire.project_id
        hire.student_id = request.form.get("student_id", type=int) or hire.student_id
        hire.client_id = request.form.get("client_id", type=int) or hire.client_id
        hire.status = request.form.get("status", hire.status)
        db.session.commit()
        flash("Hire updated.", "success")
        return redirect(url_for("admin.hired"))
    return render_template(
        "admin/hire_edit.html",
        hire=hire, projects=projects, students=students, clients=clients,
    )


# ---------------------------------------------------------------------------
# Skills & categories
# ---------------------------------------------------------------------------
@admin_bp.route("/skills", methods=["GET", "POST"])
@login_required
@admin_required
def skills():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        category_id = request.form.get("category_id") or None
        if name:
            if not Skill.query.filter(db.func.lower(Skill.name) == name.lower()).first():
                db.session.add(Skill(name=name, category_id=category_id))
                db.session.commit()
                flash("Skill added.", "success")
            else:
                flash("Skill already exists.", "warning")
        return redirect(url_for("admin.skills"))
    skills = Skill.query.order_by(Skill.name).all()
    categories = Category.query.order_by(Category.name).all()
    return render_template("admin/skills.html", skills=skills, categories=categories)


@admin_bp.route("/skills/<int:skill_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_skill(skill_id):
    skill = Skill.query.get_or_404(skill_id)
    db.session.delete(skill)
    db.session.commit()
    flash("Skill deleted.", "info")
    return redirect(url_for("admin.skills"))


@admin_bp.route("/skills/<int:skill_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def edit_skill(skill_id):
    skill = Skill.query.get_or_404(skill_id)
    categories = Category.query.order_by(Category.name).all()
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if name:
            skill.name = name
            skill.category_id = request.form.get("category_id") or None
            db.session.commit()
            flash("Skill updated.", "success")
        else:
            flash("Skill name cannot be empty.", "warning")
        return redirect(url_for("admin.skills"))
    return render_template("admin/skill_form.html", skill=skill, categories=categories)


@admin_bp.route("/categories", methods=["GET", "POST"])
@login_required
@admin_required
def categories():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if name and not Category.query.filter(db.func.lower(Category.name) == name.lower()).first():
            db.session.add(Category(
                name=name,
                description=request.form.get("description", "").strip(),
                icon=request.form.get("icon", "briefcase").strip() or "briefcase",
            ))
            db.session.commit()
            flash("Category added.", "success")
        return redirect(url_for("admin.categories"))
    categories = Category.query.order_by(Category.name).all()
    return render_template("admin/categories.html", categories=categories)


@admin_bp.route("/categories/<int:category_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def edit_category(category_id):
    category = Category.query.get_or_404(category_id)
    if request.method == "POST":
        category.name = request.form.get("name", "").strip() or category.name
        category.description = request.form.get("description", "").strip()
        category.icon = request.form.get("icon", category.icon).strip() or "briefcase"
        db.session.commit()
        flash("Category updated.", "success")
        return redirect(url_for("admin.categories"))
    return render_template("admin/category_form.html", category=category)


@admin_bp.route("/categories/<int:category_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_category(category_id):
    category = Category.query.get_or_404(category_id)
    db.session.delete(category)
    db.session.commit()
    flash("Category deleted.", "info")
    return redirect(url_for("admin.categories"))


# ---------------------------------------------------------------------------
# Certificates, assessments, reviews
# ---------------------------------------------------------------------------
@admin_bp.route("/certificates")
@login_required
@admin_required
def certificates():
    certificates = Certificate.query.order_by(Certificate.created_at.desc()).all()
    return render_template("admin/certificates.html", certificates=certificates)


@admin_bp.route("/certificates/<int:cert_id>/verify", methods=["POST"])
@login_required
@admin_required
def verify_certificate(cert_id):
    cert = Certificate.query.get_or_404(cert_id)
    cert.verified = not cert.verified
    db.session.commit()
    flash("Certificate verification updated.", "success")
    return redirect(url_for("admin.certificates"))


@admin_bp.route("/certificates/<int:cert_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_certificate(cert_id):
    cert = Certificate.query.get_or_404(cert_id)
    db.session.delete(cert)
    db.session.commit()
    flash("Certificate deleted.", "info")
    return redirect(url_for("admin.certificates"))


@admin_bp.route("/certificates/add", methods=["GET", "POST"])
@login_required
@admin_required
def add_certificate():
    students = StudentProfile.query.join(User).order_by(User.name).all()
    if request.method == "POST":
        student_id = request.form.get("student_id", type=int)
        title = request.form.get("title", "").strip()
        if not student_id or not title:
            flash("Student and title are required.", "danger")
            return render_template("admin/certificate_form.html", students=students)
        issue = request.form.get("issue_date", "").strip()
        cert = Certificate(
            student_id=student_id,
            title=title,
            organization=request.form.get("organization", "").strip(),
            issue_date=datetime.strptime(issue, "%Y-%m-%d").date() if issue else None,
            credential_id=request.form.get("credential_id", "").strip(),
            verification_url=request.form.get("verification_url", "").strip(),
            verified=request.form.get("verified") == "on",
        )
        db.session.add(cert)
        db.session.commit()
        flash("Certificate created.", "success")
        return redirect(url_for("admin.certificates"))
    return render_template("admin/certificate_form.html", students=students)


@admin_bp.route("/certificates/<int:cert_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def edit_certificate(cert_id):
    cert = Certificate.query.get_or_404(cert_id)
    students = StudentProfile.query.join(User).order_by(User.name).all()
    if request.method == "POST":
        cert.student_id = request.form.get("student_id", type=int) or cert.student_id
        cert.title = request.form.get("title", "").strip() or cert.title
        cert.organization = request.form.get("organization", "").strip()
        issue = request.form.get("issue_date", "").strip()
        cert.issue_date = datetime.strptime(issue, "%Y-%m-%d").date() if issue else None
        cert.credential_id = request.form.get("credential_id", "").strip()
        cert.verification_url = request.form.get("verification_url", "").strip()
        cert.verified = request.form.get("verified") == "on"
        db.session.commit()
        flash("Certificate updated.", "success")
        return redirect(url_for("admin.certificates"))
    return render_template("admin/certificate_form.html", cert=cert, students=students)


@admin_bp.route("/reviews")
@login_required
@admin_required
def reviews():
    reviews = Review.query.order_by(Review.created_at.desc()).all()
    return render_template("admin/reviews.html", reviews=reviews)


@admin_bp.route("/reviews/<int:review_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_review(review_id):
    review = Review.query.get_or_404(review_id)
    db.session.delete(review)
    db.session.commit()
    flash("Review removed.", "info")
    return redirect(url_for("admin.reviews"))


@admin_bp.route("/reviews/add", methods=["GET", "POST"])
@login_required
@admin_required
def add_review():
    projects = Project.query.order_by(Project.title).all()
    users = User.query.order_by(User.name).all()
    if request.method == "POST":
        project_id = request.form.get("project_id", type=int)
        reviewer_id = request.form.get("reviewer_id", type=int)
        reviewed_user_id = request.form.get("reviewed_user_id", type=int)
        rating = request.form.get("rating", 5, type=int)
        if not project_id or not reviewer_id or not reviewed_user_id:
            flash("Project, reviewer and reviewed user are required.", "danger")
            return render_template("admin/review_form.html", projects=projects, users=users)
        review = Review(
            project_id=project_id,
            reviewer_id=reviewer_id,
            reviewed_user_id=reviewed_user_id,
            rating=rating,
            review=request.form.get("review", "").strip(),
        )
        db.session.add(review)
        db.session.commit()
        flash("Review created.", "success")
        return redirect(url_for("admin.reviews"))
    return render_template("admin/review_form.html", projects=projects, users=users)


@admin_bp.route("/reviews/<int:review_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def edit_review(review_id):
    review = Review.query.get_or_404(review_id)
    projects = Project.query.order_by(Project.title).all()
    users = User.query.order_by(User.name).all()
    if request.method == "POST":
        review.project_id = request.form.get("project_id", type=int) or review.project_id
        review.reviewer_id = request.form.get("reviewer_id", type=int) or review.reviewer_id
        review.reviewed_user_id = request.form.get("reviewed_user_id", type=int) or review.reviewed_user_id
        review.rating = request.form.get("rating", 5, type=int)
        review.review = request.form.get("review", "").strip()
        db.session.commit()
        flash("Review updated.", "success")
        return redirect(url_for("admin.reviews"))
    return render_template("admin/review_form.html", review=review, projects=projects, users=users)


# ---------------------------------------------------------------------------
# Messages
# ---------------------------------------------------------------------------
@admin_bp.route("/messages")
@login_required
@admin_required
def messages():
    messages = Message.query.order_by(Message.created_at.desc()).limit(200).all()
    return render_template("admin/messages.html", messages=messages)


@admin_bp.route("/messages/<int:message_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_message(message_id):
    message = Message.query.get_or_404(message_id)
    db.session.delete(message)
    db.session.commit()
    flash("Message deleted.", "info")
    return redirect(url_for("admin.messages"))


# ---------------------------------------------------------------------------
# Milestones
# ---------------------------------------------------------------------------
@admin_bp.route("/milestones")
@login_required
@admin_required
def milestones():
    milestones = Milestone.query.order_by(Milestone.created_at.desc()).all()
    return render_template("admin/milestones.html", milestones=milestones)


@admin_bp.route("/milestones/<int:milestone_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def edit_milestone(milestone_id):
    milestone = Milestone.query.get_or_404(milestone_id)
    if request.method == "POST":
        milestone.title = request.form.get("title", "").strip() or milestone.title
        milestone.description = request.form.get("description", "").strip()
        milestone.amount = request.form.get("amount", 0, type=float) or 0
        milestone.status = request.form.get("status", milestone.status)
        milestone.payment_status = request.form.get("payment_status", milestone.payment_status)
        deadline = request.form.get("deadline", "").strip()
        milestone.deadline = datetime.strptime(deadline, "%Y-%m-%d").date() if deadline else None
        db.session.commit()
        flash("Milestone updated.", "success")
        return redirect(url_for("admin.milestones"))
    return render_template("admin/milestone_form.html", milestone=milestone)


@admin_bp.route("/milestones/<int:milestone_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_milestone(milestone_id):
    milestone = Milestone.query.get_or_404(milestone_id)
    db.session.delete(milestone)
    db.session.commit()
    flash("Milestone deleted.", "info")
    return redirect(url_for("admin.milestones"))


@admin_bp.route("/milestones/add", methods=["GET", "POST"])
@login_required
@admin_required
def add_milestone():
    projects = Project.query.order_by(Project.title).all()
    if request.method == "POST":
        project_id = request.form.get("project_id", type=int)
        title = request.form.get("title", "").strip()
        if not project_id or not title:
            flash("Project and title are required.", "danger")
            return render_template("admin/milestone_form.html", projects=projects)
        deadline = request.form.get("deadline", "").strip()
        milestone = Milestone(
            project_id=project_id,
            title=title,
            description=request.form.get("description", "").strip(),
            amount=request.form.get("amount", 0, type=float) or 0,
            status=request.form.get("status", "pending"),
            payment_status=request.form.get("payment_status", "unpaid"),
            deadline=datetime.strptime(deadline, "%Y-%m-%d").date() if deadline else None,
        )
        db.session.add(milestone)
        db.session.commit()
        flash("Milestone created.", "success")
        return redirect(url_for("admin.milestones"))
    return render_template("admin/milestone_form.html", projects=projects)


# ---------------------------------------------------------------------------
# Payments & withdrawals
# ---------------------------------------------------------------------------
@admin_bp.route("/payments")
@login_required
@admin_required
def payments():
    payments = Payment.query.order_by(Payment.created_at.desc()).all()
    total = db.session.query(func.coalesce(func.sum(Payment.amount), 0)).filter(
        Payment.status == "paid"
    ).scalar() or 0
    fees = db.session.query(func.coalesce(func.sum(Payment.platform_fee), 0)).filter(
        Payment.status == "paid"
    ).scalar() or 0
    return render_template(
        "admin/payments.html",
        payments=payments,
        total=float(total or 0),
        fees=float(fees or 0),
    )


@admin_bp.route("/payments/<int:payment_id>/status", methods=["POST"])
@login_required
@admin_required
def payment_status(payment_id):
    payment = Payment.query.get_or_404(payment_id)
    payment.status = request.form.get("status", payment.status)
    db.session.commit()
    flash("Payment status updated.", "success")
    return redirect(url_for("admin.payments"))


@admin_bp.route("/payments/<int:payment_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_payment(payment_id):
    payment = Payment.query.get_or_404(payment_id)
    db.session.delete(payment)
    db.session.commit()
    flash("Payment deleted.", "info")
    return redirect(url_for("admin.payments"))


@admin_bp.route("/payments/add", methods=["GET", "POST"])
@login_required
@admin_required
def add_payment():
    projects = Project.query.order_by(Project.title).all()
    clients = ClientProfile.query.join(User).order_by(User.name).all()
    students = StudentProfile.query.join(User).order_by(User.name).all()
    if request.method == "POST":
        project_id = request.form.get("project_id", type=int)
        client_id = request.form.get("client_id", type=int)
        student_id = request.form.get("student_id", type=int)
        amount = request.form.get("amount", 0, type=float) or 0
        if not project_id or not client_id or not student_id or amount <= 0:
            flash("Project, client, student and a positive amount are required.", "danger")
            return render_template("admin/payment_form.html", projects=projects, clients=clients, students=students)
        fee = round(float(amount) * 0.10, 2)
        payment = Payment(
            project_id=project_id,
            client_id=client_id,
            student_id=student_id,
            amount=amount,
            platform_fee=fee,
            student_amount=round(float(amount) - fee, 2),
            status=request.form.get("status", "pending"),
            payment_method=request.form.get("payment_method", "Platform Balance").strip() or "Platform Balance",
            transaction_reference=request.form.get("transaction_reference", "").strip(),
        )
        db.session.add(payment)
        db.session.commit()
        flash("Payment created.", "success")
        return redirect(url_for("admin.payments"))
    return render_template("admin/payment_form.html", projects=projects, clients=clients, students=students)


@admin_bp.route("/payments/<int:payment_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def edit_payment(payment_id):
    payment = Payment.query.get_or_404(payment_id)
    projects = Project.query.order_by(Project.title).all()
    clients = ClientProfile.query.join(User).order_by(User.name).all()
    students = StudentProfile.query.join(User).order_by(User.name).all()
    if request.method == "POST":
        payment.project_id = request.form.get("project_id", type=int) or payment.project_id
        payment.client_id = request.form.get("client_id", type=int) or payment.client_id
        payment.student_id = request.form.get("student_id", type=int) or payment.student_id
        amount = request.form.get("amount", 0, type=float) or 0
        payment.amount = amount
        payment.platform_fee = round(float(amount) * 0.10, 2)
        payment.student_amount = round(float(amount) - float(payment.platform_fee), 2)
        payment.status = request.form.get("status", payment.status)
        payment.payment_method = request.form.get("payment_method", payment.payment_method).strip() or "Platform Balance"
        payment.transaction_reference = request.form.get("transaction_reference", "").strip()
        db.session.commit()
        flash("Payment updated.", "success")
        return redirect(url_for("admin.payments"))
    return render_template("admin/payment_form.html", payment=payment, projects=projects, clients=clients, students=students)


@admin_bp.route("/withdrawals")
@login_required
@admin_required
def withdrawals():
    withdrawals = Withdrawal.query.order_by(Withdrawal.created_at.desc()).all()
    return render_template("admin/withdrawals.html", withdrawals=withdrawals)


@admin_bp.route("/withdrawals/<int:withdrawal_id>/status", methods=["POST"])
@login_required
@admin_required
def withdrawal_status(withdrawal_id):
    w = Withdrawal.query.get_or_404(withdrawal_id)
    w.status = request.form.get("status", w.status)
    db.session.commit()
    flash("Withdrawal status updated.", "success")
    return redirect(url_for("admin.withdrawals"))


@admin_bp.route("/withdrawals/<int:withdrawal_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_withdrawal(withdrawal_id):
    w = Withdrawal.query.get_or_404(withdrawal_id)
    db.session.delete(w)
    db.session.commit()
    flash("Withdrawal deleted.", "info")
    return redirect(url_for("admin.withdrawals"))


@admin_bp.route("/withdrawals/add", methods=["GET", "POST"])
@login_required
@admin_required
def add_withdrawal():
    students = StudentProfile.query.join(User).order_by(User.name).all()
    if request.method == "POST":
        student_id = request.form.get("student_id", type=int)
        amount = request.form.get("amount", 0, type=float) or 0
        if not student_id or amount <= 0:
            flash("Student and a positive amount are required.", "danger")
            return render_template("admin/withdrawal_form.html", students=students)
        w = Withdrawal(
            student_id=student_id,
            amount=amount,
            method=request.form.get("method", "Bank Transfer").strip() or "Bank Transfer",
            account_details=request.form.get("account_details", "").strip(),
            status=request.form.get("status", "pending"),
        )
        db.session.add(w)
        db.session.commit()
        flash("Withdrawal created.", "success")
        return redirect(url_for("admin.withdrawals"))
    return render_template("admin/withdrawal_form.html", students=students)


@admin_bp.route("/withdrawals/<int:withdrawal_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def edit_withdrawal(withdrawal_id):
    w = Withdrawal.query.get_or_404(withdrawal_id)
    students = StudentProfile.query.join(User).order_by(User.name).all()
    if request.method == "POST":
        w.student_id = request.form.get("student_id", type=int) or w.student_id
        w.amount = request.form.get("amount", 0, type=float) or 0
        w.method = request.form.get("method", w.method).strip() or "Bank Transfer"
        w.account_details = request.form.get("account_details", "").strip()
        w.status = request.form.get("status", w.status)
        db.session.commit()
        flash("Withdrawal updated.", "success")
        return redirect(url_for("admin.withdrawals"))
    return render_template("admin/withdrawal_form.html", withdrawal=w, students=students)


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------
@admin_bp.route("/notifications", methods=["GET", "POST"])
@login_required
@admin_required
def notifications():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        message = request.form.get("message", "").strip()
        target = request.form.get("target", "all")
        if title and message:
            if target == "all":
                users = User.query.all()
            elif target == "students":
                users = User.query.filter_by(role="student").all()
            elif target == "clients":
                users = User.query.filter_by(role="client").all()
            else:
                users = User.query.all()
            for u in users:
                notify(u.id, title, message, "admin")
            db.session.commit()
            flash(f"Notification sent to {len(users)} users.", "success")
        return redirect(url_for("admin.notifications"))
    notifications = Notification.query.order_by(Notification.created_at.desc()).limit(50).all()
    return render_template("admin/notifications.html", notifications=notifications)


@admin_bp.route("/notifications/<int:notification_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_notification(notification_id):
    n = Notification.query.get_or_404(notification_id)
    db.session.delete(n)
    db.session.commit()
    flash("Notification deleted.", "info")
    return redirect(url_for("admin.notifications"))


@admin_bp.route("/notifications/<int:notification_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def edit_notification(notification_id):
    n = Notification.query.get_or_404(notification_id)
    users = User.query.order_by(User.name).all()
    if request.method == "POST":
        n.user_id = request.form.get("user_id", type=int) or n.user_id
        n.title = request.form.get("title", "").strip() or n.title
        n.message = request.form.get("message", "").strip()
        n.notification_type = request.form.get("notification_type", n.notification_type).strip() or "general"
        n.link = request.form.get("link", "").strip()
        n.is_read = request.form.get("is_read") == "on"
        db.session.commit()
        flash("Notification updated.", "success")
        return redirect(url_for("admin.notifications"))
    return render_template("admin/notification_form.html", notification=n, users=users)


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------
@admin_bp.route("/reports")
@login_required
@admin_required
def reports():
    total_users = User.query.count()
    total_students = User.query.filter_by(role="student").count()
    total_clients = User.query.filter_by(role="client").count()
    total_projects = Project.query.count()
    open_projects = Project.query.filter_by(status="open").count()
    completed_projects = Project.query.filter_by(status="completed").count()
    total_payments = db.session.query(
        func.coalesce(func.sum(Payment.amount), 0)
    ).filter(Payment.status == "paid").scalar() or 0
    total_fees = db.session.query(
        func.coalesce(func.sum(Payment.platform_fee), 0)
    ).filter(Payment.status == "paid").scalar() or 0
    total_reviews = Review.query.count()
    return render_template(
        "admin/reports.html",
        total_users=total_users,
        total_students=total_students,
        total_clients=total_clients,
        total_projects=total_projects,
        open_projects=open_projects,
        completed_projects=completed_projects,
        total_payments=float(total_payments or 0),
        total_fees=float(total_fees or 0),
        total_reviews=total_reviews,
    )

# ---------------------------------------------------------------------------
# Site settings (logo)
# ---------------------------------------------------------------------------
@admin_bp.route("/settings/logo", methods=["GET", "POST"])
@login_required
@admin_required
def site_logo():
    current_logo = SiteSetting.get("logo", "")
    if request.method == "POST":
        # Reset to default logo
        if request.form.get("remove_logo") == "on":
            SiteSetting.set("logo", "")
            flash("Logo reset to default.", "success")
            return redirect(url_for("admin.site_logo"))
        upload = request.files.get("logo")
        if upload and upload.filename:
            path = save_upload(upload, subfolder="logos")
            if path:
                SiteSetting.set("logo", path)
                flash("Logo updated.", "success")
            else:
                flash("Invalid image file. Allowed: png, jpg, jpeg, gif, webp, svg, bmp.", "warning")
        else:
            flash("No file selected.", "warning")
        return redirect(url_for("admin.site_logo"))
    return render_template("admin/logo_form.html", current_logo=current_logo)


@admin_bp.route("/settings/site-name", methods=["GET", "POST"])
@login_required
@admin_required
def site_name():
    """Allow the admin to change the website name shown across the site."""
    current_name = SiteSetting.get("site_name", "")
    if not current_name:
        current_name = current_app.config["PLATFORM_NAME"]
    if request.method == "POST":
        new_name = request.form.get("site_name", "").strip()
        if not new_name:
            flash("Website name cannot be empty.", "warning")
        else:
            SiteSetting.set("site_name", new_name)
            flash("Website name updated.", "success")
        return redirect(url_for("admin.site_name"))
    return render_template("admin/site_name_form.html", current_name=current_name)

@admin_bp.route("/settings/contact", methods=["GET", "POST"])
@login_required
@admin_required
def contact_info():
    """Allow the admin to edit the contact details shown on the Contact Us page."""
    current = {
        "email": SiteSetting.get("contact_email", "support@skillbridge.test"),
        "phone": SiteSetting.get("contact_phone", "+1 (555) 000-0000"),
        "address": SiteSetting.get(
            "contact_address", "123 University Ave, Innovation City"
        ),
    }
    if request.method == "POST":
        SiteSetting.set("contact_email", request.form.get("contact_email", "").strip())
        SiteSetting.set("contact_phone", request.form.get("contact_phone", "").strip())
        SiteSetting.set("contact_address", request.form.get("contact_address", "").strip())
        flash("Contact information updated.", "success")
        return redirect(url_for("admin.contact_info"))
    return render_template("admin/contact_form.html", current=current)

@admin_bp.route("/settings/about", methods=["GET", "POST"])
@login_required
@admin_required
def about_info():
    """Allow the admin to edit the About Us page content."""
    current = {
        "mission": SiteSetting.get(
            "about_mission",
            f"{current_app.config['PLATFORM_NAME']} connects university and college students with "
            "real-world freelance projects. We believe students learn best by "
            "doing — and that businesses of every size benefit from fresh, "
            "affordable, talented help.",
        ),
        "offers": SiteSetting.get(
            "about_offers",
            "Professional student profiles with skills, portfolios and certificates|"
            "A marketplace of freelance projects posted by clients|"
            "A complete proposal, hiring and workspace flow|"
            "Skill assessments and verified badges to build trust|"
            "A built-in resume builder to launch careers",
        ),
    }
    if request.method == "POST":
        SiteSetting.set("about_mission", request.form.get("about_mission", "").strip())
        SiteSetting.set("about_offers", request.form.get("about_offers", "").strip())
        flash("About Us page updated.", "success")
        return redirect(url_for("admin.about_info"))
    return render_template("admin/about_form.html", current=current)


# ---------------------------------------------------------------------------
# Banners
# ---------------------------------------------------------------------------
def _handle_banner_image(banner):
    """Process an optional uploaded banner image (or clear request)."""
    # Clear image if requested
    if request.form.get("remove_image") == "on":
        banner.image = ""
        return
    upload = request.files.get("image")
    if upload and upload.filename:
        path = save_upload(upload, subfolder="banners")
        if path:
            banner.image = path


@admin_bp.route("/banners", methods=["GET", "POST"])
@login_required
@admin_required
def banners():
    if request.method == "POST":
        banner = Banner(
            title=request.form.get("title", "").strip(),
            message=request.form.get("message", "").strip(),
            link_url=request.form.get("link_url", "").strip(),
            link_text=request.form.get("link_text", "Learn more").strip() or "Learn more",
            background=request.form.get("background", "gold").strip() or "gold",
            is_active=request.form.get("is_active") == "on",
        )
        start = request.form.get("start_date", "").strip()
        end = request.form.get("end_date", "").strip()
        banner.start_date = datetime.strptime(start, "%Y-%m-%d").date() if start else None
        banner.end_date = datetime.strptime(end, "%Y-%m-%d").date() if end else None
        if banner.title and banner.message:
            _handle_banner_image(banner)
            db.session.add(banner)
            db.session.commit()
            flash("Banner created.", "success")
        else:
            flash("Title and message are required.", "warning")
        return redirect(url_for("admin.banners"))
    banners = Banner.query.order_by(Banner.created_at.desc()).all()
    return render_template("admin/banners.html", banners=banners)


@admin_bp.route("/banners/<int:banner_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def edit_banner(banner_id):
    banner = Banner.query.get_or_404(banner_id)
    if request.method == "POST":
        banner.title = request.form.get("title", "").strip() or banner.title
        banner.message = request.form.get("message", "").strip() or banner.message
        banner.link_url = request.form.get("link_url", "").strip()
        banner.link_text = request.form.get("link_text", "Learn more").strip() or "Learn more"
        banner.background = request.form.get("background", "gold").strip() or "gold"
        banner.is_active = request.form.get("is_active") == "on"
        start = request.form.get("start_date", "").strip()
        end = request.form.get("end_date", "").strip()
        banner.start_date = datetime.strptime(start, "%Y-%m-%d").date() if start else None
        banner.end_date = datetime.strptime(end, "%Y-%m-%d").date() if end else None
        _handle_banner_image(banner)
        db.session.commit()
        flash("Banner updated.", "success")
        return redirect(url_for("admin.banners"))
    return render_template("admin/banner_form.html", banner=banner)


@admin_bp.route("/banners/<int:banner_id>/toggle", methods=["POST"])
@login_required
@admin_required
def toggle_banner(banner_id):
    banner = Banner.query.get_or_404(banner_id)
    banner.is_active = not banner.is_active
    db.session.commit()
    flash(f"Banner is now {'active' if banner.is_active else 'inactive'}.", "success")
    return redirect(url_for("admin.banners"))


@admin_bp.route("/banners/<int:banner_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_banner(banner_id):
    banner = Banner.query.get_or_404(banner_id)
    db.session.delete(banner)
    db.session.commit()
    flash("Banner deleted.", "info")
    return redirect(url_for("admin.banners"))
