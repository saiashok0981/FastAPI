import secrets
import string
import urllib.parse
from sqlalchemy.orm import Session

# We import crud inside the function or at the top. Let's import it here.
import crud

BASE62_CHARACTERS = string.ascii_letters + string.digits

def generate_short_code(db: Session, length: int = 6) -> str:
    """Generate a unique random Base62 short code."""
    for _ in range(10):
        code = "".join(secrets.choice(BASE62_CHARACTERS) for _ in range(length))
        # Check collision
        if not crud.get_url_by_short_code(db, code):
            return code
    raise ValueError("Failed to generate a unique short code after 10 attempts")

def is_valid_url(url: str) -> bool:
    """Validate URL format."""
    try:
        result = urllib.parse.urlparse(url)
        # Check that it has a scheme (e.g. http/https) and network location (e.g. domain)
        return all([result.scheme, result.netloc]) and result.scheme in ("http", "https")
    except Exception:
        return False
