from datetime import datetime
import uuid

from sqlalchemy.dialects.postgresql import UUID

from app.extensions import db


class Listing(db.Model):
    __tablename__ = "listings"

    # Primary identity
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(160), nullable=False, index=True)
    listing_name = db.Column(db.String(160), nullable=True, index=True)
    legal_name = db.Column(db.String(200), nullable=True)
    slug = db.Column(db.String(180), unique=True, nullable=False, index=True)

    # Descriptions and taxonomy
    description = db.Column(db.Text, nullable=True)
    short_description = db.Column(db.String(320), nullable=True)
    long_description = db.Column(db.Text, nullable=True)
    main_category = db.Column(db.String(80), nullable=True, index=True)
    subcategory = db.Column(db.String(120), nullable=True, index=True)
    language_code = db.Column(db.String(10), nullable=True, index=True)
    search_keywords = db.Column(db.Text, nullable=True)
    tags_csv = db.Column(db.Text, nullable=True)
    amenities_csv = db.Column(db.Text, nullable=True)
    environment = db.Column(db.String(120), nullable=True)
    occasion = db.Column(db.String(120), nullable=True)

    # Location
    country = db.Column(db.String(80), nullable=True, index=True)
    province = db.Column(db.String(80), nullable=True, index=True)
    city = db.Column(db.String(80), nullable=True, index=True)
    canton = db.Column(db.String(80), nullable=True, index=True)
    zone = db.Column(db.String(80), nullable=True, index=True)
    neighborhood = db.Column(db.String(120), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    reference_note = db.Column(db.String(255), nullable=True)
    postal_code = db.Column(db.String(20), nullable=True)
    latitude = db.Column(db.Numeric(10, 7), nullable=True)
    longitude = db.Column(db.Numeric(10, 7), nullable=True)
    google_maps_url = db.Column(db.Text, nullable=True)
    what3words = db.Column(db.String(128), nullable=True)

    # Contact and links
    phone_primary = db.Column(db.String(40), nullable=True)
    phone_secondary = db.Column(db.String(40), nullable=True)
    whatsapp = db.Column(db.String(40), nullable=True)
    email = db.Column(db.String(255), nullable=True)
    website = db.Column(db.Text, nullable=True)
    website_url = db.Column(db.Text, nullable=True)
    booking_url = db.Column(db.Text, nullable=True)
    instagram_url = db.Column(db.Text, nullable=True)
    facebook_url = db.Column(db.Text, nullable=True)
    tiktok_url = db.Column(db.Text, nullable=True)
    youtube_url = db.Column(db.Text, nullable=True)

    # Media
    cover_image_url = db.Column(db.Text, nullable=True)
    logo_image_url = db.Column(db.Text, nullable=True)
    gallery_urls = db.Column(db.Text, nullable=True)
    video_url = db.Column(db.Text, nullable=True)

    # Pricing and listing flags
    price_level = db.Column(db.String(4), nullable=True) 
    price_min_usd = db.Column(db.Numeric(10, 2), nullable=True)
    price_max_usd = db.Column(db.Numeric(10, 2), nullable=True)
    currency_code = db.Column(db.String(10), nullable=True)
    is_free = db.Column(db.Boolean, nullable=False, default=False)
    is_featured = db.Column(db.Boolean, nullable=False, default=False)
    is_home_featured = db.Column(db.Boolean, nullable=False, default=False)
    home_feature_rank = db.Column(db.Integer, nullable=False, default=0)
    is_active = db.Column(db.Boolean, nullable=False, default=True, index=True)
    reservation_required = db.Column(db.Boolean, nullable=False, default=False)
    advance_booking_days = db.Column(db.Integer, nullable=True)
    minimum_age = db.Column(db.Integer, nullable=True)
    maximum_group_size = db.Column(db.Integer, nullable=True)
    duration_label = db.Column(db.String(80), nullable=True)

    # Amenities and experience booleans
    parking_available = db.Column(db.Boolean, nullable=False, default=False)
    wifi_available = db.Column(db.Boolean, nullable=False, default=False)
    pet_friendly = db.Column(db.Boolean, nullable=False, default=False)
    family_friendly = db.Column(db.Boolean, nullable=False, default=False)
    accessible = db.Column(db.Boolean, nullable=False, default=False)
    outdoor = db.Column(db.Boolean, nullable=False, default=False)
    indoor = db.Column(db.Boolean, nullable=False, default=False)
    airport_transfer = db.Column(db.Boolean, nullable=False, default=False)
    breakfast_included = db.Column(db.Boolean, nullable=False, default=False)
    delivery_available = db.Column(db.Boolean, nullable=False, default=False)
    takeout_available = db.Column(db.Boolean, nullable=False, default=False)
    live_music = db.Column(db.Boolean, nullable=False, default=False)

    # Ratings and engagement
    rating = db.Column(db.Numeric(3, 2), nullable=True)
    rating_avg = db.Column(db.Numeric(3, 2), nullable=False, default=0)
    reviews_count = db.Column(db.Integer, nullable=False, default=0)
    average_rating = db.Column(db.Numeric(3, 2), nullable=False, default=0)
    review_count = db.Column(db.Integer, nullable=False, default=0)
    view_count = db.Column(db.Integer, nullable=False, default=0)
    favorite_count = db.Column(db.Integer, nullable=False, default=0)
    status = db.Column(db.String(30), nullable=False, default="open", index=True)

    # Provider and import metadata
    provider_name = db.Column(db.String(160), nullable=True)
    provider_email = db.Column(db.String(255), nullable=True)
    owner_contact_name = db.Column(db.String(160), nullable=True)
    owner_contact_phone = db.Column(db.String(40), nullable=True)
    data_source = db.Column(db.String(80), nullable=True)
    source_reference = db.Column(db.String(160), nullable=True)
    import_notes = db.Column(db.Text, nullable=True)

    # Timestamps
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    bookmarks = db.relationship(
        "Bookmark",
        back_populates="listing",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    @property
    def open_badge_text(self):
        return "OPEN" if (self.status or "").lower() == "open" else (self.status or "").upper()
