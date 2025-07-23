import asyncio
import logging
import time

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Query
from google import genai

from app.retrieve import search

start_total = time.perf_counter()

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


async def get_llm_response_with_timeout(prompt, timeout=15):
    loop = asyncio.get_event_loop()

    try:

        # Gọi Gemini API trong thread riêng để không block event loop
        response = await asyncio.wait_for(
            loop.run_in_executor(
                None,
                lambda: client.models.generate_content(
                    model="gemini-2.5-flash", contents=prompt
                ),
            ),
            timeout=timeout,
        )

        return response.text  # hoặc response.candidates[0].content nếu cần tùy vào API

    except asyncio.TimeoutError:
        return "Hệ thống đang bận, vui lòng thử lại sau."


router = APIRouter()


@router.post("/rag")
def rag_endpoint(
    user_input: str = Query(..., description="Câu hỏi hoặc truy vấn người dùng"),
    k: int = Query(5, description="Số lượng kết quả cần trả về"),
):
    start_total = time.perf_counter()

    try:
        # Tìm kiếm thông tin liên quan
        start_retrieve = time.perf_counter()
        results = search(user_input, k)
        retrieve_time = time.perf_counter() - start_retrieve

        start_prompt = time.perf_counter()
        prompt = create_prompt(results["chunks"], user_input)
        prompt_time = time.perf_counter() - start_prompt

        # Gọi LLM với prompt đã tạo
        start_llm = time.perf_counter()
        response = asyncio.run(get_llm_response_with_timeout(prompt))
        if not response:
            # Chạy lại nếu không có phản hồi
            response = asyncio.run(get_llm_response_with_timeout(prompt))
            if not response:
                raise HTTPException(status_code=500, detail="Không có phản hồi từ LLM")
        llm_time = time.perf_counter() - start_llm
        total_time = time.perf_counter() - start_total

        logger = logging.getLogger()

        # Xóa hết handler cũ
        logger.handlers.clear()

        # Ghi log ra file mới
        logging.basicConfig(
            filename="../BTTH3/log/rag.log",
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s:%(message)s",
            encoding="utf-8",
        )
        logger.info(
            f"retrieve_time={retrieve_time:.2f},prompt_time={prompt_time:.2f},"
            f"llm_time={llm_time:.2f},total={total_time:.2f}"
        )
        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
