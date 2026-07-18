from fastapi import FastAPI, Depends, HTTPException, status, Request, BackgroundTasks
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from database import engine, Base, get_db
from routers import urls, auth, analytics, health
import crud
from services.analytics import log_click

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield 

app = FastAPI(
    title="Production-Style URL Shortener API",
    description="A portfolio-quality REST API using FastAPI, SQLAlchemy, and PostgreSQL.",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS Middleware here
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    db_url = crud.get_url_by_short_code(db, short_code=short_code)
    
    if db_url is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shortened URL not found"
        )
        
    if db_url.expires_at and db_url.expires_at < datetime.now(timezone.utc).replace(tzinfo=None):
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="This shortened URL has expired"
        )
        
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    referrer = request.headers.get("referer")
    
    background_tasks.add_task(
        log_click,
        db=db,
        url_id=db_url.id,
        ip_address=ip_address,
        user_agent=user_agent,
        referrer=referrer
    )
    
    return RedirectResponse(url=db_url.original_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)