"""SiteSetting model — key/value store for platform-wide settings (logo, name, etc.)."""
from extensions import db


class SiteSetting(db.Model):
    __tablename__ = "site_settings"

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(80), unique=True, nullable=False, index=True)
    value = db.Column(db.Text, default="")

    def __repr__(self):
        return f"<SiteSetting {self.key}>"

    @classmethod
    def get(cls, key, default=""):
        """Return the stored value for a key, or a default if not set."""
        record = cls.query.filter_by(key=key).first()
        return record.value if record else default

    @classmethod
    def set(cls, key, value):
        """Create or update a setting value."""
        record = cls.query.filter_by(key=key).first()
        if record:
            record.value = value or ""
        else:
            record = cls(key=key, value=value or "")
            db.session.add(record)
        db.session.commit()
        return record
