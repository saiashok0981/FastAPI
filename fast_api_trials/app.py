from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager

from database import get_db, engine, Base
from models import URL
from schemas import URLCreate

# 1. Create a lifespan function to handle startup/shutdown logic
@asynccontextmanager
async def lifespan(app: FastAPI):
    # This will now only run when the FastAPI server actually starts
    Base.metadata.create_all(bind=engine)
    yield  # The app runs here
    # (Any cleanup code would go here)

# 2. Pass the lifespan to your FastAPI instance
app = FastAPI(lifespan=lifespan)


@app.post("/urls")
def create_url(
    url: URLCreate,
    db: Session = Depends(get_db)
):
    db_url = URL(
        original_url=url.original_url,
        short_code=url.short_code
    )

    db.add(db_url)
    db.commit()
    db.refresh(db_url)

    return {
        "message": "URL created successfully",
        "id": db_url.id
    }