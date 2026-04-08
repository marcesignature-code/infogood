from flask import Flask
from slugify import slugify
from . import context_processors
import os
from dotenv import load_dotenv
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse

from .extensions import db, migrate, login_manager

load_dotenv()


def _ensure_sslmode(database_url: str) -> str:
    if not database_url:
        return database_url
    parsed = urlparse(database_url)
    q = dict(parse_qsl(parsed.query))
    if "sslmode" not in q:
        q["sslmode"] = "require"
    new_query = urlencode(q)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment))


def create_app():
    app = Flask(__name__)

    for processor in context_processors.all_context_processors:
        app.context_processor(processor)

    database_url = os.getenv("DATABASE_URL")
    database_url = _ensure_sslmode(database_url)

    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }

    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev_key")
    app.config["DEBUG"] = os.getenv("DEBUG", "False").lower() in ("true", "1")

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    with app.app_context():
        from . import models  # noqa: F401

    from .routes import main, dashboard_bp
    from .auth import auth_bp

    app.register_blueprint(main)
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)

    app.jinja_env.filters["slugify"] = slugify

    return app