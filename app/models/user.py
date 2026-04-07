from datetime import datetime
from app.extensions import db

class UserProfile(db.Model):
    __tablename__ = "profiles"

    id = db.Column(db.String(36), primary_key=True)  # Supabase auth.users UUID
    role = db.Column(db.String(20), nullable=False, default="user")
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    phone = db.Column(db.String(30), nullable=True)
    avatar_url = db.Column(db.Text, nullable=True)

    is_active = db.Column(db.Boolean, nullable=False, default=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )