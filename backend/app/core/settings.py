import os
from pathlib import Path

from dotenv import load_dotenv

env_path = Path(__file__).parent / "config" / ".env"
load_dotenv(env_path)

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("No SECRET_KEY environment variable set")

ENV = os.getenv("ENV", "development")

# Example of CORS origins based on environment
if ENV == "production":
    ORIGINS = ["https://example.com"]  # production frontend URL
else:
    ORIGINS = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
