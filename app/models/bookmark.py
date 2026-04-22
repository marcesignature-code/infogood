from datetime import datetime

from sqlalchemy.dialects.postgresql import UUID

from app.extensions import db


class Bookmark(db.Model):
    __tablename__ = "bookmarks"

    user_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("profiles.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
        index=True,
    )
    listing_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("listings.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
        index=True,
    )
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)

    user = db.relationship("UserProfile", back_populates="bookmarks")
    listing = db.relationship("Listing", back_populates="bookmarks")
