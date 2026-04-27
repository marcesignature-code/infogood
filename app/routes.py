import re
from math import ceil
from pathlib import Path
from uuid import uuid4

from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user
from slugify import slugify  # déjalo si ya lo usas en otras funciones
from werkzeug.utils import secure_filename
from app.models.bookmark import Bookmark
from app.models.listing import Listing
from app.models.newsletter_subscriber import NewsletterSubscriber
from app.models.user import UserProfile
from app.extensions import db
from app.services.dashboard_context import get_dashboard_context
from sqlalchemy import func, inspect, or_, text


main = Blueprint("main", __name__)

ALLOWED_MAIN_CATEGORIES = [
    "accommodation",
    "food_drink",
    "activities_experiences",
    "free_activities",
    "tourism_services",
]

HERO_NAV_CATEGORIES = [
    {
        "value": "accommodation",
        "label": "Accommodation",
        "subcategories": [
            {"value": "hotel", "label": "Hotel"},
            {"value": "hostel", "label": "Hostel"},
            {"value": "boutique_hotel", "label": "Boutique Hotel"},
            {"value": "hacienda_lodge", "label": "Hacienda Lodge"},
            {"value": "apartment_stay", "label": "Apartment Stay"},
            {"value": "resort", "label": "Resort"},
            {"value": "guesthouse", "label": "Guesthouse"},
            {"value": "cabin_glamping", "label": "Cabin & Glamping"},
        ],
    },
    {
        "value": "food_drink",
        "label": "Food & Drink",
        "subcategories": [
            {"value": "restaurant", "label": "Restaurant"},
            {"value": "cafe", "label": "Cafe"},
            {"value": "bakery_dessert", "label": "Bakery & Dessert"},
            {"value": "bar_pub", "label": "Bar & Pub"},
            {"value": "fine_dining", "label": "Fine Dining"},
            {"value": "local_cuisine", "label": "Local Cuisine"},
            {"value": "fast_casual", "label": "Fast Casual"},
            {"value": "rooftop_lounge", "label": "Rooftop Lounge"},
        ],
    },
    {
        "value": "activities_experiences",
        "label": "Activities & Experiences",
        "subcategories": [
            {"value": "outdoor_adventure", "label": "Outdoor Adventure"},
            {"value": "cultural_experience", "label": "Cultural Experience"},
            {"value": "nature_experience", "label": "Nature Experience"},
            {"value": "wellness_experience", "label": "Wellness Experience"},
            {"value": "city_tour", "label": "City Tour"},
            {"value": "nightlife_experience", "label": "Nightlife Experience"},
            {"value": "family_activity", "label": "Family Activity"},
            {"value": "workshop_class", "label": "Workshop & Class"},
        ],
    },
    {
        "value": "free_activities",
        "label": "Free Activities",
        "subcategories": [
            {"value": "parks_public_spaces", "label": "Parks & Public Spaces"},
            {"value": "museums_free_entry", "label": "Museums (Free Entry)"},
            {"value": "scenic_viewpoints", "label": "Scenic Viewpoints"},
            {"value": "public_cultural_activities", "label": "Public Cultural Activities"},
            {"value": "free_family_activities", "label": "Free Family Activities"},
        ],
    },
    {
        "value": "tourism_services",
        "label": "Tourism & Services",
        "subcategories": [
            {"value": "tourist_transport", "label": "Tourist Transport"},
            {"value": "tour_operator", "label": "Tour Operator"},
            {"value": "travel_agency", "label": "Travel Agency"},
            {"value": "car_rental", "label": "Car Rental"},
            {"value": "shuttle_service", "label": "Shuttle Service"},
            {"value": "guide_service", "label": "Guide Service"},
            {"value": "local_travel_support", "label": "Local Travel Support"},
        ],
    },
]

ALLOWED_SUBCATEGORIES = {
    subcategory["value"]
    for category in HERO_NAV_CATEGORIES
    for subcategory in category["subcategories"]
}

HOME_CATEGORY_META = [
    {
        "value": "accommodation",
        "label": "Accommodation",
        "icon": "bi bi-house-check",
    },
    {
        "value": "food_drink",
        "label": "Food & Drink",
        "icon": "bi bi-cup-straw",
    },
    {
        "value": "activities_experiences",
        "label": "Activities & Experiences",
        "icon": "bi bi-lamp",
    },
    {
        "value": "free_activities",
        "label": "Free Activities",
        "icon": "bi bi-stars",
    },
    {
        "value": "tourism_services",
        "label": "Tourism & Services",
        "icon": "bi bi-briefcase",
    },
]

HOME_POPULAR_LISTINGS_LIMIT = 8

HOME_LATEST_UPDATES_LIMIT = 3
HOME_LATEST_UPDATES_PLACEHOLDERS = [
    {
        "title": "New Weekend Routes Added for Quito and Cotopaxi",
        "excerpt": "We added new route collections to help travelers compare stay, food, and activity options faster.",
        "post_type": "Announcement",
        "display_date": "Apr 10, 2026",
        "cover_image_url": "/static/assets/img/blog-1.jpg",
    },
    {
        "title": "April Partner Promotions: Local Tours and Family Plans",
        "excerpt": "Discover seasonal promotions from tourism partners with clear pricing and updated booking links.",
        "post_type": "Promotion",
        "display_date": "Apr 5, 2026",
        "cover_image_url": "/static/assets/img/blog-2.jpg",
    },
    {
        "title": "How to Build a 2-Day Escape with InfoGoodTrip",
        "excerpt": "A practical planning guide to combine accommodation, food, and experiences in one itinerary.",
        "post_type": "Blog Post",
        "display_date": "Mar 29, 2026",
        "cover_image_url": "/static/assets/img/blog-3.jpg",
    },
]

# Temporary home placeholders until platform reviews are sourced from external channels.
HOME_PLATFORM_REVIEWS = [
    {
        "reviewer_name": "Daniel Morgan",
        "reviewer_role": "Frequent Traveler",
        "rating": 5,
        "review_text": "InfoGoodTrip helped me compare options quickly and plan a full weekend without jumping between multiple sites.",
    },
    {
        "reviewer_name": "Sophia Reed",
        "reviewer_role": "Content Creator",
        "rating": 4,
        "review_text": "The category filters are clear and practical. I can find places that fit my plans in just a few minutes.",
    },
    {
        "reviewer_name": "Ethan Walker",
        "reviewer_role": "Small Business Owner",
        "rating": 5,
        "review_text": "I like how the platform balances useful information with a clean interface. It feels organized and easy to trust.",
    },
    {
        "reviewer_name": "Maya Thompson",
        "reviewer_role": "Family Trip Planner",
        "rating": 4,
        "review_text": "InfoGoodTrip makes trip planning simpler for families. The listings are easier to browse than most directories I have used.",
    },
]

NEWSLETTER_EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
NEWSLETTER_STATUS_MESSAGES = {
    "saved": "Thanks. Your email has been saved. You can complete your profile below.",
    "duplicate": "This email is already subscribed. You can still update profile details below.",
    "invalid_email": "Please enter a valid email address.",
    "profile_updated": "Subscriber profile updated successfully.",
    "subscriber_not_found": "Please subscribe with your email first.",
    "profile_email_invalid": "Please provide a valid email in step 2.",
    "profile_email_taken": "That email is already used by another subscriber.",
}
ALLOWED_AVATAR_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}


def _avatar_extension(filename):
    name = (filename or "").strip()
    if "." not in name:
        return ""
    return name.rsplit(".", 1)[1].lower()

@main.context_processor
def inject_slugify():
    return {'slugify': slugify}


def _resolve_actor_profile():
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


def _bookmarked_listing_id_strings(profile):
    if not profile:
        return set()
    try:
        listing_ids = (
            db.session.query(Bookmark.listing_id)
            .filter(Bookmark.user_id == profile.id)
            .all()
        )
        return {str(row[0]) for row in listing_ids if row and row[0]}
    except Exception:
        db.session.rollback()
        return set()


@main.context_processor
def inject_bookmark_state():
    profile = _resolve_actor_profile()
    return {"bookmarked_listing_ids": _bookmarked_listing_id_strings(profile)}


@main.context_processor
def inject_navigation_role_context():
    role = "guest"
    dashboard_home_url = "/dashboard-user/"
    provider_public_listing_url = None

    try:
        if current_user.is_authenticated:
            role = (getattr(current_user, "role", "") or "user").strip().lower()
            if role == "provider":
                dashboard_home_url = "/dashboard/provider"
                listing = _resolve_provider_listing(current_user)
                provider_public_listing_url = _provider_public_listing_url(listing)
            elif role == "admin":
                dashboard_home_url = "/dashboard/admin"
            elif role == "sales":
                dashboard_home_url = "/dashboard/sales"
            else:
                dashboard_home_url = "/dashboard-user/"
    except Exception:
        role = "guest"
        dashboard_home_url = "/dashboard-user/"
        provider_public_listing_url = None

    return {
        "nav_role": role,
        "nav_dashboard_home_url": dashboard_home_url,
        "nav_provider_public_listing_url": provider_public_listing_url,
    }


def _normalize_email(value):
    return (value or "").strip().lower()


def _is_valid_email(value):
    return bool(NEWSLETTER_EMAIL_REGEX.match(_normalize_email(value)))


def _home_with_newsletter_state(status, email="", step=1):
    params = {
        "newsletter_status": status,
        "newsletter_step": str(step),
    }
    if email:
        params["newsletter_email"] = email
    return redirect(url_for("main.index", **params))


def _is_ajax_request():
    return (
        request.headers.get("X-Requested-With", "").lower() == "xmlhttprequest"
        or "application/json" in (request.headers.get("Accept", "").lower())
    )


def _format_display_date(raw_value):
    if not raw_value:
        return "-"
    if hasattr(raw_value, "strftime"):
        return raw_value.strftime("%b %d, %Y")
    raw_text = str(raw_value)
    return raw_text[:10] if len(raw_text) >= 10 else raw_text


