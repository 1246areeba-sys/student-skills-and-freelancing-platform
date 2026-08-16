"""Banner model — promotional banners managed from the admin panel."""
from datetime import datetime, date

from extensions import db


class Banner(db.Model):
    __tablename__ = "banners"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(160), nullable=False)
    message = db.Column(db.Text, nullable=False)
    link_url = db.Column(db.String(255), default="")
    link_text = db.Column(db.String(80), default="Learn more")
    background = db.Column(db.String(40), default="gold")  # gold | blue | green | red | dark
    image = db.Column(db.String(255), default="")  # optional uploaded banner image
    is_active = db.Column(db.Boolean, default=True)
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Banner {self.title}>"

    @property
    def is_currently_visible(self):
        """True if the banner is active and within its scheduled date range."""
        if not self.is_active:
            return False
        today = date.today()
        if self.start_date and self.start_date > today:
            return False
        if self.end_date and self.end_date < today:
            return False
        return True
