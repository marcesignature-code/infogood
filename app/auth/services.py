from __future__ import annotations

from uuid import uuid4

from sqlalchemy.exc import SQLAlchemyError
from slugify import slugify

from app.extensions import db
from app.models.listing import Listing
from app.models.user import UserProfile


def _normalize_email(email: str | None) -> str:
    return (email or "").strip().lower()


def _split_full_name(full_name: str | None) -> tuple[str, str]:
    clean_name = (full_name or "").strip()
    if not clean_name:
        return "User", "Profile"
    parts = clean_name.split()
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], " ".join(parts[1:])


def authenticate_user(email: str | None, password: str | None) -> UserProfile | None:
    normalized_email = _normalize_email(email)
    raw_password = password or ""

    if not normalized_email or not raw_password:
        return None

    profile = UserProfile.query.filter_by(email=normalized_email).first()
    if not profile:
        return None
    if not profile.is_active:
        return None
    if not profile.check_password(raw_password):
        return None

    return profile


def create_user(
    full_name: str | None,
    email: str | None,
    password: str | None,
    role: str = "user",
    main_category: str | None = None,
    subcategory: str | None = None,
    business_name: str | None = None,
) -> UserProfile:
    normalized_email = _normalize_email(email)
    raw_password = (password or "").strip()

    if not normalized_email:
        raise ValueError("Email is required.")
    if not raw_password:
        raise ValueError("Password is required.")
    if len(raw_password) < 6:
        raise ValueError("Password must be at least 6 characters.")
    existing = UserProfile.query.filter_by(email=normalized_email).first()
    if existing:
        raise ValueError("An account with this email already exists.")

    first_name, last_name = _split_full_name(full_name)
    normalized_role = (role or "user").strip().lower()
    if normalized_role not in {"user", "provider", "admin"}:
        normalized_role = "user"

    profile = UserProfile(
        email=normalized_email,
        username=None,
        role=normalized_role,
        first_name=first_name,
        last_name=last_name,
        phone=None,
        avatar_url=None,
        is_active=True,
    )
    profile.set_password(raw_password)

    db.session.add(profile)
    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        raise

    if normalized_role == "provider":
        _create_provider_listing_draft(
            profile=profile,
            main_category=main_category,
            subcategory=subcategory,
            business_name=business_name,
        )

    return profile


def _build_unique_slug(seed_value: str) -> str:
    base = slugify(seed_value)[:150] or "new-business"
    candidate = base
    max_attempts = 8
    attempt = 0

    while Listing.query.filter_by(slug=candidate).first():
        attempt += 1
        suffix = uuid4().hex[:8]
        candidate = f"{base}-{suffix}"[:180]
        if attempt >= max_attempts:
            break
    return candidate


def _create_provider_listing_draft(
    profile: UserProfile,
    main_category: str | None,
    subcategory: str | None,
    business_name: str | None,
) -> None:
    if not profile or not profile.email:
        return

    normalized_main_category = (main_category or "").strip() or None
    normalized_subcategory = (subcategory or "").strip() or None
    normalized_name = (business_name or "").strip() or "New Business"

    existing_listing = (
        Listing.query.filter_by(provider_email=profile.email)
        .order_by(Listing.created_at.asc())
        .first()
    )
    if existing_listing:
        return

    listing = Listing(
        name=normalized_name,
        listing_name=normalized_name,
        slug=_build_unique_slug(f"{normalized_name}-{profile.email}"),
        main_category=normalized_main_category,
        subcategory=normalized_subcategory,
        provider_name=profile.full_name or normalized_name,
        provider_email=profile.email,
        email=profile.email,
        is_active=False,
        status="draft",
    )

    db.session.add(listing)
    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