def _select_latest_updates(limit=HOME_LATEST_UPDATES_LIMIT):
    fallback = HOME_LATEST_UPDATES_PLACEHOLDERS[:limit]
    try:
        inspector = inspect(db.engine)
        if not inspector.has_table("posts"):
            return fallback

        columns = {column["name"] for column in inspector.get_columns("posts")}
        if not columns:
            return fallback

        title_col = next((c for c in ["title", "name", "headline"] if c in columns), None)
        if not title_col:
            return fallback

        excerpt_col = next((c for c in ["excerpt", "summary", "short_description", "description", "content"] if c in columns), None)
        post_type_col = next((c for c in ["post_type", "type", "category"] if c in columns), None)
        published_col = next((c for c in ["published_at", "publish_date", "published_on", "created_at", "date"] if c in columns), None)
        image_col = next((c for c in ["cover_image_url", "cover_image", "image_url", "featured_image_url", "img"] if c in columns), None)
        status_col = next((c for c in ["status", "is_published", "published", "is_active"] if c in columns), None)
        order_col = published_col or ("id" if "id" in columns else title_col)

        query_parts = [f"{title_col} AS title"]
        query_parts.append(f"{excerpt_col} AS excerpt" if excerpt_col else "'' AS excerpt")
        query_parts.append(f"{post_type_col} AS post_type" if post_type_col else "'Update' AS post_type")
        query_parts.append(f"{published_col} AS published_at" if published_col else "NULL AS published_at")
        query_parts.append(f"{image_col} AS cover_image_url" if image_col else "NULL AS cover_image_url")

        where_parts = []
        if status_col == "status":
            where_parts.append("status IN ('published', 'active')")
        elif status_col in {"is_published", "published", "is_active"}:
            where_parts.append(f"{status_col} = true")

        sql = f"SELECT {', '.join(query_parts)} FROM posts"
        if where_parts:
            sql += f" WHERE {' AND '.join(where_parts)}"
        sql += f" ORDER BY {order_col} DESC LIMIT :limit"

        rows = db.session.execute(text(sql), {"limit": limit}).mappings().all()
        items = []
        for row in rows:
            title = (row.get("title") or "").strip()
            if not title:
                continue
            items.append(
                {
                    "title": title,
                    "excerpt": (row.get("excerpt") or "").strip() or "Latest platform update from InfoGoodTrip.",
                    "post_type": (row.get("post_type") or "Update").strip().title(),
                    "display_date": _format_display_date(row.get("published_at")),
                    "cover_image_url": row.get("cover_image_url") or "/static/assets/img/blog-1.jpg",
                }
            )

        return items if items else fallback
    except Exception:
        db.session.rollback()
        return fallback


@main.route("/newsletter/subscribe", methods=["POST"])
def newsletter_subscribe_step_1():
    email = _normalize_email(request.form.get("email"))
    if not _is_valid_email(email):
        if _is_ajax_request():
            return jsonify(
                {
                    "ok": False,
                    "status": "invalid_email",
                    "email": "",
                    "message": NEWSLETTER_STATUS_MESSAGES["invalid_email"],
                }
            ), 400
        return _home_with_newsletter_state("invalid_email", step=1)

    existing = NewsletterSubscriber.query.filter_by(email=email).first()
    if existing:
        if not existing.is_active:
            existing.is_active = True
            db.session.commit()
        if _is_ajax_request():
            return jsonify(
                {
                    "ok": True,
                    "status": "duplicate",
                    "email": email,
                    "message": NEWSLETTER_STATUS_MESSAGES["duplicate"],
                }
            )
        return _home_with_newsletter_state("duplicate", email=email, step=2)

    subscriber = NewsletterSubscriber(
        email=email,
        source="home_newsletter",
        language_preference="en",
        is_active=True,
    )
    db.session.add(subscriber)
    db.session.commit()
    if _is_ajax_request():
        return jsonify(
            {
                "ok": True,
                "status": "saved",
                "email": email,
                "message": NEWSLETTER_STATUS_MESSAGES["saved"],
            }
        )
    return _home_with_newsletter_state("saved", email=email, step=2)


@main.route("/newsletter/profile", methods=["POST"])
def newsletter_subscribe_step_2():
    original_email = _normalize_email(request.form.get("original_email"))
    if not original_email:
        return _home_with_newsletter_state("subscriber_not_found", step=1)

    subscriber = NewsletterSubscriber.query.filter_by(email=original_email).first()
    if not subscriber:
        return _home_with_newsletter_state("subscriber_not_found", step=1)

    submitted_email = _normalize_email(request.form.get("email")) or original_email
    if not _is_valid_email(submitted_email):
        return _home_with_newsletter_state("profile_email_invalid", email=original_email, step=2)

    if submitted_email != original_email:
        other = NewsletterSubscriber.query.filter_by(email=submitted_email).first()
        if other and other.id != subscriber.id:
            return _home_with_newsletter_state("profile_email_taken", email=original_email, step=2)

    language_preference = (request.form.get("language_preference") or "").strip().lower() or "en"
    subscriber.email = submitted_email
    subscriber.full_name = (request.form.get("full_name") or "").strip() or None
    subscriber.language_preference = language_preference
    subscriber.country = (request.form.get("country") or "").strip() or None
    subscriber.city = (request.form.get("city") or "").strip() or None
    subscriber.interests = (request.form.get("interests") or "").strip() or None
    subscriber.notes = (request.form.get("notes") or "").strip() or None
    subscriber.is_active = True

    db.session.commit()
    return _home_with_newsletter_state("profile_updated", email=submitted_email, step=2)

@main.route("/")
def index():
    newsletter_step = (request.args.get("newsletter_step") or "").strip() == "2"
    newsletter_email = _normalize_email(request.args.get("newsletter_email"))
    newsletter_status = (request.args.get("newsletter_status") or "").strip()
    newsletter_status_message = NEWSLETTER_STATUS_MESSAGES.get(newsletter_status, "")

    newsletter_subscriber = None
    if newsletter_email:
        newsletter_subscriber = NewsletterSubscriber.query.filter_by(email=newsletter_email).first()

    categories = []

    for category_meta in HOME_CATEGORY_META:
        category_value = category_meta["value"]
        if category_value == "free_activities":
            count = Listing.query.filter(
                Listing.is_active.is_(True),
                Listing.is_free.is_(True),
            ).count()
        else:
            count = Listing.query.filter(
                Listing.is_active.is_(True),
                Listing.main_category == category_value,
            ).count()

        categories.append(
            {
                "value": category_value,
                "title": category_meta["label"],
                "icon": category_meta["icon"],
                "count": count,
            }
        )

    selected_listings = []
    selected_ids = set()

    def _append_unique(rows):
        for row in rows:
            if len(selected_listings) >= HOME_POPULAR_LISTINGS_LIMIT:
                break
            if row.id in selected_ids:
                continue
            selected_listings.append(row)
            selected_ids.add(row.id)

    home_featured = (
        Listing.query.filter(
            Listing.is_active.is_(True),
            Listing.is_home_featured.is_(True),
        )
        .order_by(Listing.home_feature_rank.asc(), Listing.created_at.desc())
        .limit(HOME_POPULAR_LISTINGS_LIMIT)
        .all()
    )
    _append_unique(home_featured)

    if len(selected_listings) < HOME_POPULAR_LISTINGS_LIMIT:
        featured = (
            Listing.query.filter(
                Listing.is_active.is_(True),
                Listing.is_featured.is_(True),
            )
            .order_by(Listing.created_at.desc())
            .limit(HOME_POPULAR_LISTINGS_LIMIT * 3)
            .all()
        )
        _append_unique(featured)

    if len(selected_listings) < HOME_POPULAR_LISTINGS_LIMIT:
        recent = (
            Listing.query.filter(Listing.is_active.is_(True))
            .order_by(Listing.created_at.desc())
            .limit(HOME_POPULAR_LISTINGS_LIMIT * 5)
            .all()
        )
        _append_unique(recent)

    latest_updates = _select_latest_updates()

    return render_template(
        "pages/index.html",
        categories=categories,
        popular_listings=selected_listings,
        platform_reviews=HOME_PLATFORM_REVIEWS,
        latest_updates=latest_updates,
        hero_nav_categories=HERO_NAV_CATEGORIES,
        newsletter_step=newsletter_step,
        newsletter_email_prefill=newsletter_email,
        newsletter_status=newsletter_status,
        newsletter_status_message=newsletter_status_message,
        newsletter_subscriber=newsletter_subscriber,
    )


@main.route("/home-splash/")
def home_splash():
    return render_template("pages/home-splash.html")


@main.route("/home-map/")
def home_map():
    return render_template("pages/home-map.html")


GRID_PER_PAGE = 12
GRID_TEXT_SEARCH_COLUMNS = (
    Listing.listing_name,
    Listing.name,
    Listing.short_description,
    Listing.long_description,
    Listing.main_category,
    Listing.subcategory,
    Listing.search_keywords,
    Listing.tags_csv,
    Listing.environment,
    Listing.occasion,
)
GRID_LOCATION_SEARCH_COLUMNS = (
    Listing.country,
    Listing.province,
    Listing.city,
    Listing.canton,
    Listing.zone,
    Listing.neighborhood,
    Listing.address,
)
GRID_INACTIVE_FILTER_KEYS = {
    "distance",
    "distance_km",
    "radius",
    "radius_km",
    "my_range",
    "lat",
    "lng",
    "latitude",
    "longitude",
}
GRID_SORT_OPTIONS = {
    "default": "Default Order",
    "highest_rated": "Highest Rated",
    "most_reviewed": "Most Reviewed",
    "newest": "Newest Listings",
    "oldest": "Oldest Listings",
    "featured": "Featured Listings",
    "most_viewed": "Most Viewed",
    "a_to_z": "Sort By A to Z",
}
GRID_SUBCATEGORY_OPTIONS = {
    "food_drink": [
        ("Restaurant", "restaurant"),
        ("Cafe", "cafe"),
        ("Bar", "bar"),
        ("Fine Dining", "fine_dining"),
        ("Bakery", "bakery"),
    ],
    "accommodation": [
        ("Hotel", "hotel"),
        ("Hostel", "hostel"),
        ("Boutique Hotel", "boutique_hotel"),
        ("Apartment", "apartment"),
        ("Lodge", "lodge"),
    ],
    "activities_experiences": [
        ("Tour", "tour"),
        ("Experience", "experience"),
        ("Adventure", "adventure"),
        ("Cultural Activity", "cultural_activity"),
        ("Wellness", "wellness"),
    ],
    "tourism_services": [
        ("Travel Agency", "travel_agency"),
        ("Transportation", "transportation"),
        ("Guide", "guide"),
        ("Car Rental", "car_rental"),
        ("Airport Transfer", "airport_transfer"),
    ],
    "free_activities": [
        ("Park", "park"),
        ("Museum", "museum"),
        ("Viewpoint", "viewpoint"),
        ("Historic Site", "historic_site"),
        ("Cultural Site", "cultural_site"),
    ],
}


