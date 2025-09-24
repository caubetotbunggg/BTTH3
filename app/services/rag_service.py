import asyncio
import time

from app.config.settings import (
    GEMINI_CLIENT, 
    setup_logger, 
    RAG_CONFIG
)
from app.models.rag_model import RAGResponse, RAGRequest
from app.services.retrieve_service import RetrieveService

logger = setup_logger("rag", "../log/rag_info.log")


def create_prompt(chunks, question: str) -> str:
    chunk_text = ""
    for chunk in chunks:
        section = chunk.meta.get("section_title", "Không rõ")
        chunk_text += f"- [{section}] {chunk.text}\n"

    return f"""Bạn là một trợ lý pháp lý chuyên nghiệp.  
Chỉ dựa trên các điều luật sau để trả lời:  
{chunk_text}

Yêu cầu:  
- Trả lời chính xác, súc tích, sử dụng ngôn ngữ pháp lý chuẩn mực.  
- Mỗi kết luận phải kèm trích dẫn đầy đủ (Luật, Điều, Khoản, Điểm nếu có), ví dụ: [BLDS 2015 – Điều 117, Khoản 1].  
- Nếu có nhiều điều luật liên quan, hãy liệt kê đầy đủ.  

Câu hỏi: {question}
"""


async def _get_llm_response_with_timeout(prompt: str, timeout: int = 25) -> str:
    loop = asyncio.get_event_loop()
    try:
        response = await asyncio.wait_for(
            loop.run_in_executor(
                None,
                lambda: GEMINI_CLIENT.models.generate_content(
                    model=RAG_CONFIG["MODEL_NAME"],
                    contents=prompt,
                ),
            ),
            timeout=timeout,
        )
        return response.text
    except asyncio.TimeoutError:
        return "Hệ thống đang bận, vui lòng thử lại sau."


class RAGService:
    @staticmethod
    def rag_pipeline(RAGRequest: RAGRequest):
        start_total = time.perf_counter()

        # --- Step 1: retrieve ---
        start_retrieve = time.perf_counter()
        results = RetrieveService.retrieve(RAGRequest.user_input, k=RAGRequest.k)
        retrieve_time = time.perf_counter() - start_retrieve

        # --- Step 2: prompt ---
        start_prompt = time.perf_counter()
        if not results.chunks:
            prompt = f"Không có điều luật phù hợp với câu hỏi {RAGRequest.user_input}"
        else:
            prompt = create_prompt(results.chunks, RAGRequest.user_input)
        prompt_time = time.perf_counter() - start_prompt

        # --- Step 3: call LLM ---
        start_llm = time.perf_counter()
        response = asyncio.run(_get_llm_response_with_timeout(prompt))
        llm_time = time.perf_counter() - start_llm

        total_time = time.perf_counter() - start_total

        logger.info(
            f"retrieve_time={retrieve_time:.2f}, prompt_time={prompt_time:.2f}, "
            f"llm_time={llm_time:.2f}, total={total_time:.2f}"
        )

        return RAGResponse(answer=response, chunks=results)
