"""Seed script for SkillBridge.

Creates only the platform admin account. All other data (categories, skills,
students, clients, projects, assessments, etc.) is added by the admin through
the admin panel — no fake/demo data is inserted.

Run with:  flask seed
(or)       python seed.py
"""
from app import create_app
from config import Config
from extensions import db

from models.user import User
from models.student import StudentProfile, StudentSkill
from models.client import ClientProfile
from models.category import Category
from models.skill import Skill
from models.project import Project, ProjectSkill, Hire
from models.proposal import Proposal
from models.milestone import Milestone
from models.payment import Payment, Withdrawal
from models.review import Review
from models.notification import Notification
from models.message import Message
from models.certificate import Certificate
from models.portfolio import Portfolio
from models.wishlist import Wishlist
from models.assessment import Assessment, AssessmentQuestion, AssessmentResult


ADMIN_EMAIL = "admin@skillbridge.com"
ADMIN_NAME = "Platform Admin"
ADMIN_PASSWORD = "admin123"


def _clear():
    """Remove all existing rows so the seed can be re-run safely.

    Wrapped in try/except so tables that don't exist yet (e.g. before the
    first migration) are simply skipped.
    """
    # Order matters because of foreign keys.
    for model in (
        AssessmentResult, AssessmentQuestion, Assessment,
        Wishlist, Notification, Message, Review, Payment, Withdrawal,
        Milestone, Hire, Proposal, ProjectSkill, Project,
        Certificate, Portfolio, StudentSkill,
        StudentProfile, ClientProfile,
        Skill, Category, User,
    ):
        try:
            db.session.query(model).delete()
        except Exception:
            db.session.rollback()
    db.session.commit()


def seed_all():
    app = create_app(Config)
    with app.app_context():
        # Ensure all tables exist (works with SQLite fallback or after migrations).
        db.create_all()
        _clear()
        print("Cleared all existing data.")

        # ---------------------------------------------------------------
        # Admin only — all other data is added by the admin via the panel.
        # ---------------------------------------------------------------
        admin = User(
            email=ADMIN_EMAIL,
            name=ADMIN_NAME,
            role="admin",
            phone="+1-555-0001",
            city="San Francisco",
        )
        admin.set_password(ADMIN_PASSWORD)
        db.session.add(admin)
        db.session.commit()
        print("Created admin user.")

        print("Seed complete! Admin account:")
        print(f"  Admin : {ADMIN_EMAIL} / {ADMIN_PASSWORD}")


if __name__ == "__main__":
    seed_all()
