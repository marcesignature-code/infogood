import os
import requests
from datetime import datetime, timezone

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")

if not GOOGLE_MAPS_API_KEY:
    raise RuntimeError("Falta GOOGLE_MAPS_API_KEY en .env")

if not DATABASE_URL:
    raise RuntimeError("Falta DATABASE_URL en .env")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

PLACES_TEXT_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"

SEARCH_QUERIES = [
    {"query": "restaurants in Quito Ecuador", "main_category": "food_drink", "subcategory": "restaurant"},
    {"query": "hotels in Quito Ecuador", "main_category": "accommodation", "subcategory": "hotel"},
]

FIELD_MASK = ",".join([
    "places.id",
    "places.displayName",
    "places.formattedAddress",
    "places.location",
    "places.types",
    "places.rating",
    "places.userRatingCount",
    "places.websiteUri",
    "places.nationalPhoneNumber",
    "places.businessStatus",
    "places.priceLevel",
])

def search_places(query: str):
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_MAPS_API_KEY,
        "X-Goog-FieldMask": FIELD_MASK,
    }

    payload = {
        "textQuery": query,
        "languageCode": "en",
        "maxResultCount": 20,
    }

    response = requests.post(
        PLACES_TEXT_SEARCH_URL,
        headers=headers,
        json=payload,
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    return data.get("places", [])

def get_display_name(place: dict):
    return (place.get("displayName") or {}).get("text")

def map_price_level(price_level: str | None):
    mapping = {
        "PRICE_LEVEL_FREE": "$",
        "PRICE_LEVEL_INEXPENSIVE": "$",
        "PRICE_LEVEL_MODERATE": "$$",
        "PRICE_LEVEL_EXPENSIVE": "$$$",
        "PRICE_LEVEL_VERY_EXPENSIVE": "$$$$",
    }
    return mapping.get(price_level)

def build_record(place: dict, main_category: str, subcategory: str):
    location = place.get("location") or {}
    types = place.get("types") or []

    latitude = location.get("latitude")
    longitude = location.get("longitude")

    listing_name = get_display_name(place)
    source_reference = place.get("id")
    price_level = map_price_level(place.get("priceLevel"))
    business_status = place.get("businessStatus")

    return {
        "listing_name": listing_name,
        "name": listing_name,  # por compatibilidad con registros antiguos
        "main_category": main_category,
        "subcategory": subcategory,
        "description": None,
        "short_description": None,
        "long_description": None,
        "province": "Pichincha",
        "city": "Quito",
        "country": "Ecuador",
        "address": place.get("formattedAddress"),
        "address_line": place.get("formattedAddress"),
        "latitude": latitude,
        "longitude": longitude,
        "website_url": place.get("websiteUri"),
        "phone_primary": place.get("nationalPhoneNumber"),
        "rating": place.get("rating"),
        "rating_avg": place.get("rating"),
        "reviews_count": place.get("userRatingCount"),
        "price_level": price_level,
        "status": "open" if business_status == "OPERATIONAL" else "closed",
        "is_active": True,
        "is_featured": False,
        "is_free": place.get("priceLevel") == "PRICE_LEVEL_FREE",
        "search_keywords": ",".join(types) if types else None,
        "tags_csv": ",".join(types) if types else None,
        "data_source": "google_places",
        "source_reference": source_reference,
        "import_notes": "Imported automatically from Google Places API",
        "updated_at": datetime.now(timezone.utc),
    }

def upsert_listing(conn, record: dict):
    sql = text("""
        INSERT INTO listings (
            name,
            listing_name,
            main_category,
            subcategory,
            description,
            short_description,
            long_description,
            province,
            city,
            country,
            address,
            address_line,
            latitude,
            longitude,
            website_url,
            phone_primary,
            rating,
            rating_avg,
            reviews_count,
            price_level,
            status,
            is_active,
            is_featured,
            is_free,
            search_keywords,
            tags_csv,
            data_source,
            source_reference,
            import_notes,
            updated_at
        )
        VALUES (
            :name,
            :listing_name,
            :main_category,
            :subcategory,
            :description,
            :short_description,
            :long_description,
            :province,
            :city,
            :country,
            :address,
            :address_line,
            :latitude,
            :longitude,
            :website_url,
            :phone_primary,
            :rating,
            :rating_avg,
            :reviews_count,
            :price_level,
            :status,
            :is_active,
            :is_featured,
            :is_free,
            :search_keywords,
            :tags_csv,
            :data_source,
            :source_reference,
            :import_notes,
            :updated_at
        )
        ON CONFLICT (data_source, source_reference)
        DO UPDATE SET
            name = EXCLUDED.name,
            listing_name = EXCLUDED.listing_name,
            main_category = EXCLUDED.main_category,
            subcategory = EXCLUDED.subcategory,
            address = EXCLUDED.address,
            address_line = EXCLUDED.address_line,
            city = EXCLUDED.city,
            province = EXCLUDED.province,
            country = EXCLUDED.country,
            latitude = EXCLUDED.latitude,
            longitude = EXCLUDED.longitude,
            website_url = EXCLUDED.website_url,
            phone_primary = EXCLUDED.phone_primary,
            rating = EXCLUDED.rating,
            rating_avg = EXCLUDED.rating_avg,
            reviews_count = EXCLUDED.reviews_count,
            price_level = EXCLUDED.price_level,
            search_keywords = EXCLUDED.search_keywords,
            tags_csv = EXCLUDED.tags_csv,
            status = EXCLUDED.status,
            is_active = EXCLUDED.is_active,
            is_free = EXCLUDED.is_free,
            import_notes = EXCLUDED.import_notes,
            updated_at = EXCLUDED.updated_at
    """)
    conn.execute(sql, record)

def main():
    total_found = 0
    total_saved = 0

    with engine.begin() as conn:
        for item in SEARCH_QUERIES:
            print(f"Buscando: {item['query']}")
            try:
                places = search_places(item["query"])
                print(f"Encontrados: {len(places)}")
            except Exception as e:
                print(f"Error buscando '{item['query']}': {e}")
                continue

            total_found += len(places)

            for place in places:
                record = build_record(
                    place,
                    item["main_category"],
                    item["subcategory"],
                )

                if not record["listing_name"] or not record["source_reference"]:
                    continue

                try:
                    upsert_listing(conn, record)
                    total_saved += 1
                    print(f"Guardado: {record['listing_name']}")
                except Exception as e:
                    print(f"Error guardando {record['listing_name']}: {e}")

    print("-" * 50)
    print(f"Total encontrados: {total_found}")
    print(f"Total insertados/actualizados: {total_saved}")

if __name__ == "__main__":
    main()