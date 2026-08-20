"""Review model — two-way ratings between clients and students."""
from datetime import datetime

from extensions import db


class Review(db.Model):
    __tablename__ = "reviews"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
    reviewer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    reviewed_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    rating = db.Column(db.Integer, nullable=False, default=5)  # 1-5
    review = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    project = db.relationship("Project", back_populates="reviews")
    reviewer = db.relationship("User", foreign_keys=[reviewer_id], back_populates="reviews_given")
    reviewed_user = db.relationship("User", foreign_keys=[reviewed_user_id], back_populates="reviews_received")

    __table_args__ = (
        db.UniqueConstraint("project_id", "reviewer_id", "reviewed_user_id", name="uq_review"),
    )

    def __repr__(self):
        return f"<Review {self.id} rating={self.rating}>"
