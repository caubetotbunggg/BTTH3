from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from app.controllers import health_controller, rag_controller, retrieve_controller, tools_controller

app = FastAPI()

Instrumentator().instrument(app).expose(app)

app.include_router(retrieve_controller.router)
app.include_router(rag_controller.router)
app.include_router(tools_controller.router)
app.include_router(health_controller.router)

@app.get("/")
def read_root():
    return {"Hello": "World"}