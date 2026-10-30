
import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:

    # Flask Security
    SECRET_KEY = os.getenv("SECRET_KEY")

    # Supabase Configuration
    SUPABASE_URL = os.getenv("SUPABASE_URL")

    SUPABASE_KEY = os.getenv(
        "SUPABASE_SERVICE_ROLE_KEY"
    ) or os.getenv("SUPABASE_KEY")

    # Application Settings
    DEBUG = False
    TESTING = False

    # Session Configuration
    SESSION_TYPE = "filesystem"
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    SESSION_COOKIE_SECURE = (
        os.getenv("FLASK_ENV") == "production"
    )

    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)

    # Upload Configuration
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024

    # Validate Configuration
    @classmethod
    def validate(cls):

        if not cls.SECRET_KEY:
            raise RuntimeError(
                "SECRET_KEY is missing in environment variables"
            )

        if len(cls.SECRET_KEY) < 32:
            raise RuntimeError(
                "SECRET_KEY must be at least 32 characters"
            )
