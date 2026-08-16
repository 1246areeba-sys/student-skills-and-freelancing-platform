"""Category model — organizes skills and projects."""
from extensions import db


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    description = db.Column(db.Text)
    icon = db.Column(db.String(50), default="briefcase")

    skills = db.relationship("Skill", back_populates="category", lazy="dynamic")
    portfolios = db.relationship("Portfolio", back_populates="category", lazy="dynamic")
    projects = db.relationship("Project", back_populates="category", lazy="dynamic")

    def __repr__(self):
        return f"<Category {self.name}>"