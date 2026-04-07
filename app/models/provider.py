from datetime import datetime
from app.extensions import db

class ProviderProfile(db.Model):
    __tablename__ = "provider_profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(36), nullable=True, index=True)  # profiles.id later
    business_name = db.Column(db.String(160), nullable=False)
    business_type = db.Column(db.String(100), nullable=True)
    city = db.Column(db.String(80), nullable=True)

    approval_status = db.Column(db.String(30), nullable=False, default="pending")
    created_source = db.Column(db.String(30), nullable=False, default="provider_signup")
    created_by = db.Column(db.String(36), nullable=True)
    submitted_at = db.Column(db.DateTime, nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    approved_by = db.Column(db.String(36), nullable=True)
    rejection_reason = db.Column(db.Text, nullable=True)

    is_active = db.Column(db.Boolean, nullable=False, default=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )