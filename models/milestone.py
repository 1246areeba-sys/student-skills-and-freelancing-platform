"""Milestone model — project milestones created by clients."""
from datetime import datetime

from extensions import db


class Milestone(db.Model):
    __tablename__ = "milestones"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    amount = db.Column(db.Numeric(12, 2), default=0)
    deadline = db.Column(db.Date)
    status = db.Column(db.String(20), default="pending")
    # pending | in_progress | submitted | approved | revision | completed
    deliverable = db.Column(db.String(255))
    payment_status = db.Column(db.String(20), default="unpaid")  # unpaid | paid
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    project = db.relationship("Project", back_populates="milestones")

    def __repr__(self):
        return f"<Milestone {self.title}>"