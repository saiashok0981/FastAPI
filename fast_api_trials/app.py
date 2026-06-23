from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import URL
from schemas import URLCreate

app = FastAPI()


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