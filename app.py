from datetime import datetime
"""SkillBridge — Student Skills Freelancing Platform.

Application factory. Creates the Flask app, binds extensions, registers
blueprints, Jinja context processors and error handlers.
"""
import os
import uuid
from flask import Flask, render_template, request, session
from werkzeug.exceptions import HTTPException

from config import Config
from extensions import db, migrate, login_manager
import utils


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Bind extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # Register Jinja helpers
    utils.register_template_filters(app)
    app.jinja_env.globals.update(
        platform_name=app.config["PLATFORM_NAME"],
        platform_tagline=app.config["PLATFORM_TAGLINE"],
        platform_fee=app.config["PLATFORM_FEE_PERCENT"],
        now=datetime.utcnow,
    )

    # Ensure upload folders exist
    for sub in ["profiles", "portfolio", "certificates", "general", "messages", "banners"]:
        folder = os.path.join(app.config["UPLOAD_FOLDER"], sub)
        os.makedirs(folder, exist_ok=True)

    # ---- Register blueprints ----
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

    app.register_blueprint(auth_bp)
    app.register_blueprint(home_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(client_bp)
    app.register_blueprint(project_bp)
    app.register_blueprint(proposal_bp)
    app.register_blueprint(message_bp)
    app.register_blueprint(payment_bp)
    app.register_blueprint(notification_bp)
    app.register_blueprint(review_bp)
    app.register_blueprint(assessment_bp)
    app.register_blueprint(admin_bp)

    # ---- Global context (nav notifications + unread messages) ----
    @app.context_processor
    def inject_globals():
        from flask_login import current_user
        from models.notification import Notification
        from models.message import Message
        from models.banner import Banner

        unread_notifications = 0
        unread_messages = 0
        if current_user.is_authenticated:
            unread_notifications = Notification.query.filter_by(
                user_id=current_user.id, is_read=False
            ).count()
            unread_messages = Message.query.filter_by(
                receiver_id=current_user.id, is_read=False
            ).count()
        visible_banners = []
        try:
            visible_banners = [
                b for b in Banner.query.filter_by(is_active=True).all()
                if b.is_currently_visible
            ]
        except Exception:
            visible_banners = []
        return {
            "unread_notifications": unread_notifications,
            "unread_messages": unread_messages,
            "site_banners": visible_banners,
        }

    # ---- CSRF token helpers for non-WTF forms ----
    @app.before_request
    def csrf_token_for_ajax():
        if not session.get("_csrf_token"):
            session["_csrf_token"] = uuid.uuid4().hex

    @app.context_processor
    def inject_csrf():
        return {"csrf_token": session.get("_csrf_token", "")}

    # ---- Error handlers ----
    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template("errors/500.html"), 500

    @app.errorhandler(HTTPException)
    def http_error(e):
        if e.code == 403:
            return render_template("errors/403.html"), 403
        if e.code == 404:
            return render_template("errors/404.html"), 404
        return render_template("errors/500.html"), 500

    # ---- CLI commands ----
    @app.cli.command("seed")
    def seed_command():
        """Seed the database with demo data."""
        from seed import seed_all
        seed_all()
        print("Database seeded successfully.")

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=app.config["DEBUG"])