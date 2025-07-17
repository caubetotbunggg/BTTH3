from fastapi import APIRouter, FastAPI, Query
from pydantic import BaseModel
from app.retrieve import router as retrieve_router

app = FastAPI()
app.include_router(retrieve_router)