def _parse_grid_layout_filters():
    query_text = (request.args.get("q") or "").strip()
    location_text = (request.args.get("location") or "").strip()
    category = (request.args.get("category") or "").strip().lower()
    subcategory = (request.args.get("subcategory") or "").strip().lower()
    price_level = (request.args.get("price_level") or "").strip()
    status = (request.args.get("status") or "").strip().lower()
    rating_min_raw = (request.args.get("rating_min") or "").strip()
    sort = (request.args.get("sort") or "default").strip().lower()
    amenity_parking = (request.args.get("parkings") or "").strip().lower() in {
        "1",
        "true",
        "on",
        "yes",
    }
    amenity_freewifi = (request.args.get("freewifi") or "").strip().lower() in {
        "1",
        "true",
        "on",
        "yes",
    }
    amenity_petallow = (request.args.get("petallow") or "").strip().lower() in {
        "1",
        "true",
        "on",
        "yes",
    }
    amenity_breakfast = (request.args.get("breakfast") or "").strip().lower() in {
        "1",
        "true",
        "on",
        "yes",
    }
    page = request.args.get("page", 1, type=int) or 1
    rating_min = None

    if category not in ALLOWED_MAIN_CATEGORIES:
        category = ""
    valid_subcategories = {
        option_value
        for _label, option_value in GRID_SUBCATEGORY_OPTIONS.get(category, [])
    } if category else set()
    if not category or subcategory not in valid_subcategories:
        subcategory = ""
    if sort not in GRID_SORT_OPTIONS:
        sort = "default"
    if rating_min_raw:
        try:
            parsed_rating = float(rating_min_raw)
            if parsed_rating in {3.0, 4.0, 5.0}:
                rating_min = parsed_rating
        except (TypeError, ValueError):
            rating_min = None
    if page < 1:
        page = 1

    return {
        "query_text": query_text,
        "location_text": location_text,
        "category": category,
        "subcategory": subcategory,
        "price_level": price_level,
        "status": status,
        "rating_min": rating_min,
        "sort": sort,
        "amenity_parking": amenity_parking,
        "amenity_freewifi": amenity_freewifi,
        "amenity_petallow": amenity_petallow,
        "amenity_breakfast": amenity_breakfast,
        "page": page,
    }


def _apply_grid_layout_filters(base_query, filters):
    query = base_query

    if filters["query_text"]:
        query_like = f"%{filters['query_text']}%"
        query = query.filter(
            or_(*(column.ilike(query_like) for column in GRID_TEXT_SEARCH_COLUMNS))
        )

    if filters["location_text"]:
        location_like = f"%{filters['location_text']}%"
        query = query.filter(
            or_(
                *(column.ilike(location_like) for column in GRID_LOCATION_SEARCH_COLUMNS)
            )
        )

    if filters["category"]:
        query = query.filter(Listing.main_category == filters["category"])
    if filters["subcategory"]:
        query = query.filter(Listing.subcategory == filters["subcategory"])
    if filters["price_level"]:
        query = query.filter(Listing.price_level == filters["price_level"])
    if filters["status"]:
        query = query.filter(Listing.status == filters["status"])
    if filters["rating_min"] is not None:
        query = query.filter(func.coalesce(Listing.rating_avg, 0) >= filters["rating_min"])
    if filters["amenity_parking"]:
        query = query.filter(Listing.parking_available.is_(True))
    if filters["amenity_freewifi"]:
        query = query.filter(Listing.wifi_available.is_(True))
    if filters["amenity_petallow"]:
        query = query.filter(Listing.pet_friendly.is_(True))
    if filters["amenity_breakfast"]:
        query = query.filter(Listing.breakfast_included.is_(True))

    return query


def _apply_grid_layout_default_order(query):
    # Step 1: oldest imported listings first, with stable fallback keys.
    return query.order_by(
        Listing.created_at.asc().nulls_last(),
        Listing.listing_name.asc().nulls_last(),
        Listing.id.asc(),
    )


def _apply_grid_layout_sort(query, sort_key):
    if sort_key == "highest_rated":
        return query.order_by(
            func.coalesce(Listing.rating_avg, 0).desc(),
            Listing.created_at.asc().nulls_last(),
            Listing.id.asc(),
        )
    if sort_key == "most_reviewed":
        return query.order_by(
            func.coalesce(Listing.reviews_count, 0).desc(),
            Listing.created_at.asc().nulls_last(),
            Listing.id.asc(),
        )
    if sort_key == "newest":
        return query.order_by(
            Listing.created_at.desc().nulls_last(),
            Listing.listing_name.asc().nulls_last(),
            Listing.id.asc(),
        )
    if sort_key == "oldest":
        return _apply_grid_layout_default_order(query)
    if sort_key == "featured":
        sort_priority_column = getattr(Listing, "sort_priority", Listing.home_feature_rank)
        return query.order_by(
            Listing.is_featured.desc(),
            sort_priority_column.asc().nulls_last(),
            Listing.created_at.asc().nulls_last(),
            Listing.id.asc(),
        )
    if sort_key == "most_viewed":
        return query.order_by(
            func.coalesce(Listing.view_count, 0).desc(),
            Listing.created_at.asc().nulls_last(),
            Listing.id.asc(),
        )
    if sort_key == "a_to_z":
        return query.order_by(
            Listing.listing_name.asc().nulls_last(),
            Listing.created_at.asc().nulls_last(),
            Listing.id.asc(),
        )
    return _apply_grid_layout_default_order(query)


def _grid_query_params_without_inactive(raw_params):
    params = dict(raw_params)
    for key in GRID_INACTIVE_FILTER_KEYS:
        params.pop(key, None)
    return params


@main.route("/grid-layout-01/")
def grid_layout_01():
    filters = _parse_grid_layout_filters()
    page = filters["page"]
    per_page = GRID_PER_PAGE

    query = Listing.query.filter(Listing.is_active.is_(True))
    query = _apply_grid_layout_filters(query, filters)

    total_results = query.count()
    total_pages = ceil(total_results / per_page) if total_results > 0 else 0

    if total_pages == 0 and page != 1:
        redirect_args = request.args.to_dict(flat=True)
        redirect_args["page"] = 1
        return redirect(url_for("main.grid_layout_01", **redirect_args))

    if total_pages > 0 and page > total_pages:
        redirect_args = request.args.to_dict(flat=True)
        redirect_args["page"] = total_pages
        return redirect(url_for("main.grid_layout_01", **redirect_args))

    ordered_query = _apply_grid_layout_sort(query, filters["sort"])
    offset = (page - 1) * per_page
    listings = ordered_query.offset(offset).limit(per_page).all()
    pagination_args = _grid_query_params_without_inactive(
        request.args.to_dict(flat=True)
    )
    pagination_args.pop("page", None)

    def build_page_url(target_page):
        params = dict(pagination_args)
        params["page"] = target_page
        return url_for("main.grid_layout_01", **params)

    def build_filter_url(**updates):
        params = _grid_query_params_without_inactive(request.args.to_dict(flat=True))
        for key, value in updates.items():
            if value is None or value == "":
                params.pop(key, None)
            else:
                params[key] = value
        params["page"] = 1
        return url_for("main.grid_layout_01", **params)

    def build_remove_filter_url(*keys):
        params = _grid_query_params_without_inactive(request.args.to_dict(flat=True))
        for key in keys:
            params.pop(key, None)
        params["page"] = 1
        return url_for("main.grid_layout_01", **params)

    category_labels = {item["value"]: item["label"] for item in HOME_CATEGORY_META}
    subcategory_labels = {
        subcategory_item["value"]: subcategory_item["label"]
        for category_item in HERO_NAV_CATEGORIES
        for subcategory_item in category_item["subcategories"]
    }

    active_filters = []
    if filters["query_text"]:
        active_filters.append(
            {
                "label": f"Search: {filters['query_text']}",
                "remove_url": build_remove_filter_url("q"),
            }
        )
    if filters["location_text"]:
        active_filters.append(
            {
                "label": f"Location: {filters['location_text']}",
                "remove_url": build_remove_filter_url("location"),
            }
        )
    if filters["category"]:
        active_filters.append(
            {
                "label": f"Category: {category_labels.get(filters['category'], filters['category'])}",
                "remove_url": build_remove_filter_url("category", "subcategory"),
            }
        )
    if filters["subcategory"]:
        active_filters.append(
            {
                "label": f"Subcategory: {subcategory_labels.get(filters['subcategory'], filters['subcategory'])}",
                "remove_url": build_remove_filter_url("subcategory"),
            }
        )
    if filters["rating_min"] is not None:
        active_filters.append(
            {
                "label": f"Rating {filters['rating_min']:.1f}+",
                "remove_url": build_remove_filter_url("rating_min"),
            }
        )
    if filters["price_level"]:
        active_filters.append(
            {
                "label": f"Price: {filters['price_level']}",
                "remove_url": build_remove_filter_url("price_level"),
            }
        )
    if filters["amenity_parking"]:
        active_filters.append(
            {
                "label": "Parking",
                "remove_url": build_remove_filter_url("parkings"),
            }
        )
    if filters["amenity_freewifi"]:
        active_filters.append(
            {
                "label": "Free WiFi",
                "remove_url": build_remove_filter_url("freewifi"),
            }
        )
    if filters["amenity_petallow"]:
        active_filters.append(
            {
                "label": "Pet Allow",
                "remove_url": build_remove_filter_url("petallow"),
            }
        )
    if filters["amenity_breakfast"]:
        active_filters.append(
            {
                "label": "Breakfast",
                "remove_url": build_remove_filter_url("breakfast"),
            }
        )
    if filters["status"]:
        active_filters.append(
            {
                "label": f"Status: {filters['status']}",
                "remove_url": build_remove_filter_url("status"),
            }
        )
    if filters["sort"] != "default":
        active_filters.append(
            {
                "label": f"Sort: {GRID_SORT_OPTIONS.get(filters['sort'], filters['sort'])}",
                "remove_url": build_remove_filter_url("sort"),
            }
        )

    return render_template(
        "pages/grid-layout-01.html",
        listings=listings,
        page=page,
        per_page=per_page,
        total_results=total_results,
        total_pages=total_pages,
        search_query=filters["query_text"],
        search_location=filters["location_text"],
        selected_category=filters["category"],
        selected_subcategory=filters["subcategory"],
        grid_subcategory_options=GRID_SUBCATEGORY_OPTIONS,
        selected_price_level=filters["price_level"],
        selected_status=filters["status"],
        selected_rating_min=filters["rating_min"],
        selected_sort=filters["sort"],
        selected_sort_label=GRID_SORT_OPTIONS.get(filters["sort"], GRID_SORT_OPTIONS["default"]),
        selected_amenity_parking=filters["amenity_parking"],
        selected_amenity_freewifi=filters["amenity_freewifi"],
        selected_amenity_petallow=filters["amenity_petallow"],
        selected_amenity_breakfast=filters["amenity_breakfast"],
        active_filters=active_filters,
        clear_all_url=url_for("main.grid_layout_01"),
        build_page_url=build_page_url,
        build_filter_url=build_filter_url,
        allowed_main_categories=ALLOWED_MAIN_CATEGORIES,
    )


