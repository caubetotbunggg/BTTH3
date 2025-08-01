from fastapi import FastAPI

from app.retrieve import router as retrieve_router

app = FastAPI()
app.include_router(retrieve_router)
