from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
import gradio as gr
import requests
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

from app.controllers import health_controller, rag_controller, retrieve_controller, tools_controller

app = FastAPI()

# Cho phép frontend gọi API nếu cần (tránh CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(retrieve_controller.router)
app.include_router(rag_controller.router)
app.include_router(tools_controller.router)
app.include_router(health_controller.router)

Instrumentator(should_ignore_untemplated=False).instrument(app).expose(app)

def format_citation(data: dict) -> str:
    citations = []
    for chunk in data.get("chunks", []):
        meta = chunk.get("meta", {})
        text = chunk.get("text", "")

        citation = f"- {meta.get('metadata', '')}\n{text}\n"
        citations.append(citation)

    if not citations:
        return "Không tìm thấy trích dẫn."

    formatted = (
        "Các luật được trích dẫn:\n"
        + "\n\n"
        + "\n".join(citations)
    )
    return formatted

# ====== GRADIO CHATBOT UI ======
API_URL = "http://localhost:8000/rag"  # gọi API mới

def chat_fn(message, history):
    try:
        resp = requests.post(
            API_URL,
            params={"user_input": message, "k": 4} 
        )
        resp.raise_for_status()
        data = resp.json()

        answer = data["answer"]
        chunks = data["chunks"]

        # ghép citation lại cho dễ đọc
        citations = format_citation(chunks)

        return answer, citations

    except Exception as e:
        return f"Lỗi: {e}", ""

def toggle_fn(citations):
    return gr.update(visible=True, value=citations)


with gr.Blocks() as demo:
    gr.Markdown("## 🤖 Chatbot tư vấn luật")

    chatbot = gr.Chatbot(height=400)
    msg = gr.Textbox(placeholder="Nhập câu hỏi pháp lý của bạn...")
    submit = gr.Button("Gửi")
    
    citation_box = gr.Textbox(label="Trích dẫn luật", visible=False, interactive=False)
    citation_btn = gr.Button("📜 Xem trích dẫn luật", visible=False)

    state_citations = gr.State("")

    def user_submit(message, chat_history):
        chat_history = chat_history + [(message, None)]
        return "", chat_history

    def bot_response(chat_history):
        message = chat_history[-1][0]
        answer, citations = chat_fn(message, chat_history)
        chat_history[-1] = (message, answer)
        return chat_history, gr.update(visible=True), citations

    msg.submit(user_submit, [msg, chatbot], [msg, chatbot]).then(
        bot_response, [chatbot], [chatbot, citation_btn, state_citations]
    )
    submit.click(user_submit, [msg, chatbot], [msg, chatbot]).then(
        bot_response, [chatbot], [chatbot, citation_btn, state_citations]
    )

    citation_btn.click(toggle_fn, state_citations, citation_box)


# mount Gradio vào FastAPI
from fastapi.middleware.wsgi import WSGIMiddleware
from gradio.routes import mount_gradio_app

app = mount_gradio_app(app, demo, path="/")   # UI ngay tại localhost:8000/
