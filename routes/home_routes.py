"""Home routes: landing page, about, contact."""
from flask import Blueprint, render_template, request, flash, current_app
from sqlalchemy import func, or_

from extensions import db
from models.student import StudentProfile
from models.project import Project
from models.category import Category
from models.skill import Skill
from models.review import Review
from models.user import User
from models.payment import Payment

home_bp = Blueprint("home", __name__, url_prefix="/")

FEATURED_SKILLS = [
    "Web Development", "Graphic Design", "UI/UX Design", "Content Writing",
    "Digital Marketing", "Video Editing", "Data Entry", "Data Analysis",
    "Mobile App Development", "Photography", "Translation", "SEO",
    "Social Media Management", "Tutoring",
]


@home_bp.route("/")
def index():
    categories = Category.query.order_by(Category.name).all()

    students = (
        StudentProfile.query.join(User, User.id == StudentProfile.user_id)
        .filter(User.status == "active")
        .order_by(StudentProfile.created_at.desc())
        .limit(6)
        .all()
    )
    projects = (
        Project.query.filter_by(status="open")
        .order_by(Project.created_at.desc())
        .limit(6)
        .all()
    )

    total_students = User.query.filter_by(role="student").count()
    active_projects = Project.query.filter(Project.status.in_(["open", "in_progress"])).count()
    completed_projects = Project.query.filter_by(status="completed").count()
    verified_skills = Skill.query.count()
    total_earnings = db.session.query(func.coalesce(func.sum(Payment.student_amount), 0)).scalar()

    testimonials = Review.query.order_by(Review.created_at.desc()).limit(3).all()

    return render_template(
        "index.html",
        categories=categories,
        featured_skills=FEATURED_SKILLS,
        students=students,
        projects=projects,
        stats={
            "students": total_students,
            "active_projects": active_projects,
            "completed_projects": completed_projects,
            "verified_skills": verified_skills,
            "earnings": float(total_earnings or 0),
        },
        testimonials=testimonials,
    )


@home_bp.route("/about")
def about():
    from models.site_setting import SiteSetting
    mission = SiteSetting.get(
        "about_mission",
        f"{current_app.config["PLATFORM_NAME"]} connects university and college students with "
        "real-world freelance projects. We believe students learn best by "
        "doing \u2014 and that businesses of every size benefit from fresh, "
        "affordable, talented help.",
    )
    offers_raw = SiteSetting.get(
        "about_offers",
        "Professional student profiles with skills, portfolios and certificates|"
        "A marketplace of freelance projects posted by clients|"
        "A complete proposal, hiring and workspace flow|"
        "Skill assessments and verified badges to build trust|"
        "A built-in resume builder to launch careers",
    )
    offers = [o.strip() for o in offers_raw.split("|") if o.strip()]
    return render_template("about.html", about_mission=mission, about_offers=offers)


@home_bp.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        message = request.form.get("message", "").strip()
        if not name or not email or not message:
            flash("Please fill all required fields.", "danger")
        else:
            # Demo: message is logged/notified to admins.
            admins = User.query.filter_by(role="admin").all()
            from utils import notify
            for admin in admins:
                notify(admin.id, "New Contact Message",
                       f"{name} ({email}) sent: {message[:200]}", "message")
            db.session.commit()
            flash("Thank you! Your message has been sent. We'll get back to you soon.", "success")
    return render_template("contact.html")


@home_bp.route("/search")
def global_search():
    """Global search across students and projects."""
    q = request.args.get("q", "").strip()
    student_results = []
    project_results = []
    if q:
        student_results = (
            StudentProfile.query.join(User)
            .filter(
                User.status == "active",
                or_(
                    User.name.ilike(f"%{q}%"),
                    StudentProfile.university.ilike(f"%{q}%"),
                    StudentProfile.bio.ilike(f"%{q}%"),
                ),
            )
            .limit(20)
            .all()
        )
        project_results = (
            Project.query.filter(
                Project.status.in_(["open", "in_progress"]),
                or_(Project.title.ilike(f"%{q}%"), Project.description.ilike(f"%{q}%")),
            )
            .limit(20)
            .all()
        )
    return render_template(
        "search.html",
        q=q,
        student_results=student_results,
        project_results=project_results,
    )