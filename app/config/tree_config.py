from typing import List
import asyncio
import os
from dotenv import load_dotenv
from weaviate.classes.query import MetadataQuery

from elysia import configure, tool, Tree
from gradio_client import Client

from app.config.settings import (
    setup_logger,
    DOCUMENT_COLLECTION,
    SEARCH_CONFIG,
    BASE_MODEL,
    COMPLEX_MODEL,
    WEAVIATE_URL,
    WEAVIATE_API_KEY,
    GEMINI_API_KEY,
)

load_dotenv()

logger = setup_logger("rag", "../log/rag_info.log")


@tool
async def retrieve_legal_documents(
    user_question: str,
    paraphrased_questions: List[str] = [],
    query: str = "",
):
    """
    🔍 Truy xuất tài liệu pháp luật từ cơ sở dữ liệu Weaviate.

    Mục đích:
    - Tìm các văn bản luật liên quan đến câu hỏi đầu vào.
    - Hỗ trợ tìm kiếm cả khi câu hỏi được diễn đạt lại bằng nhiều cách (paraphrases).

    Hướng dẫn cho reasoning model:
    - Nếu có nhiều câu paraphrased trong `paraphrased_questions`, hãy đánh giá mức độ
      tương đồng ngữ nghĩa giữa từng câu và `user_question`.
    - Chọn những câu paraphrased thể hiện rõ nhất ý định pháp lý của người dùng
      để thực hiện truy vấn embedding.
    - `query` là câu cuối cùng được chọn để gửi đến module embedding.

    Tham số:
    - `user_question`: Câu hỏi gốc người dùng nhập.
    - `paraphrased_questions`: Danh sách các cách diễn đạt lại cùng một ý
      (có thể rỗng hoặc chứa nhiều phần tử).
    - `query`: Câu dùng để tạo embedding cuối cùng (thường là câu paraphrase tốt nhất hoặc câu gốc).
    """
    try:
        if "PATH" not in os.environ:
            os.environ["PATH"] = "/usr/bin:/bin:/usr/sbin:/sbin:/usr/local/bin"

        client = Client("caubetotbunggg/api_2")
        loop = asyncio.get_event_loop()
        embedding = await loop.run_in_executor(
            None, lambda: client.predict(text=f"query: {query}", api_name="/embed_text")
        )

    except Exception as e:
        logger.error(f"Error creating embedding: {e}")
        return f"Lỗi khi tạo embedding từ Gradio: {e}"

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
        logger.error(f"Error querying Weaviate: {e}")
        return f"Lỗi khi truy vấn dữ liệu từ Weaviate: {e}"

    if not chunks:
        return f"Không tìm thấy tài liệu nào phù hợp với truy vấn: '{query}'"

    print(
        f"  - retrieve_legal_documents: Tìm thấy {len(chunks)} chunks "
        f"cho truy vấn '{query}'"
    )
    logger.info(f"Retrieved {len(chunks)} chunks for query: {query}")
    return chunks


configure(
    base_model=BASE_MODEL,
    base_provider="gemini",
    complex_model=COMPLEX_MODEL,
    complex_provider="gemini",
    gemini_api_key=GEMINI_API_KEY,
    wcd_url=WEAVIATE_URL,
    wcd_api_key=WEAVIATE_API_KEY,
)

# ===== TREE 1: Semantic + Hybrid Search =====
tree1 = Tree()
tree1.add_tool(retrieve_legal_documents)
tree1.remove_tool('cited_summarize')
tree1.change_agent_description(
    """
Bạn là một **trích xuất viên dữ liệu pháp luật** (Legal Data Extractor).

**VAI TRÒ:** Tìm kiếm và trích xuất thông tin từ cơ sở dữ liệu, KHÔNG phân tích hay tư vấn.

**NHIỆM VỤ DUY NHẤT:**
- Gọi công cụ để tìm tài liệu
- Trích xuất và liệt kê các điều luật theo đúng format
- KHÔNG thêm phân tích, giải thích, hay kết luận

**OUTPUT:** Chỉ là danh sách điều luật thuần túy.

Trả lời bằng tiếng Việt.
"""
)

tree1.change_style(
    """
**ĐỊNH DẠNG BẮT BUỘC:**

📌 Tìm thấy [X] văn bản pháp luật.

📚 Danh sách:

• **[Điều XX - Tên Luật - Năm]**: [Trích xuất nội dung]
• **[Điều YY - Tên Luật - Năm]**: [Trích xuất nội dung]

**CẤM TUYỆT ĐỐI:**
- Không viết "Theo quy định này..."
- Không viết "Điều này có nghĩa là..."
- Không thêm phân tích hay giải thích
- Không đưa ra kết luận

**CHỈ ĐƯỢC:**
- Liệt kê điều luật với metadata chính xác
- Trích xuất nội dung gốc từ tài liệu
"""
)

tree1.change_end_goal(
    "Một danh sách đơn giản các điều luật với format [Điều - Tên Luật - Năm] "
    "và nội dung trích xuất. KHÔNG có phân tích hay kết luận."
)
