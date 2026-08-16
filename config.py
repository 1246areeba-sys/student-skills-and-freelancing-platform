"""Application configuration.

Reads all sensitive settings from environment variables (loaded from .env).
Never hard-code credentials in this file or anywhere in the codebase.
"""
import os
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
    _db_url = os.environ.get("DATABASE_URL")
    if _db_url and _db_url.startswith("postgres://"):
        # Reject legacy PostgreSQL URLs — this app no longer supports them.
        raise RuntimeError(
            "PostgreSQL is no longer supported. Use a sqlite:/// DATABASE_URL or "
            "leave DATABASE_URL unset to use the default app.db SQLite database."
        )
    SQLALCHEMY_DATABASE_URI = _db_url or "sqlite:///" + os.path.join(BASE_DIR, "app.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

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
