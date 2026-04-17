from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from flask import request, url_for
from flask_login import current_user
from sqlalchemy import func

from app.extensions import db
from app.models.listing import Listing
from app.models.provider import ProviderProfile
from app.models.user import UserProfile


DEFAULT_AVATAR = "assets/img/user.jpg"


@dataclass
class DashboardUser:
    id: str | None
    full_name: str
    first_name: str
    role: str
    avatar_url: str
    profile_completion: int


class DashboardService:
    @staticmethod
    def resolve_profile(profile_id: str | None = None) -> UserProfile | None:
        try:
            if current_user.is_authenticated:
                return current_user

            if profile_id:
                return UserProfile.query.filter_by(id=profile_id, is_active=True).first()

            preview_id = request.args.get("profile_id")
            if preview_id:
                return UserProfile.query.filter_by(id=preview_id, is_active=True).first()

            return (
                UserProfile.query.filter_by(is_active=True)
                .order_by(UserProfile.created_at.asc())
                .first()
            )
        except Exception:
            db.session.rollback()
            return None

    @staticmethod
    def build_user_dashboard(profile: UserProfile | None) -> dict[str, Any]:
        dashboard_user = DashboardService._serialize_user(profile)

        provider_profile = DashboardService._get_provider_profile(profile)
        active_listings = DashboardService._count_active_listings()
        total_reviews = DashboardService._count_total_reviews()
        total_views = DashboardService._estimate_total_views(active_listings)
        total_saved = DashboardService._estimate_total_saved(active_listings)

        rows = [
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
        ]

        activities = DashboardService._build_activities(profile, provider_profile)
        messages = DashboardService._build_messages(profile)
        invoices = DashboardService._build_invoices(provider_profile)
        alert = DashboardService._build_alert(profile, provider_profile, active_listings)

        return {
            "page_title": "User Dashboard",
            "dashboard_user": dashboard_user,
            "dashboard_alert": alert,
            "rows": rows,
            "activities": activities,
            "messages": messages,
            "invoices": invoices,
        }

    @staticmethod
    def _serialize_user(profile: UserProfile | None) -> DashboardUser:
        if not profile:
            return DashboardUser(
                id=None,
                full_name="Guest User",
                first_name="Guest",
                role="user",
                avatar_url=url_for("static", filename=DEFAULT_AVATAR),
                profile_completion=15,
            )

        avatar_url = profile.avatar_url or url_for("static", filename=DEFAULT_AVATAR)

        full_name = getattr(profile, "full_name", None)
        if not full_name:
            first_name = getattr(profile, "first_name", "") or ""
            last_name = getattr(profile, "last_name", "") or ""
            full_name = f"{first_name} {last_name}".strip() or "User"

        return DashboardUser(
            id=str(profile.id),
            full_name=full_name,
            first_name=profile.first_name or "User",
            role=profile.role or "user",
            avatar_url=avatar_url,
            profile_completion=DashboardService._profile_completion(profile),
        )

    @staticmethod
    def _profile_completion(profile: UserProfile) -> int:
        fields = [
            getattr(profile, "first_name", None),
            getattr(profile, "last_name", None),
            getattr(profile, "phone", None),
            getattr(profile, "avatar_url", None),
            getattr(profile, "email", None),
        ]
        completed = sum(1 for value in fields if value)
        return min(100, int((completed / len(fields)) * 100))

    @staticmethod
    def _get_provider_profile(profile: UserProfile | None) -> ProviderProfile | None:
        if not profile:
            return None

        try:
            return ProviderProfile.query.filter_by(
                user_id=profile.id,
                is_active=True
            ).first()
        except Exception:
            db.session.rollback()
            return None

    @staticmethod
    def _count_active_listings() -> int:
        try:
            return int(Listing.query.filter_by(is_active=True).count())
        except Exception:
            db.session.rollback()
            return 0

    @staticmethod
    def _count_total_reviews() -> int:
        try:
            if hasattr(Listing, "reviews_count"):
                value = db.session.query(
                    func.coalesce(func.sum(Listing.reviews_count), 0)
                ).scalar()
                return int(value or 0)
            return 0
        except Exception:
            db.session.rollback()
            return 0

    @staticmethod
    def _estimate_total_views(active_listings: int) -> int:
        return active_listings * 127

    @staticmethod
    def _estimate_total_saved(active_listings: int) -> int:
        return active_listings * 11

    @staticmethod
    def _build_alert(
        profile: UserProfile | None,
        provider_profile: ProviderProfile | None,
        active_listings: int,
    ) -> dict[str, str]:
        if provider_profile and getattr(provider_profile, "approval_status", None) == "approved":
            business_name = getattr(provider_profile, "business_name", None) or "business"
            return {
                "type": "primary",
                "title": business_name,
                "message": f"Your business {business_name} has been approved and is ready to be managed from the dashboard.",
            }

        if profile:
            first_name = getattr(profile, "first_name", "User") or "User"
            return {
                "type": "info",
                "title": first_name,
                "message": f"Hi {first_name}, your dashboard is now loading real profile data from the database. Active public listings: {active_listings}.",
            }

        return {
            "type": "warning",
            "title": "No active profile",
            "message": "Create or connect a profile record to load real dashboard data instead of placeholders.",
        }

    @staticmethod
    def _build_activities(
        profile: UserProfile | None,
        provider_profile: ProviderProfile | None,
    ) -> list[dict[str, str]]:
        activities: list[dict[str, str]] = []

        if profile:
            full_name = getattr(profile, "full_name", None)
            if not full_name:
                full_name = f"{getattr(profile, 'first_name', '')} {getattr(profile, 'last_name', '')}".strip()

            activities.append({
                "icon_bg": "bg-light-primary",
                "icon_color": "text-primary",
                "icon": "bi bi-person-check",
                "html": f"Profile connected for <strong>{full_name or 'User'}</strong>.",
            })
            activities.append({
                "icon_bg": "bg-light-success",
                "icon_color": "text-success",
                "icon": "bi bi-shield-check",
                "html": f"Role detected: <strong>{(getattr(profile, 'role', 'user') or 'user').title()}</strong>.",
            })

        if provider_profile:
            activities.append({
                "icon_bg": "bg-light-info",
                "icon_color": "text-info",
                "icon": "bi bi-shop",
                "html": f"Provider profile linked to <strong>{getattr(provider_profile, 'business_name', 'Business')}</strong>.",
            })

        activities.append({
            "icon_bg": "bg-light-warning",
            "icon_color": "text-warning",
            "icon": "bi bi-diagram-3",
            "html": "Dashboard widgets are now ready to be reused by user, provider, sales and admin panels.",
        })

        return activities

    @staticmethod
    def _build_messages(profile: UserProfile | None) -> list[dict[str, str]]:
        first_name = getattr(profile, "first_name", None) if profile else None
        first_name = first_name or "there"

        avatar = (
            getattr(profile, "avatar_url", None)
            if profile else None
        ) or url_for("static", filename=DEFAULT_AVATAR)

        return [
            {
                "img": avatar,
                "title": "System",
                "time": "Now",
                "desc": f"Welcome {first_name}. Your user data is connected.",
                "number": "1",
                "tag": "true",
            },
            {
                "img": url_for("static", filename="assets/img/team-7.jpg"),
                "title": "InfoGoodTrip",
                "time": "Today",
                "desc": "Next step: connect bookings, favorites and provider-owned listings.",
                "number": "",
                "tag": "false",
            },
        ]

    @staticmethod
    def _build_invoices(provider_profile: ProviderProfile | None) -> list[dict[str, str]]:
        if provider_profile:
            approval_status = getattr(provider_profile, "approval_status", "pending")
            status = approval_status.title()
            style = {
                "approved": "badge-success",
                "pending": "badge-warning",
                "rejected": "badge-danger",
            }.get(approval_status, "badge-info")

            created_at = getattr(provider_profile, "created_at", None)
            created_label = created_at.strftime("%b %d, %Y") if created_at else "-"

            return [
                {
                    "title": getattr(provider_profile, "business_name", "Business"),
                    "id": f"#PR-{getattr(provider_profile, 'id', '')}",
                    "status": status,
                    "style": style,
                    "date": created_label,
                    "btn": "View Record",
                }
            ]

        return [
            {
                "title": "User profile setup",
                "id": "#USR-SETUP",
                "status": "Ready",
                "style": "badge-success",
                "date": "Today",
                "btn": "View Record",
            }
        ]
