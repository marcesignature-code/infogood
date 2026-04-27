from __future__ import annotations

from typing import Any

from flask import url_for
from flask_login import current_user

from app.extensions import db
from app.models.bookmark import Bookmark
from app.models.user import UserProfile


DEFAULT_AVATAR = "assets/img/user.jpg"
DEFAULT_LISTING_IMAGE = "assets/img/banner-1.jpg"


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _resolve_user(user: UserProfile | None = None) -> UserProfile | None:
    if user is not None:
        return user

    try:
        if current_user.is_authenticated:
            return current_user
    except Exception:
        pass

    try:
        return (
            UserProfile.query.filter_by(is_active=True)
            .order_by(UserProfile.created_at.asc())
            .first()
        )
    except Exception:
        db.session.rollback()
        return None


def _profile_completion(profile: UserProfile | None) -> int:
    if not profile:
        return 0
    fields = [
        getattr(profile, "first_name", None),
        getattr(profile, "last_name", None),
        getattr(profile, "phone", None),
        getattr(profile, "avatar_url", None),
        getattr(profile, "email", None),
    ]
    completed = sum(1 for value in fields if value)
    return min(100, int((completed / len(fields)) * 100))


def _dashboard_user_payload(profile: UserProfile | None) -> dict[str, Any]:
    if not profile:
        return {
            "id": None,
            "first_name": "Guest",
            "last_name": "",
            "full_name": "Guest User",
            "email": "",
            "role": "user",
            "avatar_url": url_for("static", filename=DEFAULT_AVATAR),
            "profile_completion": 0,
        }

    first_name = profile.first_name or "User"
    last_name = profile.last_name or ""
    full_name = f"{first_name} {last_name}".strip() or "User"

    return {
        "id": str(profile.id),
        "first_name": first_name,
        "last_name": last_name,
        "full_name": full_name,
        "email": profile.email or "",
        "role": profile.role or "user",
        "avatar_url": profile.avatar_url or url_for("static", filename=DEFAULT_AVATAR),
        "profile_completion": _profile_completion(profile),
    }


def _catalog_gallerys5() -> list[dict[str, str]]:
    return [
        {"title": "Upload Logo", "id": "single-logo", "name": "Maximum file size: 2 MB."},
        {"title": "Featured Image", "id": "featured-image", "name": "Maximum file size: 2 MB."},
        {"title": "Image Gallery", "id": "gallery", "name": "Maximum file size: 2 MB."},
    ]


def _catalog_timings() -> list[dict[str, str]]:
    labels = [
        "Closed",
        "1 :00 AM",
        "2 :00 AM",
        "3 :00 AM",
        "4 :00 AM",
        "5 :00 AM",
        "6 :00 AM",
        "7 :00 AM",
        "8 :00 AM",
        "9 :00 AM",
        "10 :00 AM",
        "11 :00 AM",
        "12 :00 AM",
        "1 :00 PM",
        "2 :00 PM",
        "3 :00 PM",
        "4 :00 PM",
        "5 :00 PM",
        "6 :00 PM",
        "7 :00 PM",
        "8 :00 PM",
        "9 :00 PM",
        "10 :00 PM",
        "11 :00 PM",
        "12 :00 PM",
    ]
    return [{"time": label} for label in labels]


def _catalog_features2() -> list[dict[str, str]]:
    names = [
        ("Reservations", "am2"),
        ("Vegetarian Options", "am3"),
        ("Moderate Noise", "am4"),
        ("Good For Kids", "am5"),
        ("Private Lot Parking", "am6"),
        ("Beer & Wine", "am7"),
        ("TV Services", "am8"),
        ("Pets Allow", "am9"),
        ("Offers Delivery", "am10"),
        ("Staff wears masks", "am11"),
        ("Accepts Credit Cards", "am12"),
        ("Offers Catering", "am13"),
        ("Good for Breakfast", "am14"),
        ("Waiter Service", "am15"),
        ("Drive-Thru", "am16"),
        ("Outdoor Seating", "am17"),
    ]
    return [{"title": title, "id": field_id} for title, field_id in names]


