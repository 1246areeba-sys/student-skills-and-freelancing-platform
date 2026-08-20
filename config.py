"""Application configuration.

Reads all sensitive settings from environment variables (loaded from .env).
Never hard-code credentials in this file or anywhere in the codebase.
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables from the .env file if present
load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Base configuration used by the application."""

    # --- Core Flask ---
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")
    DEBUG = os.environ.get("FLASK_DEBUG", "0") == "1"

    # --- Database (SQLite) ---
    # The platform uses a local SQLite file as its primary database.
    # To use a different SQLite path, set DATABASE_URL (e.g. sqlite:///other.db).
    # PostgreSQL support has been removed; this app is SQLite-only.
    #
    # Some PaaS hosts (Render, Railway, Heroku) automatically inject a DATABASE_URL
    # that points at PostgreSQL. If we blindly used that URL (or raised an error
    # here) the app would crash at import time and EVERY request would return 500.
    # To keep the deployed site alive we only honor an explicit sqlite:/// URL and
    # otherwise fall back to the local SQLite database, logging a warning when an
    # unsupported URL was ignored.
    _db_url = (os.environ.get("DATABASE_URL") or "").strip()
    if _db_url.startswith("sqlite:///"):
        SQLALCHEMY_DATABASE_URI = _db_url
    else:
        if _db_url:
            # Injected/unsupported URL (e.g. postgres://) - ignore it, do not crash.
            _scheme = _db_url.split("://", 1)[0] if "://" in _db_url else _db_url
            print(
                "WARNING: Unsupported DATABASE_URL scheme '%s' ignored; "
                "falling back to local SQLite app.db." % _scheme,
                file=sys.stderr,
            )
        SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(BASE_DIR, "app.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- SQLite engine hardening ---
    # SQLite is single-writer: under concurrent load (e.g. the 15s notification
    # poll plus writes) the default engine raises "database is locked" and the
    # request 500s. A generous busy timeout lets connections wait for the writer
    # to finish instead of failing immediately. pool_pre_ping keeps pooled
    # connections healthy. WAL mode (enabled in app.py) allows concurrent readers
    # while a write is in progress, which is what the live polling needs.
    SQLALCHEMY_ENGINE_OPTIONS = {
        "connect_args": {"timeout": 30, "check_same_thread": False},
        "pool_pre_ping": True,
        "pool_recycle": 280,
    }

    # --- Uploads ---
    UPLOAD_FOLDER = os.path.join(BASE_DIR, os.environ.get("UPLOAD_FOLDER", "static/uploads"))
    ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp", "svg", "bmp"}
    ALLOWED_FILE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp", "pdf", "doc", "docx", "txt", "zip", "xls", "xlsx", "ppt", "pptx"}
    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_CONTENT_LENGTH", 16 * 1024 * 1024))

    # --- Platform business rules ---
    PLATFORM_NAME = os.environ.get("PLATFORM_NAME", "SkillBridge")
    PLATFORM_TAGLINE = "Connect Skills. Create Opportunities. Build Your Future."
    PLATFORM_FEE_PERCENT = float(os.environ.get("PLATFORM_FEE_PERCENT", 10))

    # --- Pagination ---
    ITEMS_PER_PAGE = 9
    CHAT_MESSAGES_PER_PAGE = 50
