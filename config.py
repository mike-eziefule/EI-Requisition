"""Default configuration settings."""
import os
from functools import lru_cache

from dotenv import load_dotenv

# Load env vars from .env (only used in local/dev environments)
load_dotenv()

class Settings():
    """Default BaseSettings."""

    env_name: str = "local"
    db_url: str = "sqlite:///./requisition.sqlite"

    # default to SQLite
    app_server: str = "deployment" #change to 'deployment' when hosting
    
    #openai tags
    tags = [
        {
        'name': 'user',
        'description': 'Routes related to users activities'
        },
        {
        'name': 'auth',
        'description': 'Routes related to authentication needs'
        },
        {
        'name': 'link',
        'description': 'Routes connecting pages on the website'
        }
    ]
    
    # Secrets (loaded from environment)
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")  # Fallback to HS256 if not provided

    
    class Config:
        """Load env variables from .env file."""
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    
    """Return the current settings."""
    
    settings = Settings()
    if settings.app_server == "deployment":
        settings.db_url = os.getenv("DATABASE_URL")
    return settings
