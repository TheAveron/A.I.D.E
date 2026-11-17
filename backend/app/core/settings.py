import os
import warnings
from pathlib import Path

from dotenv import load_dotenv

env_path = Path(__file__).parent.parent / "config" / ".env"
load_dotenv(env_path)

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("No SECRET_KEY environment variable set")

if len(SECRET_KEY) < 32:
    # HS256 tokens are only as safe as this key: anybody who guesses it can sign a token for any user, admins included.
    warnings.warn(
        "SECRET_KEY is shorter than 32 characters; use a long random value "
        "(e.g. python -c 'import secrets; print(secrets.token_urlsafe(48))')",
        stacklevel=2,
    )

ENV = os.getenv("ENV", "development")

if ENV == "development":
    ORIGINS = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

else:
    ORIGINS = []
