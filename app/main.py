from fastapi import FastAPI

from app.controllers import health_controller, rag_controller, retrieve_controller

app = FastAPI()

app.include_router(retrieve_controller.router)
app.include_router(rag_controller.router)
app.include_router(health_controller.router)

@app.get("/")
def read_root():
    return {"Hello": "World"}