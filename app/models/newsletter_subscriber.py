from datetime import datetime
import uuid

from sqlalchemy.dialects.postgresql import UUID

from app.extensions import db


class NewsletterSubscriber(db.Model):
    __tablename__ = "newsletter_subscribers"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    source = db.Column(db.String(80), nullable=False, default="home_newsletter", index=True)
    language_preference = db.Column(db.String(10), nullable=False, default="en")
    is_active = db.Column(db.Boolean, nullable=False, default=True, index=True)

    full_name = db.Column(db.String(160), nullable=True)
    country = db.Column(db.String(80), nullable=True)
    city = db.Column(db.String(80), nullable=True)
    interests = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )
