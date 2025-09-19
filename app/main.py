from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import CollectorRegistry, generate_latest
import threading
import time
import requests
import os
from dotenv import load_dotenv

from app.controllers import health_controller, rag_controller, retrieve_controller, tools_controller

app = FastAPI()

registry = CollectorRegistry()
instrumentator = Instrumentator(registry=registry)
Instrumentator().instrument(app).expose(app)

# Grafana Cloud Remote Write config
GRAFANA_PUSH_URL = os.getenv("GRAFANA_URL", "<push_url>")
GRAFANA_USER = os.getenv("GRAFANA_USER", "<user_id>")
GRAFANA_API_KEY = os.getenv("GRAFANA_API_KEY", "<api_key>")

def push_metrics_periodically(interval=15):
    """Push metrics to Grafana Cloud every `interval` seconds"""
    while True:
        try:
            metrics_data = generate_latest(registry)
            response = requests.post(
                GRAFANA_PUSH_URL,
                data=metrics_data,
                headers={"Content-Type": "text/plain; version=0.0.4"},
                auth=(GRAFANA_USER, GRAFANA_API_KEY)
            )
            if response.status_code != 200:
                print("Failed to push metrics:", response.text)
        except Exception as e:
            print("Error pushing metrics:", e)
        time.sleep(interval)

# Start background thread to push metrics
threading.Thread(target=push_metrics_periodically, daemon=True).start()


app.include_router(retrieve_controller.router)
app.include_router(rag_controller.router)
app.include_router(tools_controller.router)
app.include_router(health_controller.router)

@app.get("/")
def read_root():
    return {"Hello": "World"}