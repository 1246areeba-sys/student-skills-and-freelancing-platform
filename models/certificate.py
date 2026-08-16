"""Certificate model — student certificates and achievements."""
from datetime import datetime

from extensions import db


class Certificate(db.Model):
    __tablename__ = "certificates"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student_profiles.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    organization = db.Column(db.String(200))
    issue_date = db.Column(db.Date)
    credential_id = db.Column(db.String(100))
    certificate_file = db.Column(db.String(255))
    verification_url = db.Column(db.String(500))
    verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship("StudentProfile", back_populates="certificates")

    def __repr__(self):
        return f"<Certificate {self.title}>"