from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
import gradio as gr
import requests
import os
from fastapi.middleware.cors import CORSMiddleware
from gradio.routes import mount_gradio_app
from weaviate import connect_to_weaviate_cloud
from weaviate.config import AdditionalConfig, Timeout
from weaviate.auth import AuthApiKey
from contextlib import asynccontextmanager

from app.controllers import health_controller, rag_controller, retrieve_controller

# ====== WEAVIATE CLIENT (managed lifecycle) ======
WEAVIATE_CLIENT = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan handler: initialize resources on startup, cleanup on shutdown.

    This replaces the deprecated `@app.on_event("startup")` and
    `@app.on_event("shutdown")` handlers.
    """
    global WEAVIATE_CLIENT
    # startup
    WEAVIATE_CLIENT = connect_to_weaviate_cloud(
        cluster_url=os.getenv("WEAVIATE_URL"),
        auth_credentials=AuthApiKey(os.getenv("WEAVIATE_API_KEY")),
        additional_config=AdditionalConfig(timeout=Timeout(query=60)),
    )
    print("[Startup] ✅ Weaviate client initialized")

    try:
        yield
    finally:
        # shutdown
        if WEAVIATE_CLIENT:
            WEAVIATE_CLIENT.close()
            print("[Shutdown] 🧹 Weaviate client closed")

# ====== FASTAPI APP ======
app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(retrieve_controller.router)
app.include_router(rag_controller.router)
app.include_router(health_controller.router)

# ====== PROMETHEUS ======
Instrumentator(should_ignore_untemplated=False).instrument(app).expose(app)

# ====== GRADIO CHATBOT UI ======
API_URL = os.getenv("API_URL", "http://localhost:8000/rag")

def chat_fn(message, history):
    try:
        resp = requests.post(
            API_URL,
            params={"user_input": message, "k": 4}
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("answer", "Không có câu trả lời phù hợp.")
    except Exception as e:
        return f"Lỗi: {e}"

# ====== GRADIO UI ======
with gr.Blocks() as demo:
    gr.Markdown("## 🤖 Chatbot tư vấn pháp luật (RAG)")
    chatbot = gr.Chatbot(height=400)
    msg = gr.Textbox(placeholder="Nhập câu hỏi pháp lý của bạn...")
    submit = gr.Button("Gửi")

    def user_submit(message, chat_history):
        chat_history = chat_history + [(message, None)]
        return "", chat_history

    def bot_response(chat_history):
        message = chat_history[-1][0]
        answer = chat_fn(message, chat_history)
        chat_history[-1] = (message, answer)
        return chat_history

    msg.submit(user_submit, [msg, chatbot], [msg, chatbot]).then(
        bot_response, [chatbot], [chatbot]
    )
    submit.click(user_submit, [msg, chatbot], [msg, chatbot]).then(
        bot_response, [chatbot], [chatbot]
    )

app = mount_gradio_app(app, demo, path="/")
