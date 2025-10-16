import asyncio
import os
from dotenv import load_dotenv
import time
from weaviate.classes.query import MetadataQuery

from elysia import configure, tool
from elysia import Tree
from gradio_client import Client

from app.config.settings import (
    setup_logger, 
    GROQ_CLIENT, 
    GROQ_CLIENT_B,
    DOCUMENT_COLLECTION,
    SEARCH_CONFIG
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

        @tool
        async def retrieve_legal_documents(query: str):
            """
            Thực hiện tìm kiếm tài liệu pháp luật bằng phương pháp kết hợp embedding (semantic vector) và từ khóa (hybrid search).

            Mục đích:
            - Phát hiện các văn bản luật có ngữ nghĩa gần với câu hỏi đầu vào, kể cả khi không trùng từ khóa chính xác.
            - Thường phù hợp với câu hỏi thực tế, tình huống cụ thể.

            Giới hạn:
            - Do dùng embedding, kết quả có thể **bỏ sót các định nghĩa, điều luật cụ thể, hoặc thuật ngữ pháp lý chính xác**.
            - Vì vậy, công cụ này **nên được kết hợp với truy vấn từ khóa chính xác (full-text query)** bằng `query_legal_documents`, đặc biệt với các câu hỏi mang tính định nghĩa, khái niệm, hoặc yêu cầu chính xác tuyệt đối theo từ ngữ của luật.

            Gợi ý:
            - Nếu kết quả từ tool này chưa rõ ràng hoặc chưa đủ độ chính xác, hãy sử dụng thêm `query_legal_documents` để kiểm tra theo từ khóa gốc hoặc các paraphrase liên quan.

            Tham số:
            - `query`: Câu hỏi pháp lý cần tìm trong cơ sở dữ liệu.
            """

            # --- Step 1: Gọi Gradio để lấy embedding ---
            try:
                # Fix lỗi 'PATH' nếu biến môi trường này không tồn tại (xảy ra trong một số môi trường IDE/macOS)
                if "PATH" not in os.environ:
                    os.environ["PATH"] = "/usr/bin:/bin:/usr/sbin:/sbin:/usr/local/bin"

                client = Client("caubetotbunggg/api_2")  # dùng URL chuẩn

                # dùng run_in_executor để tránh lỗi async/sync conflict
                import asyncio
                loop = asyncio.get_event_loop()
                embedding = await loop.run_in_executor(
                    None,
                    lambda: client.predict(
                        text=f"query: {query}",
                        api_name="/embed_text"
                    )
                )

            except Exception as e:
                return f"Lỗi khi tạo embedding từ Gradio: {e}"

            # --- Step 2: Truy vấn hybrid đến Weaviate ---
            try:

                results = DOCUMENT_COLLECTION.query.hybrid(
                    query=query,
                    vector=embedding,
                    alpha=SEARCH_CONFIG["ALPHA"],
                    return_metadata=MetadataQuery(score=True, explain_score=True),
                    limit=5,
                )

                chunks = results.objects
            except Exception as e:
                return f"Lỗi khi truy vấn dữ liệu từ Weaviate: {e}"

            # --- Step 3: Xử lý kết quả ---
            if not chunks:
                return f"Không tìm thấy tài liệu nào phù hợp với truy vấn: '{query}'"
            
            return chunks


        configure(
            base_model="gemini-2.5-flash",
            base_provider="gemini",
            complex_model="gemini-2.5-flash",
            complex_provider="gemini",
            gemini_api_key=GEMINI_API_KEY# replace with your API key
        )

        configure(
            wcd_url= WEAVIATE_URL, # replace with your WCD_URL
            wcd_api_key= WEAVIATE_API_KEY, # replace with your WCD_API_KEY
        )

        tree = Tree()
        tree.add_tool(retrieve_legal_documents)
        tree.change_agent_description("""
        Bạn là một trợ lý pháp lý chuyên nghiệp. Luôn thực hiện đầy đủ các bước sau trước khi trả lời.

        QUY TRÌNH 4 BƯỚC:

        B1. Luôn sử dụng tool `retrieve_legal_documents` để thực hiện tìm kiếm kết hợp từ khóa và embedding (hybrid search).
        B2. Thực hiện nhiều truy vấn 'weaviate_query' biến thể (paraphrase) dưới dạng các câu hỏi khác nhau hoặc các cách diễn đạt khác nhau để truy vấn keyword (full-text) trong cơ sở dữ liệu, ví dụ qua `query` hoặc `bm25`. Việc này rất quan trọng để đảm bảo tìm được các văn bản luật mới nhất, sát nhất với nội dung câu hỏi, đặc biệt khi câu hỏi có thể đa nghĩa hoặc có nhiều cách diễn đạt.
        B3. Tổng hợp thông tin từ cả hai bước tìm kiếm trên, so sánh và đối chiếu để chọn lọc dữ liệu phù hợp, đầy đủ và MỚI NHẤT. Khi tổng hợp nội dung, bắt buộc phải GIỮ NGUYÊN thông tin về ĐIỀU – TÊN LUẬT – NĂM BAN HÀNH (lấy từ metadata của chunks) của mỗi đoạn trích dẫn pháp luật. Tuyệt đối không được lược bỏ hoặc rút gọn các thông tin trích dẫn này.
        B4. Nếu tìm thấy dữ liệu, lập luận và trả lời dựa trên đó, trích dẫn rõ ràng ĐIỀU - LUẬT ví dụ: "Điều 37 Bộ luật Lao động 2019". Nếu không, hãy trả lời rằng "không có dữ liệu phù hợp trong tài liệu pháp luật".

        KHÔNG được trả lời từ kiến thức bên ngoài nếu có dữ liệu pháp luật.

        LUÔN trả lời bằng tiếng Việt, ngắn gọn, rõ ràng, và nếu có thể hãy trích ĐIỀU LUẬT RÕ RÀNG.
        """)

        tree.change_style("""
        - Luôn bắt đầu câu trả lời bằng kết luận rõ ràng, ngắn gọn và súc tích.
        - Mọi câu trả lời **phải dựa trên tài liệu đã truy xuất** từ cơ sở dữ liệu pháp luật.
        - Khi sử dụng thông tin từ tài liệu, hãy **trích dẫn nguyên văn đoạn liên quan** kèm theo ĐIỀU LUẬT và **năm ban hành** nếu có, ví dụ "Điều 37 Bộ luật Lao động 2019".
        - Trong trường hợp có nhiều tài liệu khác nhau, ưu tiên trích dẫn và dựa trên văn bản pháp luật mới nhất.
        - Không bao giờ trả lời dựa trên suy đoán hoặc kiến thức ngoài nếu có tài liệu pháp luật hỗ trợ.
        - Nếu không tìm thấy tài liệu liên quan, cần nói rõ rằng: "Không tìm thấy nội dung phù hợp trong cơ sở dữ liệu pháp luật."
        - Trả lời **bằng tiếng Việt** và sử dụng giọng điệu **chuyên nghiệp, trung lập và thân thiện**.
        """)
        
        QUES = RAGRequest.user_input
        resoning_response, objects = tree(QUES)

        if isinstance(objects, list) and len(objects) == 1 and isinstance(objects[0], list):
            objects = objects[0]
        print(resoning_response)
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