@main.route("/bookmark/toggle/<uuid:listing_id>", methods=["POST"])
def bookmark_toggle(listing_id):
    profile = _resolve_actor_profile()
    if not profile:
        return jsonify({"ok": False, "error": "Authentication required."}), 401

    listing = Listing.query.filter_by(id=listing_id, is_active=True).first()
    if not listing:
        return jsonify({"ok": False, "error": "Listing not found."}), 404

    try:
        bookmark = Bookmark.query.filter_by(
            user_id=profile.id,
            listing_id=listing.id,
        ).first()

        if bookmark:
            db.session.delete(bookmark)
            saved = False
        else:
            db.session.add(Bookmark(user_id=profile.id, listing_id=listing.id))
            saved = True

        db.session.commit()
        return jsonify({
            "ok": True,
            "saved": saved,
            "listing_id": str(listing.id),
        })
    except Exception:
        db.session.rollback()
        return jsonify({"ok": False, "error": "Could not update bookmark."}), 500


@main.route("/grid-layout-02/")
def grid_layout_02():
    return render_template("pages/grid-layout-02.html")


@main.route("/list-layout-01/")
def list_layout_01():
    return render_template("pages/list-layout-01.html")


@main.route("/list-layout-02/")
def list_layout_02():
    return render_template("pages/list-layout-02.html")


@main.route("/half-map-01/")
def half_map_01():
    return render_template("pages/half-map-01.html")


@main.route("/half-map-05/")
def half_map_05():
    return render_template("pages/half-map-05.html")


@main.route("/single-listing-01/")
def listing_01_list_or_default():
    listings = [
        {
            'id' : 1,
            'img' : '/static/assets/img/single-1.jpg',
            'title' : 'Liman Restaurant',
            'reviews' : '42k Reviews',
        }
    ]
    listing = listings[0]
    return render_template("pages/single-listing-01.html", listing=listing)


@main.route("/single-listing-01/<string:title>/")
def single_listing_01(title):
    listings = [
        {
            'id' : 1,
            'img' : '/static/assets/img/list-1.jpg',
            'img1' : '/static/assets/img/team-1.jpg',
            'title' : 'The Big Bumbble Gym',
            'desc' : 'Cicero famously orated against his political.',
            'number' : '+42 515 635 4758',
            'miles' : '2.4 miles',
            'name' : 'Fitness',
            'icon' : 'fa-solid fa-dumbbell',
            'span' : 'catIcon cats-1',
            'plus' : '+2',
            'rating' : '4.5',
            'avarage' : 'good',
            'reviews' : '46 Reviews',
            'btn' : 'Open',
            'color' : 'listOpen',
            'dollar' : '$$$',
            'btn1' : 'Featured',
            'tag' : 'true',
        },
        {
            'id' : 2,
            'img' : '/static/assets/img/list-2.jpg',
            'img1' : '/static/assets/img/team-2.jpg',
            'title' : 'Greenvally Real Estate',
            'desc' : 'Cicero famously orated against his political.',
            'number' : '+42 515 635 6150',
            'miles' : '3.7 miles',
            'name' : 'Real Estate',
            'icon' : 'bi bi-house-check',
            'span' : 'catIcon cats-2',
            'plus' : '+2',
            'rating' : '4.3',
            'avarage' : 'midium',
            'reviews' : '35 Reviews',
            'btn' : 'Open',
            'color' : 'listOpen',
            'dollar' : '$$$$',
            'btn1' : '',
            'tag' : 'false',
        },
        {
            'id' : 3,
            'img' : '/static/assets/img/list-3.jpg',
            'img1' : '/static/assets/img/team-3.jpg',
            'title' : 'Shree Wedding Planner',
            'desc' : 'Cicero famously orated against his political.',
            'number' : '+42 515 635 4785',
            'miles' : '2.7 miles',
            'name' : 'Weddings',
            'icon' : 'bi bi-lamp',
            'span' : 'catIcon cats-3',
            'plus' : '+1',
            'rating' : '4.8',
            'avarage' : 'excellent py-1 px-2 fw-semibold',
            'reviews' : '12 Reviews',
            'btn' : 'Closed',
            'color' : 'listClose',
            'dollar' : '$$$',
            'btn1' : 'Featured',
            'tag' : 'true',
        },
        {
            'id' : 4,
            'img' : '/static/assets/img/list-4.jpg',
            'img1' : '/static/assets/img/team-4.jpg',
            'title' : 'The Blue Ley Light',
            'desc' : 'Cicero famously orated against his political.',
            'number' : '+42 515 635 6358',
            'miles' : '5.2 miles',
            'name' : 'Restaurant',
            'icon' : 'bi bi-cup-straw',
            'span' : 'catIcon cats-4',
            'plus' : '+1',
            'rating' : '4.6',
            'avarage' : 'good',
            'reviews' : '72 Reviews',
            'btn' : 'Open',
            'color' : 'listOpen',
            'dollar' : '$$$$',
            'btn1' : '',
            'tag' : 'false',
        },
        {
            'id' : 5,
            'img' : '/static/assets/img/list-5.jpg',
            'img1' : '/static/assets/img/team-5.jpg',
            'title' : 'Shreya Study Center',
            'desc' : 'Cicero famously orated against his political.',
            'number' : '+42 515 635 0210',
            'miles' : '3.8 miles',
            'name' : 'Education',
            'icon' : 'bi bi-mortarboard',
            'span' : 'catIcon cats-5',
            'plus' : '+1',
            'rating' : '4.2',
            'avarage' : 'midium',
            'reviews' : '112 Reviews',
            'btn' : 'Closed',
            'color' : 'listClose',
            'dollar' : '$$$',
            'btn1' : 'Featured',
            'tag' : 'true',
        },
        {
            'id' : 6,
            'img' : '/static/assets/img/list-6.jpg',
            'img1' : '/static/assets/img/team-6.jpg',
            'title' : 'Mahroom Garage & Workshop',
            'desc' : 'Cicero famously orated against his political.',
            'number' : '+42 515 635 3251',
            'miles' : '2.4 miles',
            'name' : 'Showroom',
            'icon' : 'bi bi-backpack',
            'span' : 'catIcon cats-6',
            'plus' : '+1',
            'rating' : '4.9',
            'avarage' : 'excellent',
            'reviews' : '52 Reviews',
            'btn' : 'Open',
            'color' : 'listOpen',
            'dollar' : '$$$$',
            'btn1' : '',
            'tag' : 'false',
        },
        {
            'id' : 7,
            'img' : '/static/assets/img/list-9.jpg',
            'img1' : '/static/assets/img/team-7.jpg',
            'title' : 'The Great Dream Palace',
            'desc' : 'Cicero famously orated against his political.',
            'number' : '+42 515 635 5426',
            'miles' : '4.2 miles',
            'name' : 'Eat & Drink',
            'icon' : 'bi bi-cup-hot',
            'span' : 'catIcon cats-7',
            'plus' : '+2',
            'rating' : '4.9',
            'avarage' : 'excellent',
            'reviews' : '42 Reviews',
            'btn' : 'Closed',
            'color' : 'listClose',
            'dollar' : '$$$',
            'btn1' : 'Featured',
            'tag' : 'true',
        },
        {
            'id' : 8,
            'img' : '/static/assets/img/list-8.jpg',
            'img1' : '/static/assets/img/team-8.jpg',
            'title' : 'Agroo Spa & Massage Center',
            'desc' : 'Cicero famously orated against his political.',
            'number' : '+42 515 635 2136',
            'miles' : '1.2 miles',
            'name' : 'Spa & Beauty',
            'icon' : 'bi bi-basket2',
            'span' : 'catIcon cats-8',
            'plus' : '+1',
            'rating' : '4.7',
            'avarage' : 'good',
            'reviews' : '76 Reviews',
            'btn' : 'Open',
            'color' : 'listOpen',
            'dollar' : '$$$',
            'btn1' : 'Featured',
            'tag' : 'true',
        }
    ]
    selected_listing = next((listing for listing in listings if slugify(listing['title']) == title), None)

    if selected_listing:
        return render_template('pages/single-listing-01.html', listing=selected_listing)
    else:
        return "listing not found", 404


@main.route("/single-listing-02/")
def listing_02_list_or_default():
    listings2 = [
        {
            'id' : 1,
            'img' : '/static/assets/img/single-2.jpg',
            'title' : 'Sangam Apartment',
            'location' : 'Old Paris, France',
        }
    ]
    listing2 = listings2[0]
    return render_template("pages/single-listing-02.html", listing2=listing2)


