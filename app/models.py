# app/models.py
from datetime import datetime
from . import db  # usa el db creado en app/__init__.py


class Listing(db.Model):
    __tablename__ = "listings"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(160), nullable=False)
    slug = db.Column(db.String(180), unique=True, nullable=False, index=True)
    short_description = db.Column(db.String(280), nullable=True)

    status = db.Column(db.String(30), nullable=False, default="open")         # open / closed
    price_level = db.Column(db.String(4), nullable=False, default="$$")       # $, $$, $$$, $$$$
    is_featured = db.Column(db.Boolean, nullable=False, default=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True, index=True)

    cover_image_url = db.Column(db.Text, nullable=True)
    logo_image_url = db.Column(db.Text, nullable=True)

    phone_primary = db.Column(db.String(40), nullable=True)
    city = db.Column(db.String(80), nullable=True, index=True)
    distance_miles = db.Column(db.Numeric(6, 2), nullable=True)

    rating_avg = db.Column(db.Numeric(3, 2), nullable=False, default=0)
    reviews_count = db.Column(db.Integer, nullable=False, default=0)

    sort_priority = db.Column(db.Integer, nullable=False, default=0)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    @property
    def open_badge_text(self):
        return "OPEN" if self.status == "open" else self.status.upper()

