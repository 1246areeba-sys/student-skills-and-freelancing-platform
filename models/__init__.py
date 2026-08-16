"""Database models package.

Import every model here so that SQLAlchemy metadata is complete and
Flask-Migrate can autogenerate migrations for all tables.
"""
from models.user import User
from models.student import StudentProfile, StudentSkill
from models.client import ClientProfile
from models.category import Category
from models.skill import Skill
from models.portfolio import Portfolio
from models.project import Project, ProjectSkill, Hire
from models.proposal import Proposal
from models.message import Message
from models.milestone import Milestone
from models.payment import Payment, Withdrawal
from models.review import Review
from models.notification import Notification
from models.certificate import Certificate
from models.assessment import Assessment, AssessmentQuestion, AssessmentResult
from models.wishlist import Wishlist
from models.banner import Banner

__all__ = [
    "User",
    "StudentProfile",
    "StudentSkill",
    "ClientProfile",
    "Category",
    "Skill",
    "Portfolio",
    "Project",
    "ProjectSkill",
    "Hire",
    "Proposal",
    "Message",
    "Milestone",
    "Payment",
    "Withdrawal",
    "Review",
    "Notification",
    "Certificate",
    "Assessment",
    "AssessmentQuestion",
    "AssessmentResult",
    "Wishlist",
    "Banner",
]