@main.route("/single-listing-02/<string:title>/")
def single_listing_02(title):
    listings2 = [
        {
            'id' : 1,
            'img' : '/static/assets/img/list-1.jpg',
            'img1' : '/static/assets/img/team-1.jpg',
            'title' : 'The Big Bumbble Gym',
            'number' : '+42 515 635 4758',
            'location' : 'Jakarta, USA',
            'name' : 'Health & Fitness',
            'icon' : 'fa-solid fa-dumbbell',
            'span' : 'catIcon cats-1',
            'reviews' : '42 Reviews',
            'btn' : 'Open',
            'color' : 'listOpen',
            'dollar' : '$$$',
            'btn1' : 'Featured',
            'tag' : 'true',
        },
        {
            'id' : 2,
            'img' : '/static/assets/img/list-2.jpg',
            'img1' : '/static/assets/img/team-2.jpg',
            'title' : 'Greenvally Real Estate',
            'number' : '+42 515 635 6150',
            'location' : 'Jakarta, USA',
            'name' : 'Real Estate',
            'icon' : 'bi bi-house-check',
            'span' : 'catIcon cats-2',
            'reviews' : '39 Reviews',
            'btn' : 'Closed',
            'color' : 'listClose',
            'dollar' : '$$$$',
            'btn1' : '',
            'tag' : 'false',
        },
        {
            'id' : 3,
            'img' : '/static/assets/img/list-3.jpg',
            'img1' : '/static/assets/img/team-3.jpg',
            'title' : 'Shree Wedding Planner',
            'number' : '+42 515 635 4785',
            'location' : 'Jakarta, USA',
            'name' : 'Wedding & Evemts',
            'icon' : 'bi bi-lamp',
            'span' : 'catIcon cats-3',
            'reviews' : '65 Reviews',
            'btn' : 'Open',
            'color' : 'listOpen',
            'dollar' : '$$$',
            'btn1' : 'Featured',
            'tag' : 'true',
        },
        {
            'id' : 4,
            'img' : '/static/assets/img/list-4.jpg',
            'img1' : '/static/assets/img/team-4.jpg',
            'title' : 'The Blue Ley Light',
            'number' : '+42 515 635 6358',
            'location' : 'Jakarta, USA',
            'name' : 'Restaurant',
            'icon' : 'bi bi-cup-straw',
            'span' : 'catIcon cats-4',
            'reviews' : '152 Reviews',
            'btn' : 'Open',
            'color' : 'listOpen',
            'dollar' : '$$$$',
            'btn1' : '',
            'tag' : 'false',
        },
        {
            'id' : 5,
            'img' : '/static/assets/img/list-5.jpg',
            'img1' : '/static/assets/img/team-5.jpg',
            'title' : 'Shreya Study Center',
            'number' : '+42 515 635 0210',
            'location' : 'Jakarta, USA',
            'name' : 'Education',
            'icon' : 'bi bi-mortarboard',
            'span' : 'catIcon cats-5',
            'reviews' : '72 Reviews',
            'btn' : 'Closed',
            'color' : 'listClose',
            'dollar' : '$$$',
            'btn1' : 'Featured',
            'tag' : 'true',
        },
        {
            'id' : 6,
            'img' : '/static/assets/img/list-6.jpg',
            'img1' : '/static/assets/img/team-6.jpg',
            'title' : 'Mahroom Garage & Workshop',
            'number' : '+42 515 635 3251',
            'location' : 'Jakarta, USA',
            'name' : 'Showroom',
            'icon' : 'bi bi-backpack',
            'span' : 'catIcon cats-6',
            'reviews' : '42 Reviews',
            'btn' : 'Open',
            'color' : 'listOpen',
            'dollar' : '$$$$',
            'btn1' : '',
            'tag' : 'false',
        },
        {
            'id' : 7,
            'img' : '/static/assets/img/list-9.jpg',
            'img1' : '/static/assets/img/team-7.jpg',
            'title' : 'The Great Dream Palace',
            'number' : '+42 515 635 5426',
            'location' : 'Jakarta, USA',
            'name' : 'Eat & Drink',
            'icon' : 'bi bi-cup-hot',
            'span' : 'catIcon cats-7',
            'reviews' : '625 Reviews',
            'btn' : 'Closed',
            'color' : 'listClose',
            'dollar' : '$$$',
            'btn1' : '',
            'tag' : 'false',
        },
        {
            'id' : 8,
            'img' : '/static/assets/img/list-8.jpg',
            'img1' : '/static/assets/img/team-8.jpg',
            'title' : 'Agroo Spa & Massage Center',
            'number' : '+42 515 635 2136',
            'location' : 'Jakarta, USA',
            'name' : 'Spa & Beauty',
            'icon' : 'bi bi-basket2',
            'span' : 'catIcon cats-8',
            'reviews' : '102 Reviews',
            'btn' : 'Open',
            'color' : 'listOpen',
            'dollar' : '$$$$',
            'btn1' : 'Featured',
            'tag' : 'true',
        },
        {
            'id' : 9,
            'img' : '/static/assets/img/list-12.jpg',
            'img1' : '/static/assets/img/team-1.jpg',
            'title' : 'Creative Wedding Planner',
            'desc' : 'Cicero famously orated against his political.',
            'number' : '+42 515 635 4758',
            'location' : 'Jakarta, USA',
            'miles' : '2.4 miles',
            'name' : 'Wedding',
            'icon' : 'fa-solid fa-dumbbell',
            'span' : 'catIcon cats-1',
            'plus' : '+2',
            'rating' : '4.5',
            'avarage' : 'good',
            'reviews' : '46 Reviews',
            'btn' : 'Open',
            'color' : 'listOpen',
            'dollar' : '$$$',
            'btn1' : 'Featured',
            'tag' : 'true',
        }
    ]
    selected_listing2 = next((listing2 for listing2 in listings2 if slugify(listing2['title']) == title), None)

    if selected_listing2:
        return render_template('pages/single-listing-02.html', listing2=selected_listing2)
    else:
        return "listing2 not found", 404


@main.route("/single-listing-03/")
def listing_03_list_or_default():
    listings3 = [
        {
            'id' : 1,
            'img' : '/static/assets/img/single-3.jpg',
            'title' : 'Groom Barber Shop',
            'location' : 'Old Paris, France',
        }
    ]
    listing3 = listings3[0]
    return render_template("pages/single-listing-03.html", listing3=listing3)


@main.route("/single-listing-03/<string:title>/")
def single_listing_03(title):
    listings3 = [
        {
            'id' : 1,
            'img' : '/static/assets/img/list-1.jpg',
            'img1' : '/static/assets/img/team-1.jpg',
            'title' : 'The Big Bumbble Gym',
            'desc' : 'Cicero famously orated against his political.',
            'number' : '+42 515 635 4758',
            'location' : 'Jakarta, USA',
            'name' : 'Fitness',
            'icon' : 'fa-solid fa-dumbbell',
            'span' : 'catIcon cats-1',
            'plus' : '+2',
            'btn' : 'Open',
            'color' : 'listOpen',
            'dollar' : '$$$',
            'btn1' : 'Featured',
            'tag' : 'true',
        },
        {
            'id' : 2,
            'img' : '/static/assets/img/list-2.jpg',
            'img1' : '/static/assets/img/team-2.jpg',
            'title' : 'Greenvally Real Estate',
            'desc' : 'Cicero famously orated against his political.',
            'number' : '+42 515 635 6150',
            'location' : 'Niwak, USA',
            'name' : 'Real Estate',
            'icon' : 'bi bi-house-check',
            'span' : 'catIcon cats-2',
            'plus' : '+2',
            'btn' : 'Open',
            'color' : 'listOpen',
            'dollar' : '$$$$',
            'btn1' : '',
            'tag' : 'false',
        },
        {
            'id' : 3,
            'img' : '/static/assets/img/list-3.jpg',
            'img1' : '/static/assets/img/team-3.jpg',
            'title' : 'Shree Wedding Planner',
            'desc' : 'Cicero famously orated against his political.',
            'number' : '+42 515 635 4785',
            'location' : 'Jakarta, USA',
            'name' : 'Weddings',
            'icon' : 'bi bi-lamp',
            'span' : 'catIcon cats-3',
            'plus' : '+1',
            'btn' : 'Closed',
            'color' : 'listClose',
            'dollar' : '$$$',
            'btn1' : 'Featured',
            'tag' : 'true',
        },
        {
            'id' : 4,
            'img' : '/static/assets/img/list-4.jpg',
            'img1' : '/static/assets/img/team-4.jpg',
            'title' : 'The Blue Ley Light',
            'desc' : 'Cicero famously orated against his political.',
            'number' : '+42 515 635 6358',
            'location' : 'Chicago, USA',
            'name' : 'Restaurant',
            'icon' : 'bi bi-cup-straw',
            'span' : 'catIcon cats-4',
            'plus' : '+1',
            'btn' : 'Open',
            'color' : 'listOpen',
            'dollar' : '$$$$',
            'btn1' : '',
            'tag' : 'false',
        },
        {
            'id' : 5,
            'img' : '/static/assets/img/list-5.jpg',
            'img1' : '/static/assets/img/team-5.jpg',
            'title' : 'Shreya Study Center',
            'desc' : 'Cicero famously orated against his political.',
            'number' : '+42 515 635 0210',
            'location' : 'Jakarta, USA',
            'name' : 'Education',
            'icon' : 'bi bi-mortarboard',
            'span' : 'catIcon cats-5',
            'plus' : '+1',
            'btn' : 'Closed',
            'color' : 'listClose',
            'dollar' : '$$$',
            'btn1' : 'Featured',
            'tag' : 'true',
        },
        {
            'id' : 6,
            'img' : '/static/assets/img/list-6.jpg',
            'img1' : '/static/assets/img/team-6.jpg',
            'title' : 'Mahroom Garage & Workshop',
            'desc' : 'Cicero famously orated against his political.',
            'number' : '+42 515 635 3251',
            'location' : 'New York, USA',
            'name' : 'Showroom',
            'icon' : 'bi bi-backpack',
            'span' : 'catIcon cats-6',
            'plus' : '+1',
            'btn' : 'Open',
            'color' : 'listOpen',
            'dollar' : '$$$$',
            'btn1' : '',
            'tag' : 'false',
        },
        {
            'id' : 7,
            'img' : '/static/assets/img/list-9.jpg',
            'img1' : '/static/assets/img/team-7.jpg',
            'title' : 'The Great Dream Palace',
            'number' : '+42 515 635 5426',
            'location' : 'Jakarta, USA',
            'name' : 'Eat & Drink',
            'icon' : 'bi bi-cup-hot',
            'span' : 'catIcon cats-7',
            'btn' : 'Closed',
            'color' : 'listClose',
            'dollar' : '$$$',
            'btn1' : '',
            'tag' : 'false',
        },
        {
            'id' : 8,
            'img' : '/static/assets/img/list-8.jpg',
            'img1' : '/static/assets/img/team-8.jpg',
            'title' : 'Agroo Spa & Massage Center',
            'number' : '+42 515 635 2136',
            'location' : 'New York, USA',
            'name' : 'Spa & Beauty',
            'icon' : 'bi bi-basket2',
            'span' : 'catIcon cats-8',
            'btn' : 'Open',
            'color' : 'listOpen',
            'dollar' : '$$$$',
            'btn1' : 'Featured',
            'tag' : 'true',
        },
        {
            'id' : 9,
            'img' : '/static/assets/img/list-12.jpg',
            'img1' : '/static/assets/img/team-1.jpg',
            'title' : 'Creative Wedding Planner',
            'number' : '+42 515 635 4758',
            'location' : 'Jakarta, USA',
            'name' : 'Wedding',
            'icon' : 'fa-solid fa-dumbbell',
            'span' : 'catIcon cats-1',
            'btn' : 'Open',
            'color' : 'listOpen',
            'dollar' : '$$$',
            'btn1' : 'Featured',
            'tag' : 'true',
        },
        {
            'id' : 10,
            'img' : '/static/assets/img/list-11.jpg',
            'img1' : '/static/assets/img/team-1.jpg',
            'title' : 'Cruzal Escort Services',
            'desc' : 'Cicero famously orated against his political.',
            'number' : '+42 515 635 0210',
            'location' : 'Jakarta, USA',
            'name' : 'Services',
            'icon' : 'fa-solid fa-dumbbell',
            'span' : 'catIcon cats-1',
            'plus' : '+2',
            'btn' : 'Open',
            'color' : 'listOpen',
            'dollar' : '$$$',
            'btn1' : 'Featured',
            'tag' : 'true',
        }
    ]
    selected_listing3 = next((listing3 for listing3 in listings3 if slugify(listing3['title']) == title), None)

    if selected_listing3:
        return render_template('pages/single-listing-03.html', listing3=selected_listing3)
    else:
        return "listing3 not found", 404


