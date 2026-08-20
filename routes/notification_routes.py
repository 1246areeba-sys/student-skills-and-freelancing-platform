"""Notification routes: list, mark read, mark all read, delete, and live poll."""
from flask import Blueprint, render_template, redirect, url_for, flash, jsonify, request
from flask_login import login_required, current_user

from extensions import db
from models.notification import Notification

notification_bp = Blueprint("notification", __name__, url_prefix="/notifications")


@notification_bp.route("/")
@login_required
def index():
    notifications = Notification.query.filter_by(
        user_id=current_user.id
    ).order_by(Notification.created_at.desc()).all()
    return render_template("notifications/index.html", notifications=notifications)


@notification_bp.route("/api/latest")
@login_required
def api_latest():
    """Return unread count and the most recent notifications for live polling."""
    since_id = request.args.get("since_id", type=int) or 0
    unread = Notification.query.filter_by(
        user_id=current_user.id, is_read=False
    ).count()
    latest = (
        Notification.query.filter_by(user_id=current_user.id)
        .order_by(Notification.created_at.desc())
        .limit(5)
        .all()
    )
    # Only the notifications newer than since_id are "new" for toasts.
    new_items = [
        {
            "id": n.id,
            "title": n.title,
            "message": n.message,
            "type": n.notification_type,
            "link": n.link,
        }
        for n in latest
        if n.id > since_id
    ]
    return jsonify(
        {
            "unread": unread,
            "latest": [
                {
                    "id": n.id,
                    "title": n.title,
                    "message": n.message,
                    "type": n.notification_type,
                    "link": n.link,
                }
                for n in latest
            ],
            "new": new_items,
        }
    )


@notification_bp.route("/mark-read/<int:notification_id>", methods=["POST"])
@login_required
def mark_read(notification_id):
    n = Notification.query.filter_by(
        id=notification_id, user_id=current_user.id
    ).first_or_404()
    n.is_read = True
    db.session.commit()
    flash("Notification marked as read.", "success")
    return redirect(url_for("notification.index"))


@notification_bp.route("/mark-all-read", methods=["POST"])
@login_required
def mark_all_read():
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update(
        {"is_read": True}
    )
    db.session.commit()
    flash("All notifications marked as read.", "success")
    return redirect(url_for("notification.index"))


@notification_bp.route("/delete/<int:notification_id>", methods=["POST"])
@login_required
def delete(notification_id):
    n = Notification.query.filter_by(
        id=notification_id, user_id=current_user.id
    ).first_or_404()
    db.session.delete(n)
    db.session.commit()
    flash("Notification deleted.", "info")
    return redirect(url_for("notification.index"))
