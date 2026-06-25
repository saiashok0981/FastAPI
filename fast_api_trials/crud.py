from sqlalchemy.orm import Session

from models import URL
from schemas import URLCreate, URLUpdate


def create_url(
    db: Session,
    original_url: str,
    short_code: str
):
    db_url = URL(
        original_url=original_url,
        short_code=short_code
    )

    db.add(db_url)
    db.commit()
    db.refresh(db_url)

    return db_url


def get_url_by_id(
    db: Session,
    url_id: int
):
    return (
        db.query(URL)
        .filter(URL.id == url_id)
        .first()
    )


def get_url_by_short_code(
    db: Session,
    short_code: str
):
    return (
        db.query(URL)
        .filter(URL.short_code == short_code)
        .first()
    )


def get_all_urls(
    db: Session,
    skip: int = 0,
    limit: int = 10
):
    return (
        db.query(URL)
        .offset(skip)
        .limit(limit)
        .all()
    )


def update_url(
    db: Session,
    url_id: int,
    updated_url: str
):
    url = get_url_by_id(db, url_id)

    if not url:
        return None

    url.original_url = updated_url

    db.commit()
    db.refresh(url)

    return url


def delete_url(
    db: Session,
    url_id: int
):
    url = get_url_by_id(db, url_id)

    if not url:
        return None

    db.delete(url)
    db.commit()

    return url