@main.route("/single-listing-04/")
def listing_04_list_or_default():
    events = [
        {
            'id': 1,
            'img': '/static/assets/img/single-4.jpg',
            'title': 'Christmas Monday',
            'time': '10:30AM To 14:30PM',
        }
    ]
    event = events[0]
    return render_template("pages/single-listing-04.html", event=event)


@main.route("/single-listing-04/<string:title>/")
def single_listing_04(title):
    events = [
        {
            'id': 1,
            'img': '/static/assets/img/eve-1.jpg',
            'title': 'Learn Cooc with Shree Patel',
            'time': '10:30 AM To 02:40 PM',
            'name': 'Cooking',
            'color': 'badge badge-xs badge-danger',
            'date': '25',
            'month': 'Aug',
        },
        {
            'id': 2,
            'img': '/static/assets/img/eve-2.jpg',
            'title': 'Enjoy with Adobe Ceremoney',
            'time': '08:00 AM To 10:30 PM',
            'name': 'Nightlife',
            'color': 'badge badge-xs badge-success',
            'date': '15',
            'month': 'Sep',
        },
        {
            'id': 3,
            'img': '/static/assets/img/eve-3.jpg',
            'title': 'Join AI Community Workshop',
            'time': '8:30 AM To 12:20 PM',
            'name': 'Workshop',
            'color': 'badge badge-xs badge-warning',
            'date': '10',
            'month': 'Nov',
        }
    ]
    selected_event = next((event for event in events if slugify(event['title']) == title), None)

    if selected_event:
        return render_template('pages/single-listing-04.html', event=selected_event)
    else:
        return "event not found", 404


@main.route("/single-listing-05/")
def listing_05_list_or_default():
    listings5 = [
        {
            'id' : 1,
            'title' : 'TATA Nexon XM White',
        }
    ]
    listing5 = listings5[0]
    return render_template("pages/single-listing-05.html", listing5=listing5)


@main.route("/single-listing-05/<string:title>/")
def single_listing_05(title):
    listings5 = [
        {
            'id' : 1,
            'img' : '/static/assets/img/list-1.jpg',
            'img1' : '/static/assets/img/team-1.jpg',
            'title' : 'The Big Bumbble Gym',
            'number' : '+42 515 635 4758',
            'location' : 'Jakarta, USA',
            'name' : 'Health & Fitness',
            'icon' : 'fa-solid fa-dumbbell',
            'span' : 'catIcon cats-1',
            'reviews' : '42 Reviews',
            'btn' : 'Open',
            'color' : 'listOpen',
            'dollar' : '$$$',
            'btn1' : 'Featured',
            'tag' : 'true',
        },
        {
            'id' : 2,
            'img' : '/static/assets/img/list-2.jpg',
            'img1' : '/static/assets/img/team-2.jpg',
            'title' : 'Greenvally Real Estate',
            'number' : '+42 515 635 6150',
            'location' : 'Jakarta, USA',
            'name' : 'Real Estate',
            'icon' : 'bi bi-house-check',
            'span' : 'catIcon cats-2',
            'reviews' : '39 Reviews',
            'btn' : 'Closed',
            'color' : 'listClose',
            'dollar' : '$$$$',
            'btn1' : '',
            'tag' : 'false',
        },
        {
            'id' : 3,
            'img' : '/static/assets/img/list-3.jpg',
            'img1' : '/static/assets/img/team-3.jpg',
            'title' : 'Shree Wedding Planner',
            'number' : '+42 515 635 4785',
            'location' : 'Jakarta, USA',
            'name' : 'Wedding & Evemts',
            'icon' : 'bi bi-lamp',
            'span' : 'catIcon cats-3',
            'reviews' : '65 Reviews',
            'btn' : 'Open',
            'color' : 'listOpen',
            'dollar' : '$$$',
            'btn1' : 'Featured',
            'tag' : 'true',
        },
        {
            'id' : 4,
            'img' : '/static/assets/img/list-4.jpg',
            'img1' : '/static/assets/img/team-4.jpg',
            'title' : 'The Blue Ley Light',
            'number' : '+42 515 635 6358',
            'location' : 'Jakarta, USA',
            'name' : 'Restaurant',
            'icon' : 'bi bi-cup-straw',
            'span' : 'catIcon cats-4',
            'reviews' : '152 Reviews',
            'btn' : 'Open',
            'color' : 'listOpen',
            'dollar' : '$$$$',
            'btn1' : '',
            'tag' : 'false',
        },
        {
            'id' : 5,
            'img' : '/static/assets/img/list-5.jpg',
            'img1' : '/static/assets/img/team-5.jpg',
            'title' : 'Shreya Study Center',
            'number' : '+42 515 635 0210',
            'location' : 'Jakarta, USA',
            'name' : 'Education',
            'icon' : 'bi bi-mortarboard',
            'span' : 'catIcon cats-5',
            'reviews' : '72 Reviews',
            'btn' : 'Closed',
            'color' : 'listClose',
            'dollar' : '$$$',
            'btn1' : 'Featured',
            'tag' : 'true',
        },
        {
            'id' : 6,
            'img' : '/static/assets/img/list-6.jpg',
            'img1' : '/static/assets/img/team-6.jpg',
            'title' : 'Mahroom Garage & Workshop',
            'number' : '+42 515 635 3251',
            'location' : 'Jakarta, USA',
            'name' : 'Showroom',
            'icon' : 'bi bi-backpack',
            'span' : 'catIcon cats-6',
            'reviews' : '42 Reviews',
            'btn' : 'Open',
            'color' : 'listOpen',
            'dollar' : '$$$$',
            'btn1' : '',
            'tag' : 'false',
        },
        {
            'id' : 7,
            'img' : '/static/assets/img/list-9.jpg',
            'img1' : '/static/assets/img/team-7.jpg',
            'title' : 'The Great Dream Palace',
            'number' : '+42 515 635 5426',
            'location' : 'Jakarta, USA',
            'name' : 'Eat & Drink',
            'icon' : 'bi bi-cup-hot',
            'span' : 'catIcon cats-7',
            'reviews' : '625 Reviews',
            'btn' : 'Closed',
            'color' : 'listClose',
            'dollar' : '$$$',
            'btn1' : '',
            'tag' : 'false',
        },
        {
            'id' : 8,
            'img' : '/static/assets/img/list-8.jpg',
            'img1' : '/static/assets/img/team-8.jpg',
            'title' : 'Agroo Spa & Massage Center',
            'number' : '+42 515 635 2136',
            'location' : 'Jakarta, USA',
            'name' : 'Spa & Beauty',
            'icon' : 'bi bi-basket2',
            'span' : 'catIcon cats-8',
            'reviews' : '102 Reviews',
            'btn' : 'Open',
            'color' : 'listOpen',
            'dollar' : '$$$$',
            'btn1' : 'Featured',
            'tag' : 'true',
        }
    ]
    selected_listing5 = next((listing5 for listing5 in listings5 if slugify(listing5['title']) == title), None)

    if selected_listing5:
        return render_template('pages/single-listing-05.html', listing5=selected_listing5)
    else:
        return "listing5 not found", 404


@main.route("/dashboard-user/")
def dashboard_user():
    if getattr(current_user, "is_authenticated", False):
        role = (getattr(current_user, "role", "") or "").strip().lower()
        if role == "provider":
            return redirect(url_for("main.dashboard_provider"))
        if role == "sales":
            return redirect(url_for("dashboard.sales_dashboard"))
        if role == "admin":
            return redirect(url_for("dashboard.admin_dashboard"))
    # pages/dashboard-user.html does not exist yet, so we keep legacy compatibility
    # by rendering the old dashboard shell with a safe shared context.
    context = get_dashboard_context()
    return render_template("pages/dashboard-user-old.html", **context)


