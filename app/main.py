from fastapi import FastAPI

from app.rag import router as rag_router
from app.retrieve import router as retrieve_router

app = FastAPI()
app.include_router(retrieve_router)
app.include_router(rag_router)
