import asyncio
import os
from dotenv import load_dotenv
import time
from elysia import configure

from app.config.settings import (
    setup_logger, GROQ_CLIENT, GROQ_CLIENT_B
)
from app.models.rag_model import RAGResponse, RAGRequest

load_dotenv()

logger = setup_logger("rag", "../log/rag_info.log")

def chunk_to_text(chunks: list) -> str:
    all_chunks = {}
    for chunk in chunks:
        # tạo key unique để loại trùng (dựa trên law_id + text)
        law_id = chunk.meta if chunk.meta else ""
        key = f"{law_id}_{chunk.text}"
        all_chunks[key] = chunk   # dict override nếu gặp key trùng

    # kết quả unique
    unique_chunks = list(all_chunks.values())

    # build prompt text
    chunk_text = ""
    for chunk in unique_chunks:
        section = chunk.meta if chunk.meta else "Không rõ"
        chunk_text += f"- [{section}] {chunk.text}\n"

    return chunk_text

def create_prompt(reasoning_response: str, question: str) -> str:
    return f"""Bạn là một trợ lý pháp lý chuyên nghiệp.

Trước hết, hãy trả lời **dựa trên nội dung phân tích và kết quả truy vấn (reasoning/ retrieved reasoning)** được cung cấp dưới đây — nội dung này có thể là tóm tắt các điều luật, trích dẫn, và các phân tích trung gian do hệ thống thu thập:

{reasoning_response}

Yêu cầu:

- Ưu tiên diễn giải và trích dẫn theo văn bản pháp luật **mới nhất, còn hiệu lực**, nếu có nhiều văn bản điều chỉnh cùng một vấn đề (ví dụ: Luật Cư trú 2020 thay thế Luật Cư trú 2006).
- Trả lời **chính xác, súc tích, ngắn gọn**, sử dụng ngôn ngữ pháp lý chuẩn mực tiếng Việt.
- Mỗi kết luận phải kèm trích dẫn đầy đủ (tên văn bản luật, năm ban hành, Điều, Khoản, Điểm nếu có).
- Nếu không đầy đủ để kết luận, nêu rõ **những quy định, điều khoản hoặc văn bản cần có thêm** để có thể kết luận chính xác.
- Khi cần thiết, bạn được phép đưa ra **gợi ý tham khảo ngoài** (ví dụ: hướng điều tra thêm, các văn bản liên quan nên kiểm tra), nhưng **phân biệt rõ** phần gợi ý này với phần trích dẫn chính thức.

Lưu ý kỹ thuật: reasoning_response là **nguồn thông tin tham khảo chính** — đối xử như một bản tóm tắt đã được hệ thống biên soạn từ các văn bản pháp luật và tài liệu liên quan. Tuy nhiên, khi có thể, hãy ưu tiên trích dẫn tên văn bản và vị trí luật (nếu có) thay vì chỉ copy-tóm tắt.

**TẤT CẢ câu trả lời phải viết bằng tiếng Việt.**

Câu hỏi: {question}
"""

async def _get_llm_response_with_timeout(prompt: str, timeout: int = 60) -> str:
    loop = asyncio.get_event_loop()
    try:
        response = await asyncio.wait_for(
            loop.run_in_executor(
                None,
                lambda: GROQ_CLIENT_B.chat.completions.create(
                    messages=[
                        {
                            "role": "assistant",
                            "content": prompt,
                        }
                    ],
                    model="openai/gpt-oss-120b",
                    temperature=0.2,
                ),
            ),
            timeout=timeout,
        )
        return response.choices[0].message.content
    except asyncio.TimeoutError:
        return "Hệ thống đang bận, vui lòng thử lại sau."


class RAGService:
    @staticmethod
    def rag_pipeline(RAGRequest: RAGRequest):
        start_total = time.perf_counter()

        # --- Step 1: retrieve ---
        start_retrieve = time.perf_counter()
        
        retrieve_time = time.perf_counter() - start_retrieve

        # --- Step 2: prompt ---
        start_prompt = time.perf_counter()
        
        prompt_time = time.perf_counter() - start_prompt

        # --- Step 3: call LLM ---
        start_llm = time.perf_counter()
 
        WEAVIATE_URL = os.getenv("WEAVIATE_URL")
        WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY")
        GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

        configure(
            base_model="gemini-2.0-flash-lite",
            base_provider="gemini",
            complex_model="gemini-2.0-flash",
            complex_provider="gemini",
            gemini_api_key=GEMINI_API_KEY# replace with your API key
        )

        configure(
            wcd_url= WEAVIATE_URL, # replace with your WCD_URL
            wcd_api_key= WEAVIATE_API_KEY, # replace with your WCD_API_KEY
        )
        from elysia import Tree
        tree = Tree()
        QUES = RAGRequest.user_input
        resoning_response, objects = tree(QUES)
        if isinstance(objects, list) and len(objects) == 1 and isinstance(objects[0], list):
            objects = objects[0]
        
        prompt = create_prompt(resoning_response, RAGRequest.user_input)
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

        return RAGResponse(
            answer=response,
            chunks = {
                "chunks": [
                    {
                        "chunk_id": str(idx),
                        "text": c.get("text", ""),
                        "meta": {
                            "metadata": c.get("metadata")
                        },
                    }
                    for idx, c in enumerate(objects)
                    if isinstance(c, dict)
                ]
            }

        )


