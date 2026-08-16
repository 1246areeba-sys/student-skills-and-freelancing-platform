"""Wishlist model — saved students, projects and searches."""
from datetime import datetime

from extensions import db


class Wishlist(db.Model):
    __tablename__ = "wishlists"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    item_type = db.Column(db.String(20), nullable=False)  # student | project | search
    item_id = db.Column(db.Integer, nullable=False)
    search_query = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="wishlist_items")

    __table_args__ = (
        db.UniqueConstraint("user_id", "item_type", "item_id", name="uq_wishlist_item"),
    )

    @property
    def project(self):
        """Resolve the related Project when item_type == 'project'."""
        if self.item_type != "project":
            return None
        from models.project import Project
        return Project.query.get(self.item_id)

    @property
    def student(self):
        """Resolve the related StudentProfile when item_type == 'student'."""
        if self.item_type != "student":
            return None
        from models.student import StudentProfile
        return StudentProfile.query.get(self.item_id)

    def __repr__(self):
        return f"<Wishlist {self.item_type} {self.item_id}>"
