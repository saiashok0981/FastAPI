from sqlalchemy.orm import Session
from sqlalchemy import func
from models import Click

def log_click(
    db: Session,
    url_id: int,
    ip_address: str = None,
    user_agent: str = None,
    referrer: str = None
) -> Click:
    """Log a single click/redirection event for a shortened URL."""
    click = Click(
        url_id=url_id,
        ip_address=ip_address,
        user_agent=user_agent,
        referrer=referrer
    )
    db.add(click)
    db.commit()
    db.refresh(click)
    return click

def get_url_analytics(db: Session, url_id: int) -> dict:
    """Get summarized analytics for a shortened URL."""
    total_clicks = db.query(func.count(Click.id)).filter(Click.url_id == url_id).scalar() or 0
    clicks = db.query(Click).filter(Click.url_id == url_id).order_by(Click.timestamp.desc()).all()
    
    browsers = {}
    referrers = {}
    
    for click in clicks:
        # Simple browser parsing
        ua = click.user_agent or ""
        if "Chrome" in ua and "Safari" in ua and "Edge" not in ua:
            browser = "Chrome"
        elif "Firefox" in ua:
            browser = "Firefox"
        elif "Safari" in ua and "Chrome" not in ua:
            browser = "Safari"
        elif "Edge" in ua:
            browser = "Edge"
        else:
            browser = "Other/Unknown"
            
        browsers[browser] = browsers.get(browser, 0) + 1
        
        # Simple referrer parsing
        ref = click.referrer or "Direct"
        if not ref.strip():
            ref = "Direct"
        elif "google" in ref.lower():
            ref = "Google Search"
        elif "facebook" in ref.lower():
            ref = "Facebook"
        elif "twitter" in ref.lower() or "t.co" in ref.lower():
            ref = "Twitter/X"
        else:
            ref = ref.split("//")[-1].split("/")[0] # domain only
            
        referrers[ref] = referrers.get(ref, 0) + 1
        
    return {
        "total_clicks": total_clicks,
        "browsers": browsers,
        "referrers": referrers,
        "clicks": clicks
    }
