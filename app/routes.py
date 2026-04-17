import re

from flask import Blueprint, jsonify, redirect, render_template, request, url_for
from slugify import slugify  # déjalo si ya lo usas en otras funciones
from app.models.listing import Listing
from app.models.newsletter_subscriber import NewsletterSubscriber
from app.extensions import db
from sqlalchemy import inspect, or_, text


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

@main.context_processor
def inject_slugify():
    return {'slugify': slugify}


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


@main.route("/grid-layout-01/")
def grid_layout_01():
    query_text = (request.args.get("q") or "").strip()
    location_text = (request.args.get("location") or "").strip()
    category = (request.args.get("category") or "").strip().lower()
    subcategory = (request.args.get("subcategory") or "").strip().lower()

    if category not in ALLOWED_MAIN_CATEGORIES:
        category = ""
    if subcategory not in ALLOWED_SUBCATEGORIES:
        subcategory = ""

    query = Listing.query.filter(Listing.is_active.is_(True))

    if query_text:
        query_like = f"%{query_text}%"
        query = query.filter(
            or_(
                Listing.listing_name.ilike(query_like),
                Listing.name.ilike(query_like),
                Listing.short_description.ilike(query_like),
                Listing.long_description.ilike(query_like),
                Listing.main_category.ilike(query_like),
                Listing.subcategory.ilike(query_like),
                Listing.search_keywords.ilike(query_like),
                Listing.tags_csv.ilike(query_like),
                Listing.environment.ilike(query_like),
                Listing.occasion.ilike(query_like),
            )
        )

    if location_text:
        location_like = f"%{location_text}%"
        query = query.filter(
            or_(
                Listing.country.ilike(location_like),
                Listing.province.ilike(location_like),
                Listing.city.ilike(location_like),
                Listing.canton.ilike(location_like),
                Listing.zone.ilike(location_like),
                Listing.neighborhood.ilike(location_like),
                Listing.address.ilike(location_like),
            )
        )

    if category:
        query = query.filter(Listing.main_category == category)
    if subcategory:
        query = query.filter(Listing.subcategory == subcategory)

    listings = query.order_by(
        Listing.is_home_featured.desc(),
        Listing.home_feature_rank.asc(),
        Listing.created_at.desc(),
    ).all()

    return render_template(
        "pages/grid-layout-01.html",
        listings=listings,
        search_query=query_text,
        search_location=location_text,
        selected_category=category,
        selected_subcategory=subcategory,
        allowed_main_categories=ALLOWED_MAIN_CATEGORIES,
    )


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
    return render_template("pages/dashboard-user.html")


@main.route("/dashboard-my-profile/")
def dashboard_my_profile():
    return render_template("pages/dashboard-my-profile.html")


@main.route("/dashboard-my-bookings/")
def dashboard_my_bookings():
    return render_template("pages/dashboard-my-bookings.html")


@main.route("/dashboard-my-listings/")
def dashboard_my_listings():
    return render_template("pages/dashboard-my-listings.html")


@main.route("/dashboard-bookmarks/")
def dashboard_bookmarks():
    return render_template("pages/dashboard-bookmarks.html")


@main.route("/dashboard-messages/")
def dashboard_messages():
    return render_template("pages/dashboard-messages.html")


@main.route("/dashboard-reviews/")
def dashboard_reviews():
    return render_template("pages/dashboard-reviews.html")


@main.route("/dashboard-wallet/")
def dashboard_wallet():
    return render_template("pages/dashboard-wallet.html")


@main.route("/dashboard-add-listing/")
def dashboard_add_listing():
    return render_template("pages/dashboard-add-listing.html")


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


from flask import Blueprint, render_template

from app.services.dashboard_service import DashboardService

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/dashboard/user")
def user_dashboard():
    profile = DashboardService.resolve_profile()
    context = DashboardService.build_user_dashboard(profile)
    return render_template("Components/User-Dashboard/user/dashboard-user.html", **context)

@dashboard_bp.route("/dashboard/provider")
def provider_dashboard():
    return render_template("Components/User-Dashboard/provider/dashboard-provider.html")

@dashboard_bp.route("/dashboard/sales")
def sales_dashboard():
    return render_template("Components/User-Dashboard/sales/dashboard-sales.html")

@dashboard_bp.route("/dashboard/admin")
def admin_dashboard():
    return render_template("Components/User-Dashboard/admin/dashboard-admin.html")



