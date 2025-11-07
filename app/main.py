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
        return f"❌ Lỗi kết nối: {str(e)}"

# ====== CUSTOM CSS ======
custom_css = """
.gradio-container {
    max-width: 900px !important;
    margin: auto !important;
}

.header-title {
    text-align: center;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 2.5em !important;
    font-weight: bold;
    margin-bottom: 0.5em;
}

.header-subtitle {
    text-align: center;
    color: #666;
    font-size: 1.1em;
    margin-bottom: 2em;
}

.chat-container {
    border-radius: 15px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.input-box {
    border-radius: 10px !important;
}

.submit-btn {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    transition: transform 0.2s !important;
}

.submit-btn:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4) !important;
}

.clear-btn {
    border-radius: 10px !important;
    border: 2px solid #e0e0e0 !important;
}

.examples-box {
    background: #f8f9fa;
    border-radius: 10px;
    padding: 15px;
    margin-top: 20px;
}

.examples-box strong {
    color: #333 !important;
    font-size: 1.05em;
}

/* Fix cho Examples trong Gradio - màu chữ tối hơn */
.gradio-examples button {
    color: #333 !important;
    background: white !important;
    border: 1px solid #ddd !important;
}

.gradio-examples button:hover {
    background: #f0f0f0 !important;
    border-color: #667eea !important;
}

.footer-text {
    text-align: center;
    color: #999;
    font-size: 0.9em;
    margin-top: 2em;
    padding-top: 1em;
    border-top: 1px solid #e0e0e0;
}

/* Fix avatar bot */
.message-row.bot img {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 8px;
    border-radius: 50%;
}
"""

# ====== GRADIO UI ======
with gr.Blocks(css=custom_css, theme=gr.themes.Soft()) as demo:
    # Header
    gr.HTML("""
        <div class="header-title">
            ⚖️ Trợ Lý Pháp Luật Thông Minh
        </div>
        <div class="header-subtitle">
            Hỏi đáp tư vấn pháp luật nhanh chóng và chính xác với công nghệ AI
        </div>
    """)
    
    # Chat Interface
    with gr.Row():
        with gr.Column(scale=1):
            chatbot = gr.Chatbot(
                height=500,
                type="messages",
                show_label=False,
                container=True
            )
    
    # Input Area
    with gr.Row():
        with gr.Column(scale=9):
            msg = gr.Textbox(
                placeholder="💬 Nhập câu hỏi pháp lý của bạn... (VD: Thủ tục ly hôn thế nào?)",
                show_label=False,
                container=False
            )
        with gr.Column(scale=1, min_width=100):
            submit = gr.Button("📤 Gửi", variant="primary")
    
    with gr.Row():
        clear = gr.Button("🗑️ Xóa lịch sử")
    
    # Examples
    gr.HTML("""
        <div class="examples-box">
            <strong>💡 Câu hỏi mẫu - Click để thử:</strong>
        </div>
    """)
    
    gr.Examples(
        examples=[
            "Thủ tục ly hôn đơn phương như thế nào?",
            "Quyền và nghĩa vụ của người lao động là gì?",
            "Hợp đồng mua bán nhà đất cần những giấy tờ gì?",
            "Thời hiệu khởi kiện vụ án dân sự là bao lâu?",
        ],
        inputs=msg
    )
    
    # Footer
    gr.HTML("""
        <div class="footer-text">
            ⚡ Powered by RAG Technology | 🔒 Thông tin được bảo mật<br>
            📌 Lưu ý: Đây là công cụ hỗ trợ tham khảo, không thay thế tư vấn pháp lý chuyên nghiệp
        </div>
    """)

    # Event Handlers
    def user_submit(message, chat_history):
        if not message.strip():
            return message, chat_history
        # Convert to messages format
        chat_history = chat_history + [{"role": "user", "content": message}]
        return "", chat_history

    def bot_response(chat_history):
        if not chat_history or chat_history[-1]["role"] != "user":
            return chat_history
        message = chat_history[-1]["content"]
        answer = chat_fn(message, chat_history)
        chat_history = chat_history + [{"role": "assistant", "content": answer}]
        return chat_history

    # Submit on Enter or Click
    msg.submit(user_submit, [msg, chatbot], [msg, chatbot]).then(
        bot_response, [chatbot], [chatbot]
    )
    submit.click(user_submit, [msg, chatbot], [msg, chatbot]).then(
        bot_response, [chatbot], [chatbot]
    )
    
    # Clear chat history
    clear.click(lambda: [], None, chatbot, queue=False)

app = mount_gradio_app(app, demo, path="/")