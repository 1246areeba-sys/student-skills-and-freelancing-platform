from datetime import datetime

"""SkillBridge - Student Skills Freelancing Platform.

Application factory. Creates the Flask app, binds extensions, registers
blueprints, Jinja context processors and error handlers.
"""
import os
import sys
import uuid
from flask import Flask, render_template, request, session, redirect, url_for
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

    @login_manager.user_loader
    def load_user(user_id):
        from models.user import User
        try:
            return User.query.get(int(user_id))
        except (ValueError, TypeError):
            return None

    # Register Jinja helpers
    utils.register_template_filters(app)
    app.jinja_env.globals.update(
        platform_tagline=app.config["PLATFORM_TAGLINE"],
        platform_fee=app.config["PLATFORM_FEE_PERCENT"],
        now=datetime.utcnow,
    )

    # Ensure upload folders exist
    for sub in ["profiles", "portfolio", "certificates", "general", "messages", "banners", "logos"]:
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

    # ---- Ensure database tables exist (self-healing for fresh deploys) ----
    # This runs at import time (app = create_app() at module level). If it were
    # to raise, the WSGI server (gunicorn) could not import `app:app` and EVERY
    # request would return 500. So we guard it: a transient DB problem must never
    # take the whole application down at startup.
    try:
        import models  # noqa: F401  (importing registers all models on metadata)
        with app.app_context():
            db.create_all()
            # Enable WAL journaling for SQLite so that the 15s notification polling
            # (readers) can run concurrently with writes instead of hitting
            # "database is locked". This is the single most effective fix for the
            # intermittent 500 errors seen under concurrent load.
            try:
                from sqlalchemy import text
                db.session.execute(text("PRAGMA journal_mode=WAL;"))
                db.session.execute(text("PRAGMA busy_timeout=30000;"))
                db.session.commit()
            except Exception:
                pass
    except Exception as _db_err:
        # Log but do NOT crash the app. The site can still serve pages; the
        # first DB-backed request will surface the real error for diagnosis.
        print("WARNING: database initialization failed at startup: %s" % _db_err,
              file=sys.stderr)

    # ---- Global context (nav notifications + unread messages) ----
    @app.context_processor
    def inject_globals():
        from flask_login import current_user
        from models.notification import Notification
        from models.message import Message
        from models.banner import Banner
        from models.site_setting import SiteSetting

        unread_notifications = 0
        unread_messages = 0
        if current_user.is_authenticated:
            try:
                unread_notifications = Notification.query.filter_by(
                    user_id=current_user.id, is_read=False
                ).count()
                unread_messages = Message.query.filter_by(
                    receiver_id=current_user.id, is_read=False
                ).count()
            except Exception:
                # Never let a transient DB hiccup (e.g. "database is locked")
                # crash every page render. Degrade gracefully to zero badges.
                unread_notifications = 0
                unread_messages = 0
        visible_banners = []
        try:
            visible_banners = [
                b for b in Banner.query.filter_by(is_active=True).all()
                if b.is_currently_visible
            ]
        except Exception:
            visible_banners = []
        site_logo = ""
        try:
            site_logo = SiteSetting.get("logo", "")
        except Exception:
            site_logo = ""
        # Website name is editable from the admin panel; fall back to the
        # configured default if no custom name has been set yet.
        platform_name = app.config["PLATFORM_NAME"]
        try:
            platform_name = SiteSetting.get("site_name", app.config["PLATFORM_NAME"])
        except Exception:
            platform_name = app.config["PLATFORM_NAME"]
        # Contact details shown on the public Contact Us page (admin-editable).
        contact_email = "support@skillbridge.test"
        contact_phone = "+1 (555) 000-0000"
        contact_address = "123 University Ave, Innovation City"
        try:
            contact_email = SiteSetting.get("contact_email", contact_email)
            contact_phone = SiteSetting.get("contact_phone", contact_phone)
            contact_address = SiteSetting.get("contact_address", contact_address)
        except Exception:
            pass

        return {
            "unread_notifications": unread_notifications,
            "unread_messages": unread_messages,
            "site_banners": visible_banners,
            "site_logo": site_logo,
            "platform_name": platform_name,
            "contact_email": contact_email,
            "contact_phone": contact_phone,
            "contact_address": contact_address,
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
        # Always log the real exception so the root cause is diagnosable in the
        # server output instead of being swallowed by the generic error page.
        import traceback
        app.logger.error("500 error: %s\n%s", e, traceback.format_exc())
        # When debug is enabled (e.g. on a staging deploy) also surface the real
        # error in the browser so it can be diagnosed quickly.
        if app.config.get("DEBUG"):
            tb = traceback.format_exc()
            return (
                f"<pre style='padding:20px;white-space:pre-wrap;'>{tb}</pre>",
                500,
            )
        return render_template("errors/500.html"), 500

    @app.errorhandler(405)
    def method_not_allowed(e):
        # A GET (e.g. a page refresh, a link, or a browser prefetch) hitting a
        # POST-only endpoint should not show a misleading 500 page. Redirect
        # back to the previous page (or home) so the user can retry safely.
        if request.referrer and request.referrer.startswith(request.host_url):
            return redirect(request.referrer)
        return redirect(url_for("home.index"))

    @app.errorhandler(HTTPException)
    def http_error(e):
        # Only render the dedicated error pages for the statuses we actually
        # have templates for. Everything else (including 405, handled above,
        # and other 4xx) falls back to Flask's default behaviour instead of
        # being misreported as a server (500) error.
        if e.code == 403:
            return render_template("errors/403.html"), 403
        if e.code == 404:
            return render_template("errors/404.html"), 404
        return e

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
