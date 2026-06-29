from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
from models import User, URL, Click
from routers.auth import get_current_user

router = APIRouter(
    prefix="/analytics",
    tags=["analytics"]
)

@router.get("/summary")
def get_user_analytics_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve aggregate link statistics for the authenticated user."""
    total_urls = db.query(func.count(URL.id)).filter(URL.owner_id == current_user.id).scalar() or 0
    
    total_clicks = (
        db.query(func.count(Click.id))
        .join(URL, URL.id == Click.url_id)
        .filter(URL.owner_id == current_user.id)
        .scalar()
    ) or 0
    
    return {
        "total_urls": total_urls,
        "total_clicks": total_clicks
    }
