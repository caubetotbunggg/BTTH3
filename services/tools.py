import asyncio
import logging
import time

import chromadb
from dotenv import load_dotenv
from fastapi import HTTPException
from google import genai
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer

# Cấu hình logging
logging.basicConfig(
    filename="../BTTH3/log/agent_tools.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8",
)
logger = logging.getLogger(__name__)


# -------------------------------- RETRIEVE MODULE --------------------------------#


# Input schema
class SearchInput(BaseModel):
    user_input: str
    k: int = 5


# Response schema
class ChunkResponse(BaseModel):
    chunk_id: str
    text: str
    score: float
    meta: dict


class SearchResponse(BaseModel):
    chunks: list[ChunkResponse]


# Retrieve function
def retrieve_laws(input: SearchInput) -> SearchResponse:
    # Load embedding model
    model = SentenceTransformer("intfloat/e5-small-v2")

    # Initialize ChromaDB client and collection
    client = chromadb.PersistentClient(path="chroma_db")
    collection = client.get_or_create_collection("legal_chunks")

    logger.info(f"Received query: question='{input.user_input}' top_k= {input.k}")

    # Embed truy vấn
    embedding = model.encode(f"query: {input.user_input}").tolist()

    try:
        # Truy vấn ChromaDB (top k)
        results = collection.query(
            query_embeddings=[embedding],
            n_results=input.k,
            include=["documents", "distances", "metadatas"],
        )

        response_chunks = []
        documents = results["documents"][0]
        distances = results["distances"][0]
        metadatas = results["metadatas"][0]

        for doc, dist, meta in zip(documents, distances, metadatas):
            if dist > 0.5:
                continue  # Skip low similarity results
            response_chunks.append(
                ChunkResponse(
                    chunk_id=meta.get("law_id", ""),
                    text=doc,
                    score=float(dist),
                    meta=meta,
                )
            )

        if not response_chunks:
            raise HTTPException(
                status_code=500, detail="Vector search failed: 200: No results found"
            )

        return SearchResponse(chunks=response_chunks)

    except Exception as e:
        logger.error(f"Error during search: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Vector search failed: {str(e)}")


# -------------------------------- GENERATE ANSWER --------------------------------#


# Input schema
class GenerateInput(BaseModel):
    user_input: str
    chunks: list[ChunkResponse]


# Response schema
class GenerateResponse(BaseModel):
    answer: str


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


# Generate answer function
def generate_answer(input: GenerateInput) -> GenerateResponse:
    if not input.user_input.strip():
        raise HTTPException(status_code=400, detail="Câu hỏi không được để trống")
    start_total = time.perf_counter()
    try:
        # Tạo prompt từ các chunk
        start_prompt = time.perf_counter()
        prompt = create_prompt(input.chunks, input.user_input)
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
        logger.info(
            f"prompt_time={prompt_time:.2f},"
            f"llm_time={llm_time:.2f},total={total_time:.2f}"
        )
        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -------------------------------- FORMAT CITATIONS --------------------------------#


# Input schema
class FormatCitationsInput(BaseModel):
    answer: str
    chunks: list[ChunkResponse]


# Response schema
class FormatCitationsResponse(BaseModel):
    formatted_answer: str


def format_citations(input: FormatCitationsInput) -> FormatCitationsResponse:
    if not input.answer.strip():
        raise HTTPException(status_code=400, detail="Không có câu trả lời để định dạng")

    formatted_answer = input.answer
    for chunk in input.chunks:
        section_title = chunk.meta.get("section_title", "Không rõ")
        law_id = chunk.meta.get("law_id", "Không rõ")
        formatted_answer += f"\n\n[Trích dẫn: {section_title} - {law_id}]"

    return FormatCitationsResponse(formatted_answer=formatted_answer)
