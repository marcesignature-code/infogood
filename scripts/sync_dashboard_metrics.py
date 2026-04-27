from __future__ import annotations

from pathlib import Path
import sys
from typing import Iterable

from sqlalchemy import inspect

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app import create_app
from app.extensions import db
from app.models.dashboard_metrics import DashboardMetrics
from app.models.listing import Listing
from app.models.user import UserProfile


def _listing_column_names() -> set[str]:
    return {column.key for column in inspect(Listing).columns}


def _find_owned_listings(profile: UserProfile, listing_columns: set[str]) -> tuple[list[Listing], list[str]]:
    warnings: list[str] = []

    def _safe_query(column_name: str, value: object) -> list[Listing]:
        try:
            column_attr = getattr(Listing, column_name)
            return Listing.query.filter(column_attr == value).all()
        except Exception:
            db.session.rollback()
            warning_message = f"Could not resolve listings for user {profile.email}"
            if warning_message not in warnings:
                warnings.append(warning_message)
            return []

    # Strategy 1: explicit ownership-like columns in listings.
    direct_owner_columns = [
        "owner_id",
        "owner_user_id",
        "user_id",
        "profile_id",
        "created_by",
        "created_by_user_id",
        "provider_user_id",
    ]
    for column_name in direct_owner_columns:
        if column_name not in listing_columns:
            continue

        # Try UUID and string variants safely.
        listings = _safe_query(column_name, profile.id)
        if not listings:
            listings = _safe_query(column_name, str(profile.id))
        if listings:
            return listings, warnings

    # Strategy 2: provider_email (when present) can still map listing ownership safely.
    if "provider_email" in listing_columns and profile.email:
        listings = _safe_query("provider_email", profile.email)
        if listings:
            return listings, warnings

    warnings.append(
        "No clear relation between listings and user; active_listings_count, total_views and total_reviews set to 0."
    )
    return [], warnings


def _sum_review_count(listings: Iterable[Listing]) -> int:
    total = 0
    for listing in listings:
        review_count = getattr(listing, "review_count", None)
        reviews_count = getattr(listing, "reviews_count", None)
        total += int(review_count or reviews_count or 0)
    return total


def _sum_views(listings: Iterable[Listing]) -> int:
    return sum(int(getattr(listing, "view_count", 0) or 0) for listing in listings)


def sync_dashboard_metrics() -> None:
    app = create_app()

    with app.app_context():
        active_users = UserProfile.query.filter_by(is_active=True).order_by(UserProfile.created_at.asc()).all()
        listing_columns = _listing_column_names()

        print(f"Active users found: {len(active_users)}")
        print("-" * 60)

        processed = 0
        for profile in active_users:
            processed += 1

            metrics = DashboardMetrics.query.filter_by(user_id=profile.id).first()
            created = False
            if not metrics:
                metrics = DashboardMetrics(user_id=profile.id)
                db.session.add(metrics)
                created = True

            user_warnings: list[str] = []

            owned_listings, relation_warnings = _find_owned_listings(profile, listing_columns)
            user_warnings.extend(relation_warnings)

            active_listings_count = sum(1 for listing in owned_listings if bool(getattr(listing, "is_active", False)))
            total_views = _sum_views(owned_listings) if owned_listings else 0
            total_reviews = _sum_review_count(owned_listings) if owned_listings else 0
            total_saved = int(len(profile.bookmarks or []))

            # Keep current wallet balance when metrics already exists.
            wallet_balance = metrics.wallet_balance_usd if metrics.wallet_balance_usd is not None else 0

            metrics.active_listings_count = active_listings_count
            metrics.total_views = total_views
            metrics.total_saved = total_saved
            metrics.total_reviews = total_reviews
            metrics.wallet_balance_usd = wallet_balance

            print(f"User: {profile.email} ({profile.id})")
            print(f"  Metrics record: {'created' if created else 'updated'}")
            print(f"  active_listings_count={active_listings_count}")
            print(f"  total_saved={total_saved}")
            print(f"  total_reviews={total_reviews}")
            print(f"  total_views={total_views}")
            print(f"  wallet_balance_usd={wallet_balance}")
            if user_warnings:
                for warning in user_warnings:
                    print(f"  WARNING: {warning}")
            print("-" * 60)

        db.session.commit()
        print(f"Done. Processed users: {processed}")


if __name__ == "__main__":
    sync_dashboard_metrics()
