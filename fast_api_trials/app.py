from fastapi import FastAPI, Depends, HTTPException, status, Request, BackgroundTasks
from fastapi.responses import RedirectResponse
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from database import engine, Base, get_db
from routers import urls, auth, analytics, health
import crud
from services.analytics import log_click

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Auto-create tables on startup
    Base.metadata.create_all(bind=engine)
    yield 

app = FastAPI(
    title="Production-Style URL Shortener API",
    description="A portfolio-quality REST API using FastAPI, SQLAlchemy, and PostgreSQL.",
    version="1.0.0",
    lifespan=lifespan
)

# Include Routers
app.include_router(auth.router)
app.include_router(urls.router)
app.include_router(analytics.router)
app.include_router(health.router)

@app.get("/{short_code}", response_class=RedirectResponse)
def redirect_to_original_url(
    short_code: str,
    request: Request,
    background_tasks: BackgroundTasks,
    db=Depends(get_db)
):
    """Redirect to the original destination URL and record analytics."""
    db_url = crud.get_url_by_short_code(db, short_code=short_code)
    
    if db_url is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shortened URL not found"
        )
        
    # Check if URL is expired
    if db_url.expires_at and db_url.expires_at < datetime.now(timezone.utc).replace(tzinfo=None):
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="This shortened URL has expired"
        )
        
    # Gather client details
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    referrer = request.headers.get("referer")
    
    # Track click asynchronously in the background
    background_tasks.add_task(
        log_click,
        db=db,
        url_id=db_url.id,
        ip_address=ip_address,
        user_agent=user_agent,
        referrer=referrer
    )
    
    # Use 307 (Temporary Redirect) to avoid browser caching of redirects,
    # ensuring that every visit is logged in the analytics.
    return RedirectResponse(url=db_url.original_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)