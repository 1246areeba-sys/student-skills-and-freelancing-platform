"""Student profile and student-skill association models."""
from datetime import datetime

from extensions import db


class StudentProfile(db.Model):
    __tablename__ = "student_profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True)
    university = db.Column(db.String(200))
    education = db.Column(db.Text)
    bio = db.Column(db.Text)
    experience = db.Column(db.String(50), default="Entry Level")  # Entry/Intermediate/Advanced/Expert
    hourly_rate = db.Column(db.Numeric(10, 2), default=0)
    availability = db.Column(db.String(30), default="Full Time")  # Full Time | Part Time | Weekends
    languages = db.Column(db.String(255), default="English")
    student_id = db.Column(db.String(50))
    university_email = db.Column(db.String(255))
    verification_status = db.Column(db.String(20), default="pending")  # pending | verified | rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship("User", back_populates="student_profile")
    skills = db.relationship(
        "StudentSkill", back_populates="student", cascade="all, delete-orphan", lazy="dynamic"
    )
    portfolios = db.relationship(
        "Portfolio", back_populates="student", cascade="all, delete-orphan", lazy="dynamic"
    )
    certificates = db.relationship(
        "Certificate", back_populates="student", cascade="all, delete-orphan", lazy="dynamic"
    )
    proposals = db.relationship(
        "Proposal", back_populates="student", cascade="all, delete-orphan", lazy="dynamic"
    )
    hires = db.relationship(
        "Hire", back_populates="student", cascade="all, delete-orphan", lazy="dynamic"
    )
    assessment_results = db.relationship(
        "AssessmentResult", back_populates="student", cascade="all, delete-orphan", lazy="dynamic"
    )

    @property
    def skill_list(self):
        return [ss.skill for ss in self.skills]

    @property
    def skill_names(self):
        return [ss.skill.name for ss in self.skills]

    @property
    def is_verified(self):
        return self.verification_status == "verified"

    def __repr__(self):
        return f"<StudentProfile {self.id} user={self.user_id}>"


class StudentSkill(db.Model):
    __tablename__ = "student_skills"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student_profiles.id"), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey("skills.id"), nullable=False)
    skill_level = db.Column(db.String(20), default="Intermediate")  # Beginner/Intermediate/Advanced/Expert

    student = db.relationship("StudentProfile", back_populates="skills")
    skill = db.relationship("Skill")

    __table_args__ = (db.UniqueConstraint("student_id", "skill_id", name="uq_student_skill"),)

    def __repr__(self):
        return f"<StudentSkill student={self.student_id} skill={self.skill_id}>"