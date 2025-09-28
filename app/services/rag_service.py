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

def paraphrase(question: str) -> str:
    response = GEMINI_CLIENT.models.generate_content(
        model=RAG_CONFIG["MODEL_NAME"],
        contents=f"""
Bạn là một trợ lý pháp luật.
Nhiệm vụ của bạn là viết lại câu hỏi pháp lý của người dùng sao cho rõ ràng, cụ thể, và sát nghĩa với ngôn ngữ văn bản pháp luật.  

Nguyên tắc:
- Giữ nguyên ý nghĩa gốc, không thêm thông tin mới.
- Biến câu hỏi mơ hồ thành câu hỏi rõ ràng, dễ truy vấn trong luật.
- Sử dụng từ vựng pháp lý chính xác (ví dụ: "đăng ký nghĩa vụ quân sự", "tuổi", "thời điểm", "trách nhiệm").

Ví dụ:
Người dùng: "nam giới phải đi nghĩa vụ khi nào"
Kết quả: "Nam giới bao nhiêu tuổi thì phải đăng ký nghĩa vụ quân sự theo quy định pháp luật?"

Người dùng: {question}
Kết quả:""",
    )
    return response.text


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


async def _get_llm_response_with_timeout(prompt: str, timeout: int = 60) -> str:
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
        paraphrased_question = paraphrase(RAGRequest.user_input)
        
        print(f"Paraphrased question: {paraphrased_question}")
        logger.info(f"Paraphrased question: {paraphrased_question}")
        
        results = RetrieveService.retrieve(paraphrased_question, k=RAGRequest.k)
        retrieve_time = time.perf_counter() - start_retrieve

        # --- Step 2: prompt ---
        start_prompt = time.perf_counter()
        if not results.chunks:
            prompt = f"Không có điều luật phù hợp với câu hỏi {RAGRequest.user_input}"
            return RAGResponse(answer=prompt, chunks=results)
        else:
            prompt = create_prompt(results.chunks, paraphrased_question)
        prompt_time = time.perf_counter() - start_prompt

        # --- Step 3: call LLM ---
        start_llm = time.perf_counter()
        response = asyncio.run(_get_llm_response_with_timeout(prompt))
        llm_time = time.perf_counter() - start_llm

        total_time = time.perf_counter() - start_total

        print(
            f"retrieve_time={retrieve_time:.2f}, prompt_time={prompt_time:.2f}, "
            f"llm_time={llm_time:.2f}, total={total_time:.2f}"
        )
        logger.info(
            f"retrieve_time={retrieve_time:.2f}, prompt_time={prompt_time:.2f}, "
            f"llm_time={llm_time:.2f}, total={total_time:.2f}"
        )

        return RAGResponse(answer=response, chunks=results)