PROVIDER_ALLOWED_ROLES = {"provider", "admin"}
PROVIDER_BUSINESS_FIELDS = {
    "listing_name": "listing_name",
    "name": "name",
    "main_category": "main_category",
    "subcategory": "subcategory",
    "short_description": "short_description",
    "long_description": "long_description",
    "address": "address",
    "country": "country",
    "province": "province",
    "city": "city",
    "canton": "canton",
    "zone": "zone",
    "neighborhood": "neighborhood",
    "google_maps_url": "google_maps_url",
    "phone": "phone_primary",
    "email": "email",
    "website_url": "website_url",
    "whatsapp_url": "whatsapp",
    "instagram_url": "instagram_url",
    "facebook_url": "facebook_url",
    "price_level": "price_level",
    "search_keywords": "search_keywords",
    "tags": "tags_csv",
    "opening_hours": "opening_hours",
    "business_hours": "business_hours",
    "hours": "hours",
}
PROVIDER_MEDIA_FIELDS = {
    "cover_image_url": "cover_image_url",
    "logo_image_url": "logo_image_url",
    "gallery_urls": "gallery_urls",
}


def _provider_slug_seed(profile, listing_name):
    safe_name = (listing_name or "new-business").strip()
    safe_email = ((getattr(profile, "email", None) or "").split("@")[0] or "provider").strip()
    return f"{safe_name}-{safe_email}"


def _build_provider_slug(profile, listing_name):
    base = slugify(_provider_slug_seed(profile, listing_name))[:150] or "new-business"
    candidate = base
    attempts = 0
    while Listing.query.filter_by(slug=candidate).first():
        attempts += 1
        candidate = f"{base}-{uuid4().hex[:8]}"[:180]
        if attempts > 8:
            break
    return candidate


def _require_provider_account():
    if not getattr(current_user, "is_authenticated", False):
        return None, redirect(url_for("auth.login"))

    role = (getattr(current_user, "role", "") or "").strip().lower()
    if role not in PROVIDER_ALLOWED_ROLES:
        flash("Provider access is only available for provider accounts.", "error")
        return None, redirect(url_for("main.dashboard_user"))

    return current_user, None


def _resolve_provider_listing(profile):
    if not profile:
        return None

    profile_email = _normalize_email(getattr(profile, "email", None))
    if not profile_email:
        return None

    try:
        return (
            Listing.query.filter(
                or_(
                    func.lower(Listing.provider_email) == profile_email,
                    func.lower(Listing.email) == profile_email,
                )
            )
            .order_by(Listing.created_at.asc())
            .first()
        )
    except Exception:
        db.session.rollback()
        return None


def _provider_listing_metrics(listing):
    if not listing:
        return {
            "status_label": "Pending Setup",
            "status_raw": "draft",
            "category_label": "-",
            "subcategory_label": "-",
            "business_name": "New Business",
            "city_label": "-",
            "views_count": 0,
            "reviews_count": 0,
            "saved_count": 0,
        }

    category_parts = [listing.main_category, listing.subcategory]
    reviews_count = int(getattr(listing, "reviews_count", 0) or getattr(listing, "review_count", 0) or 0)

    return {
        "status_label": (listing.status or ("active" if listing.is_active else "draft")).replace("_", " ").title(),
        "status_raw": (listing.status or ("active" if listing.is_active else "draft")).lower(),
        "category_label": " / ".join(part for part in category_parts if part) or "-",
        "subcategory_label": listing.subcategory or "-",
        "business_name": listing.listing_name or listing.name or "New Business",
        "city_label": listing.city or "-",
        "views_count": int(getattr(listing, "view_count", 0) or 0),
        "reviews_count": reviews_count,
        "saved_count": int(getattr(listing, "favorite_count", 0) or 0),
    }


def _provider_public_listing_url(listing):
    if not listing or not getattr(listing, "slug", None):
        return None
    return url_for("main.public_listing", slug=listing.slug)


def _listing_column_names():
    try:
        return {column.name for column in Listing.__table__.columns}
    except Exception:
        return set()


def _provider_field_flags():
    columns = _listing_column_names()
    return {
        "whatsapp": "whatsapp" in columns,
        "instagram_url": "instagram_url" in columns,
        "facebook_url": "facebook_url" in columns,
        "tags_csv": "tags_csv" in columns,
        "search_keywords": "search_keywords" in columns,
        "gallery_urls": "gallery_urls" in columns,
        "opening_hours": any(name in columns for name in {"opening_hours", "business_hours", "hours"}),
    }


def _provider_dashboard_context(profile, listing):
    first_name = (getattr(profile, "first_name", None) or "Provider").strip() or "Provider"
    last_name = (getattr(profile, "last_name", None) or "").strip()
    full_name = f"{first_name} {last_name}".strip() or first_name
    avatar_url = getattr(profile, "avatar_url", None) or url_for("static", filename="assets/img/user.jpg")

    context = {
        "profile": profile,
        "dashboard_user": {
            "id": str(profile.id),
            "first_name": first_name,
            "last_name": last_name,
            "full_name": full_name,
            "email": getattr(profile, "email", None) or "",
            "role": getattr(profile, "role", None) or "provider",
            "avatar_url": avatar_url,
        },
        "user_name": full_name,
        "user_email": getattr(profile, "email", None) or "",
        "user_avatar_url": avatar_url,
        "messages2": [],
        "saveds": [],
    }
    context.update(
        {
            "provider_listing": listing,
            **_provider_listing_metrics(listing),
            "provider_ready_message": "Your provider account is ready. Complete your business information.",
            "provider_public_listing_url": _provider_public_listing_url(listing),
            "provider_fields": _provider_field_flags(),
        }
    )
    return context


def _coerce_coordinate(raw_value):
    cleaned = (raw_value or "").strip()
    if not cleaned:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def _ensure_provider_listing(profile):
    listing = _resolve_provider_listing(profile)
    if listing:
        return listing

    listing_name = "New Business"
    listing = Listing(
        name=listing_name,
        listing_name=listing_name,
        slug=_build_provider_slug(profile, listing_name),
        provider_name=getattr(profile, "full_name", None) or listing_name,
        provider_email=getattr(profile, "email", None),
        email=getattr(profile, "email", None),
        is_active=False,
        status="draft",
    )
    db.session.add(listing)
    return listing


@main.route("/dashboard/provider")
def dashboard_provider():
    profile, redirect_response = _require_provider_account()
    if redirect_response:
        return redirect_response

    listing = _resolve_provider_listing(profile)
    context = _provider_dashboard_context(profile, listing)
    return render_template("pages/dashboard-provider.html", **context)


@main.route("/dashboard/provider/business", methods=["GET", "POST"])
def dashboard_provider_business():
    profile, redirect_response = _require_provider_account()
    if redirect_response:
        return redirect_response

    listing = _resolve_provider_listing(profile)

    if request.method == "POST":
        try:
            listing = listing or _ensure_provider_listing(profile)
            for form_name, attr_name in PROVIDER_BUSINESS_FIELDS.items():
                if not hasattr(listing, attr_name):
                    continue
                value = (request.form.get(form_name) or "").strip()
                if not value:
                    continue
                if attr_name == "email":
                    value = value.lower()
                setattr(listing, attr_name, value)

            if hasattr(listing, "latitude"):
                latitude = _coerce_coordinate(request.form.get("latitude"))
                if latitude is not None:
                    listing.latitude = latitude
            if hasattr(listing, "longitude"):
                longitude = _coerce_coordinate(request.form.get("longitude"))
                if longitude is not None:
                    listing.longitude = longitude

            if hasattr(listing, "name") and not (listing.name or "").strip():
                fallback_name = (listing.listing_name or "New Business").strip()
                listing.name = fallback_name
            if hasattr(listing, "listing_name") and not (listing.listing_name or "").strip():
                listing.listing_name = listing.name
            if hasattr(listing, "slug") and not (listing.slug or "").strip():
                listing.slug = _build_provider_slug(profile, listing.listing_name or listing.name)

            db.session.commit()
            flash("Business information updated successfully.", "success")
        except Exception:
            db.session.rollback()
            flash("Could not update business information right now.", "error")

        return redirect(url_for("main.dashboard_provider_business"))

    context = _provider_dashboard_context(profile, listing)
    return render_template("pages/dashboard-provider-business.html", **context)


@main.route("/dashboard/provider/media", methods=["GET", "POST"])
def dashboard_provider_media():
    profile, redirect_response = _require_provider_account()
    if redirect_response:
        return redirect_response

    listing = _resolve_provider_listing(profile)

    if request.method == "POST":
        try:
            listing = listing or _ensure_provider_listing(profile)
            for form_name, attr_name in PROVIDER_MEDIA_FIELDS.items():
                if not hasattr(listing, attr_name):
                    continue
                value = (request.form.get(form_name) or "").strip()
                if not value:
                    continue
                setattr(listing, attr_name, value)

            db.session.commit()
            flash("Business media updated successfully.", "success")
        except Exception:
            db.session.rollback()
            flash("Could not update business media right now.", "error")

        return redirect(url_for("main.dashboard_provider_media"))

    context = _provider_dashboard_context(profile, listing)
    return render_template("pages/dashboard-provider-media.html", **context)


@main.route("/listing/<string:slug>/")
def public_listing(slug):
    listing = Listing.query.filter_by(slug=slug).first_or_404()
    return render_template("pages/public-listing.html", listing=listing)


