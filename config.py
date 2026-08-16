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

    # --- Database (PostgreSQL via Neon) ---
    # Fall back to a local SQLite file ONLY if DATABASE_URL is not provided,
    # so the app can still boot for quick local testing.
    _db_url = os.environ.get("DATABASE_URL")
    if _db_url and _db_url.startswith("postgres://"):
        _db_url = _db_url.replace("postgres://", "postgresql://", 1)
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
