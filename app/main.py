from fastapi import FastAPI

from app.controllers import retrieve_controller

app = FastAPI()

app.include_router(retrieve_controller.router)