@main.route("/dashboard-my-profile/", methods=["GET", "POST"])
def dashboard_my_profile():
    if request.method == "POST":
        if not getattr(current_user, "is_authenticated", False):
            flash("Please log in to update your profile.", "error")
            return redirect(url_for("auth.login"))

        form_type = (request.form.get("form_type") or "").strip().lower()
        user = current_user

        if form_type == "profile":
            first_name = (request.form.get("first_name") or "").strip()
            last_name = (request.form.get("last_name") or "").strip()
            email = (request.form.get("email") or "").strip().lower()
            phone = (request.form.get("phone") or "").strip()

            if not first_name or not last_name:
                flash("First name and last name are required.", "error")
                return redirect(url_for("main.dashboard_my_profile"))

            if not email:
                flash("Email is required.", "error")
                return redirect(url_for("main.dashboard_my_profile"))

            email_owner = UserProfile.query.filter_by(email=email).first()
            if email_owner and email_owner.id != user.id:
                flash("That email is already in use.", "error")
                return redirect(url_for("main.dashboard_my_profile"))

            user.first_name = first_name
            user.last_name = last_name
            user.email = email
            user.phone = phone or None

            db.session.commit()
            flash("Profile updated successfully.", "success")
            return redirect(url_for("main.dashboard_my_profile"))

        if form_type == "avatar":
            avatar_url = (request.form.get("avatar_url") or "").strip()
            if avatar_url:
                user.avatar_url = avatar_url
                db.session.commit()
                flash("Profile image updated successfully.", "success")
            elif request.files.get("myfile"):
                avatar_file = request.files.get("myfile")
                original_filename = avatar_file.filename or ""
                extension = _avatar_extension(original_filename)

                if not original_filename.strip():
                    flash("Please select an image file.", "error")
                    return redirect(url_for("main.dashboard_my_profile"))

                if extension not in ALLOWED_AVATAR_EXTENSIONS:
                    flash("Invalid image format. Allowed: jpg, jpeg, png, webp.", "error")
                    return redirect(url_for("main.dashboard_my_profile"))

                try:
                    uploads_root = Path(current_app.static_folder) / "uploads" / "avatars"
                    uploads_root.mkdir(parents=True, exist_ok=True)

                    safe_stem = secure_filename(Path(original_filename).stem) or "avatar"
                    filename = f"{safe_stem}-{uuid4().hex}.{extension}"
                    destination = uploads_root / filename
                    avatar_file.save(destination)

                    user.avatar_url = f"/static/uploads/avatars/{filename}"
                    db.session.commit()
                    flash("Profile image updated successfully.", "success")
                except Exception:
                    db.session.rollback()
                    flash("Could not upload profile image. Please try again.", "error")
            else:
                flash("No new profile image provided.", "error")
            return redirect(url_for("main.dashboard_my_profile"))

        if form_type == "password":
            old_password = request.form.get("old_password") or ""
            new_password = request.form.get("new_password") or ""
            confirm_password = request.form.get("confirm_password") or ""

            if not old_password or not new_password or not confirm_password:
                flash("All password fields are required.", "error")
                return redirect(url_for("main.dashboard_my_profile"))

            if not user.check_password(old_password):
                flash("Current password is incorrect.", "error")
                return redirect(url_for("main.dashboard_my_profile"))

            if len(new_password) < 6:
                flash("New password must be at least 6 characters.", "error")
                return redirect(url_for("main.dashboard_my_profile"))

            if new_password != confirm_password:
                flash("New password and confirmation do not match.", "error")
                return redirect(url_for("main.dashboard_my_profile"))

            user.set_password(new_password)
            db.session.commit()
            flash("Password updated successfully.", "success")
            return redirect(url_for("main.dashboard_my_profile"))

        flash("Unsupported profile action.", "error")
        return redirect(url_for("main.dashboard_my_profile"))

    context = get_dashboard_context()
    return render_template("pages/dashboard-my-profile.html", **context)


@main.route("/dashboard-my-bookings/")
def dashboard_my_bookings():
    context = get_dashboard_context()
    return render_template("pages/dashboard-my-bookings.html", **context)


@main.route("/dashboard-my-listings/")
def dashboard_my_listings():
    context = get_dashboard_context()
    return render_template("pages/dashboard-my-listings.html", **context)


@main.route("/dashboard-bookmarks/")
def dashboard_bookmarks():
    context = get_dashboard_context()
    return render_template("pages/dashboard-bookmarks.html", **context)


@main.route("/dashboard-messages/")
def dashboard_messages():
    context = get_dashboard_context()
    return render_template("pages/dashboard-messages.html", **context)


@main.route("/dashboard-reviews/")
def dashboard_reviews():
    context = get_dashboard_context()
    return render_template("pages/dashboard-reviews.html", **context)


@main.route("/dashboard-wallet/")
def dashboard_wallet():
    context = get_dashboard_context()
    return render_template("pages/dashboard-wallet.html", **context)


@main.route("/dashboard-add-listing/")
def dashboard_add_listing():
    context = get_dashboard_context()
    return render_template("pages/dashboard-add-listing.html", **context)


@main.route("/login/")
def login():
    return render_template("pages/login.html")


@main.route("/register/")
def register():
    return render_template("pages/register.html")


@main.route("/forgot-password/")
def forgot_password():
    return render_template("pages/forgot-password.html")


@main.route("/two-factor-auth/")
def two_factor_auth():
    return render_template("pages/two-factor-auth.html")


@main.route("/author-profile/")
def author_profile():
    return render_template("pages/author-profile.html")


@main.route("/booking-page/")
def booking_page():
    return render_template("pages/booking-page.html")


@main.route("/about-us/")
def about_us():
    return render_template("pages/about-us.html")


@main.route("/blog/")
def blog():
    return render_template("pages/blog.html")


@main.route("/blog-detail/")
def blog_list_or_default():
    blogs = [
        {
            'id' : 1,
            'img' : '/static/assets/img/gal-4.jpg',
            'title' : 'Top 10 Free Bootstrap Templates for Your Next Project',
            'date' : "6 Sep 2025",
        }
    ]
    blog = blogs[0]
    return render_template("pages/blog-detail.html", blog=blog)


@main.route("/blog-detail/<string:title>/")
def blog_detail(title):
    blogs = [
        {
            'id' : 1,
            'img' : '/static/assets/img/blog-2.jpg',
            'title' : '10 Must-Have Bootstrap Templates for Modern Web Design',
            'desc' : "Think of a news blog that's filled with content political against opponent Lucius Sergius.",
            'date' : "12 Feb 2025",
            'views' : "12k Views",
        },
        {
            'id' : 2,
            'img' : '/static/assets/img/blog-1.jpg',
            'title' : 'Top 5 Bootstrap Themes for E-commerce Websites.',
            'desc' : "Think of a news blog that's filled with content political against opponent Lucius Sergius.",
            'date' : "10 Jan 2025",
            'views' : "33k Views",
        },
        {
            'id' : 3,
            'img' : '/static/assets/img/blog-3.jpg',
            'title' : 'The Ultimate Guide to Customizing Bootstrap Templates',
            'desc' : "Think of a news blog that's filled with content political against opponent Lucius Sergius.",
            'date' : "07 March 2025",
            'views' : "15k Views",
        },
        {
            'id' : 4,
            'img' : '/static/assets/img/blog-4.jpg', 
            'title' : 'Top 10 Free Bootstrap Templates for Your Next Project',
            'desc' : "Think of a news blog that's filled with content political against opponent Lucius Sergius Catilina. Hourly on the day of going live.",
            'date' : '12 Feb 2025',
            'views' : '12k Views',
        },
        {
            'id' : 5,
            'img' : '/static/assets/img/blog-5.jpg', 
            'title' : 'Creating Stunning Landing Pages with Bootstrap: Best Practices',
            'desc' : "Think of a news blog that's filled with content political against opponent Lucius Sergius Catilina. Hourly on the day of going live.",
            'date' : '17 Jan 2025',
            'views' : '33k Views',
        },
        {
            'id' : 6,
            'img' : '/static/assets/img/blog-6.jpg', 
            'title' : 'The Benefits of Using Bootstrap for Your Web Development Projects',
            'desc' : "Think of a news blog that's filled with content political against opponent Lucius Sergius Catilina. Hourly on the day of going live.",
            'date' : '07 March 2025',
            'views' : '15k Views',
        }
    ]
    selected_blog = next((blog for blog in blogs if slugify(blog['title']) == title), None)

    if selected_blog:
        return render_template('pages/blog-detail.html', blog=selected_blog)
    else:
        return "blog not found", 404


@main.route("/contact-us/")
def contact_us():
    return render_template("pages/contact-us.html")


@main.route("/pricing/")
def pricing():
    return render_template("pages/pricing.html")


@main.route("/help-center/")
def help_center():
    return render_template("pages/help-center.html")


@main.route("/comingsoon/")
def comingsoon():
    return render_template("pages/comingsoon.html")


@main.route("/faq/")
def faq():
    return render_template("pages/faq.html")


@main.route("/error/")
def error():
    return render_template("pages/error.html")


@main.route("/elements/")
def elements():
    return render_template("pages/elements.html")


@main.route("/checkout-page/")
def checkout_page():
    return render_template("pages/checkout-page.html")


@main.route("/invoice-page/")
def invoice_page():
    return render_template("pages/invoice-page.html")


@main.route("/privacy-policy/")
def privacy_policy():
    return render_template("pages/privacy-policy.html")


@main.route("/single-helps/")
def single_helps():
    return render_template("pages/single-helps.html")


@main.route("/success-payment/")
def success_payment():
    return render_template("pages/success-payment.html")


@main.route("/viewcart/")
def viewcart():
    return render_template("pages/viewcart.html")


from app.services.dashboard_service import DashboardService

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/dashboard/user")
def user_dashboard():
    if getattr(current_user, "is_authenticated", False):
        role = (getattr(current_user, "role", "") or "").strip().lower()
        if role == "provider":
            return redirect(url_for("main.dashboard_provider"))
        if role == "sales":
            return redirect(url_for("dashboard.sales_dashboard"))
        if role == "admin":
            return redirect(url_for("dashboard.admin_dashboard"))
    profile = DashboardService.resolve_profile()
    context = DashboardService.build_user_dashboard(profile)
    return render_template("Components/User-Dashboard/user/dashboard-user.html", **context)

@dashboard_bp.route("/dashboard/provider-legacy")
def provider_dashboard():
    return redirect(url_for("main.dashboard_provider"))

@dashboard_bp.route("/dashboard/sales")
def sales_dashboard():
    return render_template("Components/User-Dashboard/sales/dashboard-sales.html")

@dashboard_bp.route("/dashboard/admin")
def admin_dashboard():
    return render_template("Components/User-Dashboard/admin/dashboard-admin.html")







