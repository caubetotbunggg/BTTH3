import asyncio
import time

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Query
from google import genai

from app.retrieve import search

load_dotenv()  # Tự động đọc file .env ở cùng thư mục

client = genai.Client()


def create_prompt(chunks, question):
    chunk_text = ""
    for chunk in chunks:
        # lấy từ chunk['meta']['section_title']
        section = chunk["meta"].get("section_title", "Không rõ")
        text = chunk.get("text", "")
        chunk_text += f"- [{section}] {text}\n"

    prompt = f"""Bạn là một trợ lý pháp lý. Hãy tham khảo các điều luật sau:
{chunk_text}

Câu hỏi: {question}
Trả lời kèm theo trích dẫn, ví dụ: [Luật X – Điều Y]."""

    return prompt


def get_llm_response_with_timeout(prompt, timeout=10):
    try:
        start_time = time.time()

        # Gọi LLM (thay thế bằng API call thực tế)
        response = client.models.generate_content(
            model="gemini-2.5-flash", contents=prompt
        )

        elapsed_time = time.time() - start_time

        if elapsed_time > timeout:
            return "Hệ thống đang bận, vui lòng thử lại sau."

        return response

    except asyncio.TimeoutError:
        return "Hệ thống đang bận, vui lòng thử lại sau."


router = APIRouter()


@router.post("/rag")
def rag_endpoint(
    user_input: str = Query(..., description="Câu hỏi hoặc truy vấn người dùng"),
    k: int = Query(5, description="Số lượng kết quả cần trả về"),
):
    try:
        # Tìm kiếm thông tin liên quan
        results = search(user_input, k)
        prompt = create_prompt(results["chunks"], user_input)
        response = get_llm_response_with_timeout(prompt)
        return response.text
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
