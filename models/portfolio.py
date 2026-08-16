"""Portfolio model — student showcase items."""
from datetime import datetime

from extensions import db


class Portfolio(db.Model):
    __tablename__ = "portfolios"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student_profiles.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    image = db.Column(db.String(255))
    technologies = db.Column(db.String(500))  # comma separated
    project_url = db.Column(db.String(500))
    github_url = db.Column(db.String(500))
    completion_date = db.Column(db.Date)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship("StudentProfile", back_populates="portfolios")
    category = db.relationship("Category", back_populates="portfolios")

    @property
    def tech_list(self):
        if not self.technologies:
            return []
        return [t.strip() for t in self.technologies.split(",") if t.strip()]

    def __repr__(self):
        return f"<Portfolio {self.title}>"