from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
import gradio as gr
import requests
from fastapi.middleware.cors import CORSMiddleware
from gradio.routes import mount_gradio_app

from app.controllers import health_controller, rag_controller, retrieve_controller

app = FastAPI()

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

# Prometheus monitoring
Instrumentator(should_ignore_untemplated=False).instrument(app).expose(app)

# ====== GRADIO CHATBOT UI ======
API_URL = "http://localhost:8000/rag"  # endpoint RAG chính của bạn

def chat_fn(message, history):
    """Gọi API backend để lấy câu trả lời."""
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
