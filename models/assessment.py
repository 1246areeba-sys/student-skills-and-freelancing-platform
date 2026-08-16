"""Assessment models — skill assessments with MCQs and results."""
from datetime import datetime

from extensions import db


class Assessment(db.Model):
    __tablename__ = "assessments"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    skill_id = db.Column(db.Integer, db.ForeignKey("skills.id"))
    passing_score = db.Column(db.Integer, default=70)  # percentage
    duration_minutes = db.Column(db.Integer, default=15)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    skill = db.relationship("Skill")
    questions = db.relationship(
        "AssessmentQuestion", back_populates="assessment", cascade="all, delete-orphan", lazy="dynamic"
    )
    results = db.relationship(
        "AssessmentResult", back_populates="assessment", cascade="all, delete-orphan", lazy="dynamic"
    )

    def __repr__(self):
        return f"<Assessment {self.title}>"


class AssessmentQuestion(db.Model):
    __tablename__ = "assessment_questions"

    id = db.Column(db.Integer, primary_key=True)
    assessment_id = db.Column(db.Integer, db.ForeignKey("assessments.id"), nullable=False)
    question = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.String(300), nullable=False)
    option_b = db.Column(db.String(300), nullable=False)
    option_c = db.Column(db.String(300), nullable=False)
    option_d = db.Column(db.String(300), nullable=False)
    correct_answer = db.Column(db.String(1), nullable=False)  # A | B | C | D

    assessment = db.relationship("Assessment", back_populates="questions")

    def __repr__(self):
        return f"<Question {self.id}>"


class AssessmentResult(db.Model):
    __tablename__ = "assessment_results"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student_profiles.id"), nullable=False)
    assessment_id = db.Column(db.Integer, db.ForeignKey("assessments.id"), nullable=False)
    score = db.Column(db.Integer, default=0)
    percentage = db.Column(db.Integer, default=0)
    passed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship("StudentProfile", back_populates="assessment_results")
    assessment = db.relationship("Assessment", back_populates="results")

    __table_args__ = (
        db.UniqueConstraint("student_id", "assessment_id", name="uq_student_assessment"),
    )

    def __repr__(self):
        return f"<AssessmentResult {self.id} {self.percentage}%>"