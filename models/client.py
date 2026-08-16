"""Client profile model."""
from datetime import datetime

from extensions import db


class ClientProfile(db.Model):
    __tablename__ = "client_profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True)
    company_name = db.Column(db.String(200))
    description = db.Column(db.Text)
    phone = db.Column(db.String(30))
    city = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="client_profile")
    projects = db.relationship(
        "Project", back_populates="client", cascade="all, delete-orphan", lazy="dynamic"
    )

    def __repr__(self):
        return f"<ClientProfile {self.id} user={self.user_id}>"