def _build_saveds(profile: UserProfile | None) -> list[dict[str, Any]]:
    if not profile:
        return []

    try:
        bookmarks = (
            Bookmark.query.filter_by(user_id=profile.id)
            .order_by(Bookmark.created_at.desc())
            .all()
        )
    except Exception:
        db.session.rollback()
        return []

    saveds: list[dict[str, Any]] = []
    fallback_image = url_for("static", filename=DEFAULT_LISTING_IMAGE)

    for bookmark in bookmarks:
        listing = bookmark.listing
        if listing is None:
            continue

        title = (
            listing.listing_name
            or listing.name
            or listing.legal_name
            or "Untitled Listing"
        )
        location_parts = [
            listing.neighborhood,
            listing.city,
            listing.province,
            listing.country,
        ]
        desc = ", ".join(part for part in location_parts if part) or "Location pending"
        review_count = getattr(listing, "review_count", 0) or getattr(
            listing, "reviews_count", 0
        )
        reviews_label = f"{_safe_int(review_count)} Reviews"

        saveds.append(
            {
                "id": str(listing.id),
                "img": listing.cover_image_url or fallback_image,
                "title": title,
                "desc": desc,
                "reviews": reviews_label,
                "saved_at": bookmark.created_at,
            }
        )

    return saveds


def get_dashboard_context(user: UserProfile | None = None) -> dict[str, Any]:
    profile = _resolve_user(user)
    profile_metrics = getattr(profile, "metrics", None) if profile else None
    saveds = _build_saveds(profile)

    active_listings = _safe_int(getattr(profile_metrics, "active_listings_count", 0))
    total_views = _safe_int(getattr(profile_metrics, "total_views", 0))
    total_saved = len(saveds) if saveds else 0
    total_reviews = _safe_int(getattr(profile_metrics, "total_reviews", 0))
    wallet_balance = _safe_int(getattr(profile_metrics, "wallet_balance_usd", 0))
    wallet_total_earning = _safe_int(getattr(profile_metrics, "wallet_total_earning_usd", 0))
    wallet_total_orders = _safe_int(getattr(profile_metrics, "wallet_total_orders", 0))
    metrics = profile_metrics or {
        "active_listings_count": 0,
        "total_views": 0,
        "total_saved": 0,
        "total_reviews": 0,
        "wallet_balance_usd": 0,
    }

    dashboard_user = _dashboard_user_payload(profile)
    user_name = dashboard_user["full_name"]
    user_email = dashboard_user["email"]
    user_avatar_url = dashboard_user["avatar_url"]
    alert_message = (
        f"Hi {dashboard_user['first_name']}, your dashboard is ready with default values."
        if profile
        else "Connect or create a profile to replace guest defaults."
    )

    return {
        "profile": profile,
        "user_name": user_name,
        "user_email": user_email,
        "user_avatar_url": user_avatar_url,
        "metrics": metrics,
        "active_listings_count": active_listings,
        "total_views": total_views,
        "total_saved": total_saved,
        "total_reviews": total_reviews,
        "wallet_balance_usd": wallet_balance,
        "saved_listings": saveds,
        "dashboard_user": dashboard_user,
        "dashboard_alert": {
            "type": "info" if profile else "warning",
            "title": dashboard_user["first_name"],
            "message": alert_message,
        },
        "rows": [
            {
                "icon": "bi bi-pin-map-fill text-success fs-2",
                "style": "bg-light-success",
                "title": "Active Listings",
                "value": active_listings,
                "symbol": "",
            },
            {
                "icon": "bi bi-graph-up-arrow text-danger fs-2",
                "style": "bg-light-danger",
                "title": "Total Views",
                "value": total_views,
                "symbol": "",
            },
            {
                "icon": "bi bi-suit-heart text-warning fs-2",
                "style": "bg-light-warning",
                "title": "Total Saved",
                "value": total_saved,
                "symbol": "",
            },
            {
                "icon": "bi bi-chat-left-text text-info fs-2",
                "style": "bg-light-info",
                "title": "Total Reviews",
                "value": total_reviews,
                "symbol": "",
            },
        ],
        "rows2": [
            {
                "icon": "bi bi-wallet",
                "style": "bg-danger",
                "title": "Your Balance in USD",
                "number": wallet_balance,
                "price": wallet_balance,
            },
            {
                "icon": "bi bi-coin",
                "style": "bg-warning",
                "title": "Total Earning in USD",
                "number": wallet_total_earning,
                "price": wallet_total_earning,
            },
            {
                "icon": "bi bi-basket2",
                "style": "bg-purple",
                "title": "Total Orders",
                "number": wallet_total_orders,
                "price": wallet_total_orders,
            },
        ],
        "activities": [],
        "messages": [],
        "invoices": [],
        "bookings": [],
        "manages": [],
        "saveds": saveds,
        "messages2": [],
        "reviews2": [],
        "earnings": [],
        "gallerys5": _catalog_gallerys5(),
        "timings": _catalog_timings(),
        "features2": _catalog_features2(),
    }
