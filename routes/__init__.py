"""Route blueprints package."""
from routes.auth_routes import auth_bp
from routes.home_routes import home_bp
from routes.student_routes import student_bp
from routes.client_routes import client_bp
from routes.project_routes import project_bp
from routes.proposal_routes import proposal_bp
from routes.message_routes import message_bp
from routes.payment_routes import payment_bp
from routes.notification_routes import notification_bp
from routes.review_routes import review_bp
from routes.assessment_routes import assessment_bp
from routes.admin_routes import admin_bp

__all__ = [
    "auth_bp",
    "home_bp",
    "student_bp",
    "client_bp",
    "project_bp",
    "proposal_bp",
    "message_bp",
    "payment_bp",
    "notification_bp",
    "review_bp",
    "assessment_bp",
    "admin_bp",
]