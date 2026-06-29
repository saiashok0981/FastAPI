from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from typing import List, Optional

import crud
from database import get_db
from schemas import (
    URLCreate, URLUpdate, URLResponse, URLCreateResponse, URLAnalyticsResponse
)
from routers.auth import get_current_user, get_optional_current_user
from services.shortner import generate_short_code, is_valid_url
from services.qr import generate_qr_code
from services.analytics import get_url_analytics
from models import User

router = APIRouter(
    prefix="/urls",
    tags=["urls"]
)

@router.post("", response_model=URLCreateResponse, status_code=status.HTTP_200_OK)
def create_url(
    url: URLCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Create a new shortened URL mapping."""
    if not is_valid_url(url.original_url):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid destination URL format"
        )
    
    # Process short code selection
    if url.short_code:
        db_url = crud.get_url_by_short_code(db, short_code=url.short_code)
        if db_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Short code already registered"
            )
        short_code = url.short_code
    else:
        short_code = generate_short_code(db)
        
    # Process expiration offset
    expires_at = None
    if url.expires_in_days is not None:
        if url.expires_in_days <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="expires_in_days must be a positive integer"
            )
        expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=url.expires_in_days)
        
    owner_id = current_user.id if current_user else None
    
    new_url = crud.create_url(
        db=db, 
        original_url=url.original_url, 
        short_code=short_code, 
        owner_id=owner_id,
        expires_at=expires_at
    )
    
    return URLCreateResponse(message="URL created successfully", id=new_url.id)


@router.get("", response_model=List[URLResponse])
def read_user_urls(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve all shortened URLs owned by the current authenticated user."""
    return crud.get_user_urls(db, owner_id=current_user.id, skip=skip, limit=limit)


@router.get("/{short_code}", response_model=URLResponse)
def read_url_by_short_code(short_code: str, db: Session = Depends(get_db)):
    """Retrieve details for a specific shortened URL by its short code."""
    db_url = crud.get_url_by_short_code(db, short_code=short_code)
    if db_url is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="URL not found")
    return db_url


@router.put("/{short_code}", response_model=URLResponse)
def update_url(
    short_code: str,
    url: URLUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update the target destination URL. Restrict to the URL owner."""
    if not is_valid_url(url.original_url):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid destination URL format"
        )
        
    db_url = crud.get_url_by_short_code(db, short_code=short_code)
    if db_url is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="URL not found")
        
    if db_url.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to edit this URL"
        )
        
    updated = crud.update_url(db, url_id=db_url.id, updated_url=url.original_url)
    return updated


@router.delete("/{short_code}")
def delete_url(
    short_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a shortened URL. Restrict to the URL owner."""
    db_url = crud.get_url_by_short_code(db, short_code=short_code)
    if db_url is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="URL not found")
        
    if db_url.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this URL"
        )
        
    crud.delete_url(db, url_id=db_url.id)
    return {"message": "URL deleted successfully"}


@router.get("/{short_code}/qr")
def get_url_qr_code(short_code: str, db: Session = Depends(get_db)):
    """Generate and serve a QR code image linking to the short URL destination."""
    db_url = crud.get_url_by_short_code(db, short_code=short_code)
    if db_url is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="URL not found")
    
    # We construct the redirect URL path dynamically (or just point to the original)
    # Using the short_code path is standard. Let's assume redirect URL is standard
    # E.g. http://localhost:8000/{short_code}
    short_url = f"http://localhost:8000/{short_code}"
    qr_img_bytes = generate_qr_code(short_url)
    
    return Response(content=qr_img_bytes, media_type="image/png")


@router.get("/{short_code}/analytics", response_model=URLAnalyticsResponse)
def read_url_analytics(
    short_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve detailed redirection analytics. Restrict to the URL owner."""
    db_url = crud.get_url_by_short_code(db, short_code=short_code)
    if db_url is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="URL not found")
        
    if db_url.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view analytics for this URL"
        )
        
    analytics = get_url_analytics(db, url_id=db_url.id)
    return {
        "id": db_url.id,
        "original_url": db_url.original_url,
        "short_code": db_url.short_code,
        "created_at": db_url.created_at,
        "expires_at": db_url.expires_at,
        "owner_id": db_url.owner_id,
        "click_count": analytics["total_clicks"],
        "clicks": analytics["clicks"]
    }