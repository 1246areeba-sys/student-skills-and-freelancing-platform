"""Authentication routes: register, login, logout, forgot password."""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash

from extensions import db
from models.user import User
from models.student import StudentProfile
from models.client import ClientProfile
from utils import save_upload

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


def get_or_create_profile(user):
    """Create the role-specific profile if it does not exist yet."""
    if user.is_student and not user.student_profile:
        sp = StudentProfile(user_id=user.id)
        db.session.add(sp)
        db.session.commit()
    elif user.is_client and not user.client_profile:
        cp = ClientProfile(user_id=user.id)
        db.session.add(cp)
        db.session.commit()


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home.index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            if user.status == "suspended":
                flash("Your account has been suspended. Contact support.", "danger")
                return render_template("auth/login.html")
            login_user(user, remember=True)
            get_or_create_profile(user)
            flash(f"Welcome back, {user.name}!", "success")
            next_page = request.args.get("next")
            if user.is_admin:
                return redirect(next_page or url_for("admin.dashboard"))
            if user.is_student:
                return redirect(next_page or url_for("student.dashboard"))
            return redirect(next_page or url_for("client.dashboard"))
        flash("Invalid email or password.", "danger")

    return render_template("auth/login.html")


@auth_bp.route("/register/student", methods=["GET", "POST"])
def register_student():
    if current_user.is_authenticated:
        return redirect(url_for("home.index"))

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
        skills_input = request.form.get("skills", "").strip()
        picture = request.files.get("profile_picture")

        # Validation
        errors = []
        if not name or not email or not password:
            errors.append("Please fill all required fields.")
        if "@" not in email or "." not in email.split("@")[-1]:
            errors.append("Please enter a valid email address.")
        if len(password) < 8:
            errors.append("Password must contain at least 8 characters.")
        if password != confirm:
            errors.append("Passwords do not match.")
        if User.query.filter_by(email=email).first():
            errors.append("An account with this email already exists.")
        if university_email and User.query.filter_by(email=university_email).first():
            errors.append("An account with this university email already exists.")
        if not university:
            errors.append("University/College is required.")

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("auth/register_student.html")

        user = User(
            name=name,
            email=email,
            role="student",
            phone=phone,
            city=city,
        )
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
            student_id=student_id,
            university_email=university_email or email,
            verification_status="pending",
        )
        db.session.add(profile)
        db.session.flush()

        # Attach provided skills (comma separated) to the student
        from models.skill import Skill
        from models.student import StudentSkill
        for skill_name in [s.strip() for s in skills_input.split(",") if s.strip()]:
            skill = Skill.query.filter(db.func.lower(Skill.name) == skill_name.lower()).first()
            if not skill:
                skill = Skill(name=skill_name)
                db.session.add(skill)
                db.session.flush()
            db.session.add(StudentSkill(student_id=profile.id, skill_id=skill.id))

        db.session.commit()
        login_user(user)
        flash("Account created successfully! Welcome to SkillBridge.", "success")
        return redirect(url_for("student.dashboard"))

    return render_template("auth/register_student.html")


@auth_bp.route("/register/client", methods=["GET", "POST"])
def register_client():
    if current_user.is_authenticated:
        return redirect(url_for("home.index"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        company = request.form.get("company", "").strip()
        phone = request.form.get("phone", "").strip()
        city = request.form.get("city", "").strip()
        description = request.form.get("description", "").strip()
        picture = request.files.get("profile_picture")

        errors = []
        if not name or not email or not password:
            errors.append("Please fill all required fields.")
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
            return render_template("auth/register_client.html")

        user = User(
            name=name,
            email=email,
            role="client",
            phone=phone,
            city=city,
        )
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
        login_user(user)
        flash("Account created successfully! Welcome to SkillBridge.", "success")
        return redirect(url_for("client.dashboard"))

    return render_template("auth/register_client.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("home.index"))


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user = User.query.filter_by(email=email).first()
        if user:
            # Demo flow: reset password to a known value after confirmation.
            flash(
                "Password reset link sent (demo: use the reset form below to set a new password).",
                "success",
            )
            return render_template("auth/forgot_password.html", step="reset", email=email)
        flash("No account found with that email address.", "danger")

    return render_template("auth/forgot_password.html")


@auth_bp.route("/forgot-password/reset", methods=["POST"])
def reset_password():
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    confirm = request.form.get("confirm_password", "")
    user = User.query.filter_by(email=email).first()
    if not user:
        flash("No account found with that email address.", "danger")
        return redirect(url_for("auth.forgot_password"))
    if len(password) < 8:
        flash("Password must contain at least 8 characters.", "danger")
        return render_template("auth/forgot_password.html", step="reset", email=email)
    if password != confirm:
        flash("Passwords do not match.", "danger")
        return render_template("auth/forgot_password.html", step="reset", email=email)
    user.set_password(password)
    db.session.commit()
    flash("Password updated successfully. You can now log in.", "success")
    return redirect(url_for("auth.login"))