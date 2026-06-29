from sqlalchemy.orm import Session
from datetime import datetime
from models import User, URL
from schemas import UserCreate
from services.auth import hash_password

# --- User CRUD ---

def create_user(db: Session, user: UserCreate) -> User:
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hash_password(user.password)
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user_by_id(db: Session, user_id: int) -> User:
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_username(db: Session, username: str) -> User:
    return db.query(User).filter(User.username == username).first()

def get_user_by_email(db: Session, email: str) -> User:
    return db.query(User).filter(User.email == email).first()

# --- URL CRUD ---

def create_url(
    db: Session,
    original_url: str,
    short_code: str,
    owner_id: int = None,
    expires_at: datetime = None
) -> URL:
    db_url = URL(
        original_url=original_url,
        short_code=short_code,
        owner_id=owner_id,
        expires_at=expires_at
    )
    db.add(db_url)
    db.commit()
    db.refresh(db_url)
    return db_url

def get_url_by_id(db: Session, url_id: int) -> URL:
    return db.query(URL).filter(URL.id == url_id).first()

def get_url_by_short_code(db: Session, short_code: str) -> URL:
    return db.query(URL).filter(URL.short_code == short_code).first()

def get_all_urls(db: Session, skip: int = 0, limit: int = 10) -> list[URL]:
    return db.query(URL).offset(skip).limit(limit).all()

def get_user_urls(db: Session, owner_id: int, skip: int = 0, limit: int = 10) -> list[URL]:
    return db.query(URL).filter(URL.owner_id == owner_id).offset(skip).limit(limit).all()

def update_url(db: Session, url_id: int, updated_url: str) -> URL:
    url = get_url_by_id(db, url_id)
    if not url:
        return None
    url.original_url = updated_url
    db.commit()
    db.refresh(url)
    return url

def delete_url(db: Session, url_id: int) -> URL:
    url = get_url_by_id(db, url_id)
    if not url:
        return None
    db.delete(url)
    db.commit()
    return url