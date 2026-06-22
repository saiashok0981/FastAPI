from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional

# 1. Initialize the app
app = FastAPI()

# 2. Define a data model using Pydantic
class Item(BaseModel):
    name: str
    price: float
    description: Optional[str] = None

# In-memory storage for demonstration
items_db = {}

# 3. Define endpoints
@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI!"}