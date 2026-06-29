from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional, List
from datetime import datetime

# --- Authentication & User Schemas ---

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None


# --- URL Schemas ---

class URLCreate(BaseModel):
    original_url: str
    short_code: Optional[str] = None
    expires_in_days: Optional[int] = None

class URLUpdate(BaseModel):
    original_url: str

class URLResponse(BaseModel):
    id: int
    original_url: str
    short_code: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    owner_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)

class URLCreateResponse(BaseModel):
    message: str
    id: int


# --- Analytics Schemas ---

class ClickResponse(BaseModel):
    id: int
    timestamp: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    referrer: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class URLAnalyticsResponse(BaseModel):
    id: int
    original_url: str
    short_code: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    owner_id: Optional[int] = None
    click_count: int
    clicks: List[ClickResponse]

    model_config = ConfigDict(from_attributes=True)