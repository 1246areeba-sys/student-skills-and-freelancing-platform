"""User model — shared by students, clients and admins."""
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from extensions import db, login_manager


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="student")  # student | client | admin
    profile_picture = db.Column(db.String(255))
    phone = db.Column(db.String(30))
    city = db.Column(db.String(100))
    status = db.Column(db.String(20), nullable=False, default="active")  # active | suspended
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    student_profile = db.relationship(
        "StudentProfile", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    client_profile = db.relationship(
        "ClientProfile", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    notifications = db.relationship(
        "Notification", back_populates="user", cascade="all, delete-orphan", lazy="dynamic"
    )
    sent_messages = db.relationship(
        "Message", foreign_keys="Message.sender_id", back_populates="sender", lazy="dynamic"
    )
    received_messages = db.relationship(
        "Message", foreign_keys="Message.receiver_id", back_populates="receiver", lazy="dynamic"
    )
    wishlist_items = db.relationship(
        "Wishlist", back_populates="user", cascade="all, delete-orphan", lazy="dynamic"
    )

    # --- Password helpers ---
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    # --- Role helpers ---
    @property
    def is_student(self):
        return self.role == "student"

    @property
    def is_client(self):
        return self.role == "client"

    @property
    def is_admin(self):
        return self.role == "admin"

    @property
    def is_active_user(self):
        return self.status == "active"

    # --- Convenience accessors ---
    @property
    def display_picture(self):
        if self.profile_picture:
            return self.profile_picture
        return "images/default-avatar.png"

    def __repr__(self):
        return f"<User {self.id} {self.email} ({self.role})>"


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))