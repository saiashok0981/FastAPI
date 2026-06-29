import os
import time
import base64
import json
import hmac
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "production-style-secret-key-change-in-prod")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# --- Password Hashing Helpers ---

def hash_password(password: str) -> str:
    """Hash password using PBKDF2 with a random salt."""
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
    # Store salt and key in hex format separated by a colon
    return f"{salt.hex()}:{key.hex()}"

def verify_password(password: str, hashed_password: str) -> bool:
    """Verify password by matching PBKDF2 hash of input against stored hash."""
    try:
        salt_hex, key_hex = hashed_password.split(":")
        salt = bytes.fromhex(salt_hex)
        key = bytes.fromhex(key_hex)
        new_key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
        return hmac.compare_digest(key, new_key)
    except Exception:
        return False

# --- Custom JWT Hashing Helpers ---

def base64url_encode(data: bytes) -> str:
    """Encode bytes to a base64url string."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")

def base64url_decode(data: str) -> bytes:
    """Decode a base64url string to bytes."""
    padding = "=" * (4 - len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Generate a signed JWT token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Store expiration as epoch timestamp
    to_encode.update({"exp": int(expire.timestamp())})
    
    header = {"alg": ALGORITHM, "typ": "JWT"}
    header_b64 = base64url_encode(json.dumps(header).encode("utf-8"))
    payload_b64 = base64url_encode(json.dumps(to_encode).encode("utf-8"))
    
    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    signature = hmac.new(SECRET_KEY.encode("utf-8"), signing_input, hashlib.sha256).digest()
    signature_b64 = base64url_encode(signature)
    
    return f"{header_b64}.{payload_b64}.{signature_b64}"

def decode_access_token(token: str) -> Optional[dict]:
    """Decode and verify a signed JWT token."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        
        header_b64, payload_b64, signature_b64 = parts
        signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
        
        # Verify signature
        expected_signature = hmac.new(SECRET_KEY.encode("utf-8"), signing_input, hashlib.sha256).digest()
        if not hmac.compare_digest(base64url_decode(signature_b64), expected_signature):
            return None
        
        # Decode and inspect payload
        payload = json.loads(base64url_decode(payload_b64).decode("utf-8"))
        
        # Check expiration
        exp = payload.get("exp")
        if exp is None or exp < time.time():
            return None
            
        return payload
    except Exception:
        return None
