"""Shared helper utilities: file uploads, notifications, matching, formatting."""
import os
import uuid
from datetime import datetime, date
from functools import wraps
from werkzeug.utils import secure_filename

from flask import current_app, url_for, abort
from extensions import db
from flask_login import current_user


# ---------------------------------------------------------------------------
# File upload helpers
# ---------------------------------------------------------------------------
def allowed_file(filename, kind="image"):
    """Check a filename against the allowed extension set."""
    if not filename or "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    if kind == "image":
        return ext in current_app.config["ALLOWED_IMAGE_EXTENSIONS"]
    return ext in current_app.config["ALLOWED_FILE_EXTENSIONS"]


def save_upload(file_storage, subfolder="general"):
    """Securely save an uploaded file and return its relative URL path.

    Returns None if the upload is invalid.
    """
    if not file_storage or not file_storage.filename:
        return None
    if not allowed_file(file_storage.filename):
        return None

    original = secure_filename(file_storage.filename)
    ext = original.rsplit(".", 1)[1].lower() if "." in original else ""
    unique = f"{uuid.uuid4().hex}_{original}" if ext else f"{uuid.uuid4().hex}"
    if ext and not unique.endswith(f".{ext}"):
        unique = f"{unique}.{ext}"

    folder = os.path.join(current_app.config["UPLOAD_FOLDER"], subfolder)
    os.makedirs(folder, exist_ok=True)
    file_storage.save(os.path.join(folder, unique))
    return f"uploads/{subfolder}/{unique}"


# ---------------------------------------------------------------------------
# Authorization decorators
# ---------------------------------------------------------------------------
def admin_required(f):
    """Decorator that requires the current user to be an admin."""
    from functools import wraps

    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)

    return decorated


# ---------------------------------------------------------------------------
# Notification helper
# ---------------------------------------------------------------------------
def notify(user_id, title, message, notification_type="general", link=None):
    """Create a notification record for a user."""
    from models.notification import Notification
    n = Notification(
        user_id=user_id,
        title=title,
        message=message,
        notification_type=notification_type,
        link=link,
    )
    db.session.add(n)
    return n


# ---------------------------------------------------------------------------
# Smart matching engine (rule-based, transparent scoring)
# ---------------------------------------------------------------------------
def skill_match_percentage(student_skill_names, project_skill_names):
    """Compute a transparent skill-match percentage.

    Formula: 100 * (matched skills) / (required skills).
    If the project requires no skills, return 0 (nothing to match against).
    """
    required = {s.strip().lower() for s in project_skill_names if s and s.strip()}
    if not required:
        return 0
    owned = {s.strip().lower() for s in student_skill_names if s and s.strip()}
    matched = len(required & owned)
    return round((matched / len(required)) * 100)


def project_match_for_student(student, project):
    """Return a dict with match score and matched skills for a project."""
    student_skills = [s.skill.name for s in student.skills]
    project_skills = [ps.skill.name for ps in project.required_skills]
    score = skill_match_percentage(student_skills, project_skills)
    owned = {s.lower() for s in student_skills}
    matched = [name for name in project_skills if name.lower() in owned]
    return {"score": score, "matched": matched}


def student_match_for_project(project, student):
    """Return a dict with match score and matched skills for a student."""
    return project_match_for_student(student, project)


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------
def format_money(amount):
    """Format a number as currency (USD)."""
    if amount is None:
        amount = 0
    return f"${amount:,.2f}"


def days_remaining(deadline):
    """Return whole days remaining until a deadline (0 if passed)."""
    if not deadline:
        return 0
    if isinstance(deadline, datetime):
        deadline = deadline.date()
    delta = (deadline - date.today()).days
    return max(delta, 0)


def profile_completion_percentage(student):
    """Estimate profile completion for a student profile (0-100)."""
    checks = [
        bool(student.bio),
        bool(student.university),
        bool(student.education),
        bool(student.hourly_rate),
        bool(student.availability),
        bool(student.languages),
        bool(student.skills),
        bool(student.portfolios),
        bool(student.certificates),
        bool(student.user.profile_picture),
    ]
    return round((sum(checks) / len(checks)) * 100)


def register_template_filters(app):
    """Register Jinja filters used across templates."""
    app.jinja_env.filters["money"] = format_money
    app.jinja_env.filters["days_left"] = days_remaining
    app.jinja_env.filters["completion"] = profile_completion_percentage
    app.jinja_env.filters["match"] = skill_match_percentage
    app.jinja_env.filters["date"] = lambda d: d.strftime("%b %d, %Y") if d else "—"
    app.jinja_env.filters["datetime"] = lambda d: d.strftime("%b %d, %Y %I:%M %p") if d else "—"
    app.jinja_env.filters["timeago"] = timeago
    app.jinja_env.filters["star_rating"] = star_rating
    # Also expose as a global so templates can call star_rating(...) directly.
    app.jinja_env.globals["star_rating"] = star_rating


def timeago(dt):
    """Human friendly relative time."""
    if not dt:
        return "—"
    now = datetime.utcnow()
    diff = now - dt
    seconds = int(diff.total_seconds())
    if seconds < 60:
        return "just now"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes} min ago"
    hours = minutes // 60
    if hours < 24:
        return f"{hours} hr ago"
    days = hours // 24
    if days < 30:
        return f"{days} day{'s' if days > 1 else ''} ago"
    months = days // 30
    if months < 12:
        return f"{months} month{'s' if months > 1 else ''} ago"
    years = months // 12
    return f"{years} year{'s' if years > 1 else ''} ago"


def star_rating(rating):
    """Return a list of 5 star states for template rendering."""
    rating = round(rating or 0)
    return [i < rating for i in range(5)]
