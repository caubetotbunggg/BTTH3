from fastapi import FastAPI

from app.controllers import rag_controller, retrieve_controller

app = FastAPI()

app.include_router(retrieve_controller.router)
app.include_router(rag_controller.router)
