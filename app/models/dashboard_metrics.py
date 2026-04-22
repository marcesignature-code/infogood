from datetime import datetime

from app.extensions import db
from sqlalchemy.dialects.postgresql import UUID


class DashboardMetrics(db.Model):
    __tablename__ = "dashboard_metrics"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    active_listings_count = db.Column(db.Integer, nullable=False, default=0)
    total_views = db.Column(db.Integer, nullable=False, default=0)
    total_saved = db.Column(db.Integer, nullable=False, default=0)
    total_reviews = db.Column(db.Integer, nullable=False, default=0)
    wallet_balance_usd = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    wallet_total_earning_usd = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    wallet_total_orders = db.Column(db.Integer, nullable=False, default=0)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    user = db.relationship("UserProfile", back_populates="metrics", uselist=False)
