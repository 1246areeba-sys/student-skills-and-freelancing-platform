"""Proposal model — student applications to projects."""
from datetime import datetime

from extensions import db


class Proposal(db.Model):
    __tablename__ = "proposals"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("student_profiles.id"), nullable=False)
    cover_letter = db.Column(db.Text, nullable=False)
    proposed_price = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    delivery_time = db.Column(db.Integer, default=7)  # days
    relevant_skills = db.Column(db.String(500))
    portfolio_samples = db.Column(db.Text)
    status = db.Column(db.String(20), default="pending")  # pending|accepted|rejected|withdrawn
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    project = db.relationship("Project", back_populates="proposals")
    student = db.relationship("StudentProfile", back_populates="proposals")
    hire = db.relationship("Hire", back_populates="proposal", uselist=False)

    __table_args__ = (
        db.UniqueConstraint("project_id", "student_id", name="uq_project_student_proposal"),
    )

    def __repr__(self):
        return f"<Proposal {self.id} project={self.project_id} student={self.student_id}>"