"""Project, project-skill and hire models."""
from datetime import datetime

from extensions import db


class Project(db.Model):
    __tablename__ = "projects"

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("client_profiles.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    budget = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    deadline = db.Column(db.Date)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"))
    project_type = db.Column(db.String(30), default="Fixed")  # Fixed | Hourly
    location_type = db.Column(db.String(30), default="Remote")  # Remote | Onsite | Hybrid
    location = db.Column(db.String(150))
    freelancers_needed = db.Column(db.Integer, default=1)
    attachment = db.Column(db.String(255))
    status = db.Column(db.String(20), default="open")  # draft|open|in_progress|completed|cancelled|closed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    client = db.relationship("ClientProfile", back_populates="projects")
    category = db.relationship("Category", back_populates="projects")
    required_skills = db.relationship(
        "ProjectSkill", back_populates="project", cascade="all, delete-orphan", lazy="dynamic"
    )
    proposals = db.relationship(
        "Proposal", back_populates="project", cascade="all, delete-orphan", lazy="dynamic"
    )
    hires = db.relationship(
        "Hire", back_populates="project", cascade="all, delete-orphan", lazy="dynamic"
    )
    milestones = db.relationship(
        "Milestone", back_populates="project", cascade="all, delete-orphan", lazy="dynamic"
    )
    payments = db.relationship(
        "Payment", back_populates="project", cascade="all, delete-orphan", lazy="dynamic"
    )
    reviews = db.relationship(
        "Review", back_populates="project", cascade="all, delete-orphan", lazy="dynamic"
    )

    @property
    def skill_names(self):
        return [ps.skill.name for ps in self.required_skills]

    @property
    def proposal_count(self):
        return self.proposals.count()

    @property
    def hired_students(self):
        return [h.student for h in self.hires]

    @property
    def is_open(self):
        return self.status == "open"

    def __repr__(self):
        return f"<Project {self.title}>"


class ProjectSkill(db.Model):
    __tablename__ = "project_skills"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey("skills.id"), nullable=False)

    project = db.relationship("Project", back_populates="required_skills")
    skill = db.relationship("Skill", back_populates="project_links")

    __table_args__ = (db.UniqueConstraint("project_id", "skill_id", name="uq_project_skill"),)

    def __repr__(self):
        return f"<ProjectSkill project={self.project_id} skill={self.skill_id}>"


class Hire(db.Model):
    __tablename__ = "hires"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("student_profiles.id"), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey("client_profiles.id"), nullable=False)
    proposal_id = db.Column(db.Integer, db.ForeignKey("proposals.id"))
    status = db.Column(db.String(20), default="active")  # active | completed | cancelled
    hired_at = db.Column(db.DateTime, default=datetime.utcnow)

    project = db.relationship("Project", back_populates="hires")
    student = db.relationship("StudentProfile", back_populates="hires")
    client = db.relationship("ClientProfile")
    proposal = db.relationship("Proposal", back_populates="hire")

    def __repr__(self):
        return f"<Hire project={self.project_id} student={self.student_id}>"