"""Payment and withdrawal models."""
from datetime import datetime

from extensions import db


class Payment(db.Model):
    __tablename__ = "payments"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey("client_profiles.id"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("student_profiles.id"), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    platform_fee = db.Column(db.Numeric(12, 2), default=0)
    student_amount = db.Column(db.Numeric(12, 2), default=0)
    status = db.Column(db.String(20), default="pending")  # pending|processing|paid|failed|refunded
    transaction_reference = db.Column(db.String(100), unique=True)
    payment_method = db.Column(db.String(50), default="Platform Balance")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    project = db.relationship("Project", back_populates="payments")
    client = db.relationship("ClientProfile")
    student = db.relationship("StudentProfile")

    def __repr__(self):
        return f"<Payment {self.id} {self.amount} {self.status}>"


class Withdrawal(db.Model):
    __tablename__ = "withdrawals"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student_profiles.id"), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    method = db.Column(db.String(50), default="Bank Transfer")
    account_details = db.Column(db.String(255))
    status = db.Column(db.String(20), default="pending")  # pending|approved|rejected|paid
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship("StudentProfile")

    def __repr__(self):
        return f"<Withdrawal {self.id} {self.amount} {self.status}>"