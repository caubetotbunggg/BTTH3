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
async def retrieve_legal_documents(query: str):
    """
    🔍 Truy xuất tài liệu pháp luật từ cơ sở dữ liệu Weaviate.

    Mục đích:
    - Tìm các văn bản luật liên quan đến câu hỏi đầu vào.
    - Trước khi truy vấn, hãy chuyển câu hỏi người dùng từ ngôn ngữ đời thường sang **ngôn ngữ pháp luật**.
      Ví dụ:
        • "nhân viên không tắt đèn" → "người lao động vi phạm nội quy lao động"
        • "bị phạt đi làm muộn" → "xử lý kỷ luật người lao động vi phạm giờ làm việc"
        • "công ty xả rác bừa bãi" → "vi phạm hành chính trong lĩnh vực bảo vệ môi trường"
    - Sử dụng các cụm từ thường gặp trong văn bản pháp luật để tăng độ chính xác:
        “xử lý kỷ luật”, “người lao động”, “người sử dụng lao động”, “vi phạm nội quy lao động”,
        “theo quy định pháp luật”, “trách nhiệm pháp lý”.
    - Sau khi chuyển đổi, chỉ dùng **một câu truy vấn pháp lý duy nhất** (`query`) để tạo embedding và tìm kiếm trong Weaviate.
    
    Hướng dẫn cho reasoning model:
    1. Nhận dạng hành vi pháp lý từ câu hỏi đời thường.
    2. Khái quát hành vi thành dạng hợp pháp lý (tập trung vào nguyên tắc, quyền và nghĩa vụ).
    3. Sử dụng cụm từ pháp luật chuẩn.
    4. Trả về câu truy vấn pháp lý duy nhất để gửi vào embedding.

    Tham số:
    - `query`: Câu hỏi đã được chuyển đổi sang **ngôn ngữ pháp luật**, dùng để tạo embedding và tìm tài liệu.

    Ví dụ:
    - Input user question: "Liệu doanh nghiệp có quyền kỷ luật nhân viên không tắt thiết bị điện sau khi dùng không?"
    - Query pháp lý: "Quy định về quyền và trình tự xử lý kỷ luật người lao động vi phạm nội quy lao động theo Bộ luật Lao động 2019."
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
    "Đầy đủ các điều luật để kết luận pháp lý chính xác."
    "Một danh sách đơn giản các điều luật với format [Điều - Tên Luật - Năm] "
    "và nội dung trích xuất. KHÔNG có phân tích hay kết luận."
)
