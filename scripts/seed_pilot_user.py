from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app import create_app
from app.extensions import db
from app.models.dashboard_metrics import DashboardMetrics
from app.models.user import UserProfile
from sqlalchemy.exc import ProgrammingError


PILOT_EMAIL = "pilot@example.com"


def seed_pilot_user() -> None:
    app = create_app()

    with app.app_context():
        profile = UserProfile.query.filter_by(email=PILOT_EMAIL).first()
        if not profile:
            profile = UserProfile(
                email=PILOT_EMAIL,
                username="pilot",
                role="user",
                first_name="Pilot",
                last_name="User",
                phone="",
                avatar_url=None,
                is_active=True,
            )
            profile.set_password("pilot12345")
            db.session.add(profile)
            db.session.flush()

        try:
            metrics = DashboardMetrics.query.filter_by(user_id=profile.id).first()
        except ProgrammingError:
            db.session.rollback()
            raise SystemExit(
                "dashboard_metrics table does not exist yet. Run your migration first, then rerun this seed."
            )
        if not metrics:
            metrics = DashboardMetrics(user_id=profile.id)
            db.session.add(metrics)
        else:
            metrics.active_listings_count = 0
            metrics.total_views = 0
            metrics.total_saved = 0
            metrics.total_reviews = 0
            metrics.wallet_balance_usd = 0
            metrics.wallet_total_earning_usd = 0
            metrics.wallet_total_orders = 0

        db.session.commit()
        print(f"Pilot user ready: {profile.email} ({profile.id})")


if __name__ == "__main__":
    seed_pilot_user()
