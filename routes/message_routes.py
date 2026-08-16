"""Message routes: inbox, chat thread, send message, mark read."""
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from sqlalchemy import or_

from extensions import db
from models.user import User
from models.message import Message
from models.project import Project
from utils import save_upload, notify

message_bp = Blueprint("message", __name__, url_prefix="/messages")


@message_bp.route("/")
@login_required
def inbox():
    """List all conversations for the current user."""
    conversations = {}
    messages = (
        Message.query.filter(
            or_(Message.sender_id == current_user.id, Message.receiver_id == current_user.id)
        )
        .order_by(Message.created_at.desc())
        .all()
    )
    for m in messages:
        other_id = m.receiver_id if m.sender_id == current_user.id else m.sender_id
        key = other_id
        if key not in conversations:
            other = User.query.get(other_id)
            unread = Message.query.filter_by(
                receiver_id=current_user.id, sender_id=other_id, is_read=False
            ).count()
            conversations[key] = {
                "other": other,
                "last": m,
                "unread": unread,
            }
    return render_template("messages/messages.html", conversations=conversations)


@message_bp.route("/<int:user_id>", methods=["GET", "POST"])
@login_required
def chat(user_id):
    other = User.query.get_or_404(user_id)
    if other.id == current_user.id:
        flash("You cannot message yourself.", "warning")
        return redirect(url_for("message.inbox"))

    if request.method == "POST":
        text = request.form.get("message", "").strip()
        attachment = request.files.get("attachment")
        att_path = save_upload(attachment, "messages") if attachment and attachment.filename else None
        project_id = request.form.get("project_id", type=int)
        if not text and not att_path:
            flash("Message cannot be empty.", "danger")
            return redirect(url_for("message.chat", user_id=user_id))
        msg = Message(
            sender_id=current_user.id,
            receiver_id=user_id,
            project_id=project_id,
            message=text,
            attachment=att_path,
        )
        db.session.add(msg)
        notify(user_id, "New Message", f"{current_user.name} sent you a message.", "message",
               url_for("message.chat", user_id=current_user.id))
        db.session.commit()
        return redirect(url_for("message.chat", user_id=user_id))

    # Mark incoming messages as read
    Message.query.filter_by(receiver_id=current_user.id, sender_id=user_id, is_read=False).update(
        {"is_read": True}
    )
    db.session.commit()

    thread = (
        Message.query.filter(
            or_(
                (Message.sender_id == current_user.id) & (Message.receiver_id == user_id),
                (Message.sender_id == user_id) & (Message.receiver_id == current_user.id),
            )
        )
        .order_by(Message.created_at.asc())
        .all()
    )

    # Projects shared between the two users (for context)
    shared_projects = []
    if current_user.is_student and other.is_client:
        student = current_user.student_profile
        shared_projects = Project.query.filter_by(client_id=other.client_profile.id).all()
    elif current_user.is_client and other.is_student:
        client = current_user.client_profile
        shared_projects = Project.query.filter_by(client_id=client.id).all()

    return render_template(
        "messages/chat.html",
        other=other,
        thread=thread,
        shared_projects=shared_projects,
    )
