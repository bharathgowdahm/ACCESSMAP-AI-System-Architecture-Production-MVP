"""Security, hashing, input sanitization, and role definitions."""
import html
import re
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserRole:
    GUEST = "guest"
    CONTRIBUTOR = "contributor"
    VERIFIER = "trusted_verifier"
    MODERATOR = "moderator"
    ADMIN = "administrator"

    ALL = {GUEST, CONTRIBUTOR, VERIFIER, MODERATOR, ADMIN}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def sanitize_text(text: str) -> str:
    """Sanitizes user input to prevent XSS attacks in rendered HTML/Markdown."""
    if not text:
        return ""
    cleaned = html.escape(text.strip())
    # Strip dangerous URI schemes
    cleaned = re.sub(r"javascript:", "", cleaned, flags=re.IGNORECASE)
    return cleaned


def validate_coordinates(lat: float, lon: float) -> bool:
    """Validates real-world geographic bounds."""
    return -90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0
