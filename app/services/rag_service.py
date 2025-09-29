import asyncio
import os
from dotenv import load_dotenv
import time

from groq import Groq

from app.config.settings import (
    setup_logger, 
)
from app.models.rag_model import RAGResponse, RAGRequest
from app.services.retrieve_service import RetrieveService

load_dotenv()

logger = setup_logger("rag", "../log/rag_info.log")

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)
def paraphrase(question: str) -> str:
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
Kết quả:"""
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "assistant",
                "content": contents,
            }
        ],
        model="openai/gpt-oss-20b",
    )
    return chat_completion.choices[0].message.content

def keyword_extraction(question: str) -> str:
    contents=f"""
Bạn là một trợ lý pháp luật. 
Nhiệm vụ của bạn là đọc câu hỏi đời thường của người dùng và xác định khái niệm pháp lý trung tâm mà câu hỏi đó liên quan đến. 

Nguyên tắc:
- Chỉ trả lời bằng 1 hoặc vài khái niệm pháp lý ngắn gọn.  
- Không viết lại câu hỏi.  
- Không thêm ví dụ, số liệu, tình tiết cụ thể.  
- Luôn dùng thuật ngữ pháp lý chuẩn xác trong luật (ví dụ: "hình thức giao dịch dân sự", "hợp đồng vay tài sản", "nghĩa vụ quân sự", "hợp đồng lao động", "nghĩa vụ đóng bảo hiểm xã hội", "điều kiện có hiệu lực của giao dịch dân sự"...).

Ví dụ:
Người dùng: "Tôi vay bạn 200 triệu, có viết giấy vay tay. Giờ không trả, bạn tôi có thể kiện tôi ra tòa không?"
→ Kết quả: "hình thức giao dịch dân sự; hợp đồng vay tài sản; quyền khởi kiện"

Người dùng: "Nam giới phải đi nghĩa vụ khi nào?"
→ Kết quả: "nghĩa vụ quân sự; độ tuổi đăng ký"

Người dùng: "Ký hợp đồng thử việc 2 tháng thì công ty có phải đóng bảo hiểm xã hội không?"
→ Kết quả: "hợp đồng lao động; nghĩa vụ đóng bảo hiểm xã hội"

Người dùng: {question}
→ Kết quả:
"""
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "assistant",
                "content": contents,
            }
        ],
        model="openai/gpt-oss-20b",
    )
    return chat_completion.choices[0].message.content

def chunk_to_text(chunks: list) -> str:
    all_chunks = {}
    for chunk in chunks:
        # tạo key unique để loại trùng (dựa trên law_id + text)
        law_id = chunk.meta.get("law_id", "") if chunk.meta else ""
        key = f"{law_id}_{chunk.text}"
        all_chunks[key] = chunk   # dict override nếu gặp key trùng

    # kết quả unique
    unique_chunks = list(all_chunks.values())

    # build prompt text
    chunk_text = ""
    for chunk in unique_chunks:
        section = chunk.meta.get("section_title", "Không rõ") if chunk.meta else "Không rõ"
        chunk_text += f"- [{section}] {chunk.text}\n"

    return chunk_text

def create_prompt(chunk_text: str, question: str) -> str:
    return f"""Bạn là một trợ lý pháp lý chuyên nghiệp.  
Trước hết, hãy trả lời dựa trên các điều luật sau:  
{chunk_text}

Yêu cầu:  
- Trả lời chính xác, súc tích, sử dụng ngôn ngữ pháp lý chuẩn mực.  
- Mỗi kết luận phải kèm trích dẫn đầy đủ (Luật, Điều, Khoản, Điểm nếu có).  
- Nếu các điều luật chưa đủ để kết luận, hãy nêu rõ phần còn thiếu.  
- Trong trường hợp cần thiết, bạn có thể đưa ra “gợi ý tham khảo ngoài văn bản được cung cấp” nhưng phải phân biệt rõ với phần trích dẫn chính thức.  

Câu hỏi: {question}
"""


async def _get_llm_response_with_timeout(prompt: str, timeout: int = 60) -> str:
    loop = asyncio.get_event_loop()
    try:
        response = await asyncio.wait_for(
            loop.run_in_executor(
                None,
                lambda: client.chat.completions.create(
                        messages=[
                    {
                        "role": "assistant",
                        "content": prompt,
                    }
                ],
                model="openai/gpt-oss-20b",
                ),
            ),
            timeout=timeout,
        )
        return response.choices[0].message.content
    except asyncio.TimeoutError:
        return "Hệ thống đang bận, vui lòng thử lại sau."

async def run_parallel_llm(user_input: str):
    paraphrase_task = asyncio.to_thread(paraphrase, user_input)
    keyword_task = asyncio.to_thread(keyword_extraction, user_input)

    paraphrased, keywords = await asyncio.gather(paraphrase_task, keyword_task)
    return paraphrased, keywords

async def run_retrieve_all(keywords: list[str], paraphrased: str, k: int):
    tasks = [asyncio.to_thread(RetrieveService.retrieve, kw, k) for kw in keywords]
    tasks.append(asyncio.to_thread(RetrieveService.retrieve, paraphrased, k))

    results = await asyncio.gather(*tasks)
    return results



class RAGService:
    @staticmethod
    def rag_pipeline(RAGRequest: RAGRequest):
        start_total = time.perf_counter()

        # --- Step 1: retrieve ---
        start_retrieve = time.perf_counter()
        
        paraphrased, keywords = asyncio.run(run_parallel_llm(RAGRequest.user_input))
        print("Paraphrased:", paraphrased)
        print("Keywords:", keywords)
        
        keywords = [kw.strip() for kw in keywords.split(";") if kw.strip()]
        
        results = asyncio.run(run_retrieve_all(keywords, paraphrased, RAGRequest.k))

        all_chunks = []
        for res in results:
            if res and res.chunks:
                all_chunks.extend(res.chunks)

        chunks = chunk_to_text(all_chunks)
        retrieve_time = time.perf_counter() - start_retrieve

        # --- Step 2: prompt ---
        start_prompt = time.perf_counter()
        if not all_chunks:
            prompt = f"Không có điều luật phù hợp với câu hỏi {RAGRequest.user_input}"
            return RAGResponse(answer=prompt, chunks={"chunks": []})
        else:
            prompt = create_prompt(chunks, RAGRequest.user_input)
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

        return RAGResponse(
            answer=response,
            chunks={"chunks": [
                {
                    "chunk_id": str(idx),
                    "text": c.text,
                    "score": getattr(c, "score", None),
                    "meta": getattr(c, "meta", {})
                }
                for idx, c in enumerate(all_chunks)
            ]}
        )


