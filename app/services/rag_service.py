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
    SEARCH_CONFIG,
    BASE_MODEL,
    COMPLEX_MODEL,
    WEAVIATE_URL,
    WEAVIATE_API_KEY,
    GEMINI_API_KEY,
)
from app.models.rag_model import RAGResponse, RAGRequest

load_dotenv()

logger = setup_logger("rag", "../log/rag_info.log")


def create_prompt(reasoning_response_tree1: str, reasoning_response_tree2: str, question: str) -> str:
    return f"""Bạn là một **trợ lý pháp lý chuyên nghiệp**.

Dưới đây là kết quả truy vấn và phân tích pháp luật đã được hệ thống tổng hợp:

**Nguồn 1 (Semantic + Hybrid):**
{reasoning_response_tree1}

**Nguồn 2 (Tìm kiếm bổ sung):**
{reasoning_response_tree2}

---

Hãy **Ưu tiên sử dụng điều luật mới hơn**, trả lời **ngắn gọn, súc tích**, theo **cấu trúc sau**:

---

**I. Căn cứ pháp lý:**  
- Nêu rõ Điều, Khoản, Điểm và tên văn bản luật điều chỉnh trực tiếp.(giữ nguyên định dạng [Điều xx - Tên Luật - Năm Ban Hành])
- Trình bày ngắn gọn nội dung chính của điều luật (1–2 câu/bullet).

**II. Áp dụng cho trường hợp cụ thể:**  
- Giải thích vắn tắt việc áp dụng điều luật vào tình huống trong câu hỏi.  
- Kết luận ngắn gọn, rõ ràng về đúng/sai, hợp pháp/trái luật.

**III. Nghĩa vụ hoặc quyền lợi phát sinh:**  
- Liệt kê nhanh các quyền, nghĩa vụ hoặc khoản bồi thường cụ thể nếu có.

**IV. Lưu ý cần kiểm tra thêm:**  
- Liệt kê các yếu tố thực tế cần xác minh thêm (ví dụ: loại HĐLĐ, thời gian điều trị, giấy xác nhận y tế, tính chất tai nạn,...).

---

🧭 **Yêu cầu quan trọng:**  
- Không lặp lại toàn bộ nội dung reasoning_response.  
- Không tóm tắt lan man.  
- Giữ độ dài **tối đa khoảng 5–10 dòng** như ví dụ mẫu sau:

---

**Ví dụ mẫu:**

Căn cứ Điều 37 Bộ luật Lao động 2019, người sử dụng lao động **không được đơn phương chấm dứt HĐLĐ** khi người lao động bị ốm đau, tai nạn đang điều trị, trừ khi đã điều trị 06 tháng liên tục (HĐLĐ xác định thời hạn) hoặc quá nửa thời hạn hợp đồng (HĐLĐ <12 tháng).  

Theo Điều 41, nếu chấm dứt trái pháp luật, công ty phải:
- Nhận người lao động trở lại làm việc;  
- Trả tiền lương, bảo hiểm xã hội, y tế trong thời gian không làm việc;  
- Trả thêm ít nhất 02 tháng tiền lương theo hợp đồng.  

**Lưu ý cần kiểm tra thêm:** thời gian điều trị thực tế, loại hợp đồng lao động, và có giấy chứng nhận y tế hợp lệ.

---

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
                    temperature=0.0,
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
        try:
            start_total = time.perf_counter()

            # @tool
            # async def retrieve_legal_documents(user_question: str, paraphrased_question: str = "", query: str = ""):
            #     start_retrieve = time.perf_counter()

            #     """
            #     Thực hiện tìm kiếm tài liệu pháp luật bằng phương pháp kết hợp embedding (semantic vector) và từ khóa (hybrid search).

            #     Mục đích:
            #     - Phát hiện các văn bản luật có ngữ nghĩa gần với câu hỏi đầu vào, kể cả khi không trùng từ khóa chính xác.
            #     - Thường phù hợp với câu hỏi thực tế, tình huống cụ thể.

            #     Tham số:
            #     - `query`: Câu hỏi pháp lý cần tìm trong cơ sở dữ liệu.
            #     """

            #     try:
            #         if "PATH" not in os.environ:
            #             os.environ["PATH"] = "/usr/bin:/bin:/usr/sbin:/sbin:/usr/local/bin"

            #         client = Client("caubetotbunggg/api_2")

            #         loop = asyncio.get_event_loop()
            #         embedding = await loop.run_in_executor(
            #             None,
            #             lambda: client.predict(
            #                 text=f"query: {query}",
            #                 api_name="/embed_text"
            #             )
            #         )

            #     except Exception as e:
            #         return f"Lỗi khi tạo embedding từ Gradio: {e}"

            #     try:

            #         results = DOCUMENT_COLLECTION.query.hybrid(
            #             query=query,
            #             vector=embedding,
            #             alpha=SEARCH_CONFIG["ALPHA"],
            #             return_metadata=MetadataQuery(score=True, explain_score=True),
            #             limit=5,
            #         )

            #         chunks = results.objects
            #     except Exception as e:
            #         return f"Lỗi khi truy vấn dữ liệu từ Weaviate: {e}"

            #     if not chunks:
            #         return f"Không tìm thấy tài liệu nào phù hợp với truy vấn: '{query}'"
                
            #     print(f"  - retrieve_legal_documents: Tìm thấy {len(chunks)} chunks cho truy vấn '{query}'")
            #     print(f"    + Thời gian truy vấn: {time.perf_counter() - start_retrieve:.2f} giây")
            #     return chunks
            from typing import List

            @tool
            async def retrieve_legal_documents(
                user_question: str,
                paraphrased_questions: List[str] = [],
            ):
                """
                🔍 Truy xuất tài liệu pháp luật từ cơ sở dữ liệu Weaviate.

                Mục đích:
                - Tìm kiếm các văn bản luật có nội dung gần nghĩa nhất với câu hỏi người dùng.
                - Hỗ trợ nhiều cách diễn đạt khác nhau của cùng một câu hỏi (paraphrases).

                Hướng dẫn cho reasoning model:
                - Nếu có nhiều câu trong `paraphrased_questions`, hãy hiểu rằng chúng là các biến thể diễn đạt lại cùng ý nghĩa với `user_question`.
                - Tool sẽ tự động tạo embedding cho tất cả các câu (gồm `user_question` và các paraphrase), sau đó gộp vector bằng phép trung bình để tăng độ bao phủ ngữ nghĩa.
                - Không cần chọn thủ công câu nào — toàn bộ paraphrases sẽ được dùng chung trong một embedding duy nhất.
                
                Tham số:
                - `user_question`: Câu hỏi gốc người dùng nhập.
                - `paraphrased_questions`: Danh sách các cách diễn đạt lại cùng ý (có thể rỗng hoặc chứa nhiều phần tử).
                """

                start_retrieve = time.perf_counter()

                try:
                    if "PATH" not in os.environ:
                        os.environ["PATH"] = "/usr/bin:/bin:/usr/sbin:/sbin:/usr/local/bin"

                    client = Client("caubetotbunggg/api_2")

                    # Combine all queries
                    all_queries = [user_question] + paraphrased_questions

                    loop = asyncio.get_event_loop()

                    # Embed all sentences asynchronously
                    embeddings = []
                    for q in all_queries:
                        emb = await loop.run_in_executor(
                            None,
                            lambda q=q: client.predict(text=f"query: {q}", api_name="/embed_text")
                        )
                        embeddings.append(np.array(emb))

                    # Average embedding
                    combined_embedding = np.mean(embeddings, axis=0)

                except Exception as e:
                    return f"Lỗi khi tạo embedding từ Gradio: {e}"

                try:
                    results = DOCUMENT_COLLECTION.query.hybrid(
                        query=user_question,  # vẫn dùng user_question để scoring lexical
                        vector=combined_embedding.tolist(),
                        alpha=SEARCH_CONFIG["ALPHA"],
                        return_metadata=MetadataQuery(score=True, explain_score=True),
                        limit=5,
                    )
                    chunks = results.objects

                except Exception as e:
                    return f"Lỗi khi truy vấn dữ liệu từ Weaviate: {e}"

                if not chunks:
                    return f"Không tìm thấy tài liệu nào phù hợp với truy vấn: '{user_question}'"

                print(f"  - retrieve_legal_documents: Tìm thấy {len(chunks)} chunks cho '{user_question}'")
                print(f"    + Thời gian truy vấn: {time.perf_counter() - start_retrieve:.2f} giây")
                return chunks

            # @tool
            # async def retrieve_legal_documents(
            #     user_question: str,
            #     paraphrased_questions: List[str] = [],
            #     query: str = "",
            # ):
            #     """
            #     🔍 Truy xuất tài liệu pháp luật từ cơ sở dữ liệu Weaviate.

            #     Mục đích:
            #     - Tìm các văn bản luật liên quan đến câu hỏi đầu vào.
            #     - Hỗ trợ tìm kiếm cả khi câu hỏi được diễn đạt lại bằng nhiều cách (paraphrases).
                
            #     Hướng dẫn cho reasoning model:
            #     - Nếu có nhiều câu paraphrased trong `paraphrased_questions`, hãy đánh giá mức độ tương đồng ngữ nghĩa giữa từng câu và `user_question`.
            #     - Chọn những câu paraphrased thể hiện rõ nhất ý định pháp lý của người dùng để thực hiện truy vấn embedding.
            #     - `query` là câu cuối cùng được chọn để gửi đến module embedding.
                
            #     Tham số:
            #     - `user_question`: Câu hỏi gốc người dùng nhập.
            #     - `paraphrased_questions`: Danh sách các cách diễn đạt lại cùng một ý (có thể rỗng hoặc chứa nhiều phần tử).
            #     - `query`: Câu dùng để tạo embedding cuối cùng (thường là câu paraphrase tốt nhất hoặc câu gốc).
            #     """
                
            #     start_retrieve = time.perf_counter()

            #     try:
            #         if "PATH" not in os.environ:
            #             os.environ["PATH"] = "/usr/bin:/bin:/usr/sbin:/sbin:/usr/local/bin"

            #         client = Client("caubetotbunggg/api_2")
            #         loop = asyncio.get_event_loop()
            #         embedding = await loop.run_in_executor(
            #             None,
            #             lambda: client.predict(text=f"query: {query}", api_name="/embed_text")
            #         )

            #     except Exception as e:
            #         return f"Lỗi khi tạo embedding từ Gradio: {e}"

            #     try:
            #         results = DOCUMENT_COLLECTION.query.hybrid(
            #             query=query,
            #             vector=embedding,
            #             alpha=SEARCH_CONFIG["ALPHA"],
            #             return_metadata=MetadataQuery(score=True, explain_score=True),
            #             limit=5,
            #         )
            #         chunks = results.objects
            #     except Exception as e:
            #         return f"Lỗi khi truy vấn dữ liệu từ Weaviate: {e}"

            #     if not chunks:
            #         return f"Không tìm thấy tài liệu nào phù hợp với truy vấn: '{query}'"
                
            #     print(f"  - retrieve_legal_documents: Tìm thấy {len(chunks)} chunks cho truy vấn '{query}'")
            #     print(f"    + Thời gian truy vấn: {time.perf_counter() - start_retrieve:.2f} giây")
            #     return chunks


            configure(
                base_model=BASE_MODEL,
                base_provider="gemini",
                complex_model=COMPLEX_MODEL,
                complex_provider="gemini",
                gemini_api_key=GEMINI_API_KEY,
                wcd_url=WEAVIATE_URL, 
                wcd_api_key=WEAVIATE_API_KEY, 
                temparature=0.2,
            )

            tree1 = Tree()
            tree1.add_tool(retrieve_legal_documents)
            tree1.change_agent_description("""
            Bạn là một chuyên viên pháp lý phân tích dữ liệu chuyên nghiệp. 
            Nhiệm vụ của bạn là **tìm kiếm và trích xuất các trích dẫn pháp luật chi tiết** liên quan đến câu hỏi được đưa ra, sử dụng công cụ truy vấn cơ sở dữ liệu tài liệu pháp luật.
            **KẾT QUẢ CUỐI CÙNG phải là danh sách CÁC **[Điều Luật] - [Tên Luật] - [Năm Ban Hành]**(giữ nguyên định dạng trong metadata) và **NỘI DUNG ĐÃ ĐƯỢC TÓM TẮT SÚC TÍCH** có cấu trúc và đầy đủ thông tin.**
            LUÔN trả lời bằng tiếng Việt.
            """)

            tree1.change_style("""
            - Bắt đầu câu trả lời bằng một tóm tắt ngắn (1-2 câu) về HƯỚNG PHÂN TÍCH hoặc các VĂN BẢN PHÁP LUẬT QUAN TRỌNG NHẤT được tìm thấy.
            - Phần nội dung chính **phải là danh sách các trích dẫn pháp luật chi tiết.** Mỗi trích dẫn phải bao gồm: **[Điều Luật] - [Tên Luật] - [Năm Ban Hành]**(giữ nguyên định dạng trong metadata) và **NỘI DUNG ĐÃ ĐƯỢC TÓM TẮT SÚC TÍCH**.
            - **Luôn ưu tiên** trích dẫn văn bản pháp luật **mới nhất, còn hiệu lực.**
            - Trả lời **bằng tiếng Việt.**
            """)

            tree1.change_end_goal("danh sách các trích dẫn pháp luật chi tiết.** Mỗi trích dẫn phải bao gồm: **[Điều Luật] - [Tên Luật] - [Năm Ban Hành]**(giữ nguyên định dạng trong metadata) và **NỘI DUNG ĐÃ ĐƯỢC TÓM TẮT SÚC TÍCH**.")

            print("\n=== TREE 1: Tìm kiếm Semantic + Hybrid ===")
            tree1_start = time.perf_counter()
            reasoning_response_tree1, objects_tree1 = tree1(RAGRequest.user_input)
            tree1_time = time.perf_counter() - tree1_start
            print(f"Tree 1 execution time: {tree1_time:.2f} seconds\n")
            
            tree2 = Tree()
            tree2.change_agent_description("""
            Bạn là một chuyên viên pháp lý phân tích dữ liệu chuyên nghiệp. 
            Nhiệm vụ của bạn là **tìm kiếm và trích xuất các trích dẫn pháp luật chi tiết** liên quan đến câu hỏi được đưa ra, sử dụng công cụ truy vấn cơ sở dữ liệu tài liệu pháp luật.
            **KẾT QUẢ CUỐI CÙNG phải là danh sách CÁC **[Điều Luật] - [Tên Luật] - [Năm Ban Hành]**(giữ nguyên định dạng trong metadata) và **NỘI DUNG ĐÃ ĐƯỢC TÓM TẮT SÚC TÍCH** có cấu trúc và đầy đủ thông tin.**
            LUÔN trả lời bằng tiếng Việt.
            """)

            tree2.change_style("""
            - Bắt đầu câu trả lời bằng một tóm tắt ngắn (1-2 câu) về HƯỚNG PHÂN TÍCH hoặc các VĂN BẢN PHÁP LUẬT QUAN TRỌNG NHẤT được tìm thấy.
            - Phần nội dung chính **phải là danh sách các trích dẫn pháp luật chi tiết.** Mỗi trích dẫn phải bao gồm: **[Điều Luật] - [Tên Luật] - [Năm Ban Hành]** và **NỘI DUNG ĐÃ ĐƯỢC TÓM TẮT SÚC TÍCH**.
            - **Luôn ưu tiên** trích dẫn văn bản pháp luật **mới nhất, còn hiệu lực.**
            - Trả lời **bằng tiếng Việt.**
            """)

            tree2.change_end_goal("danh sách các trích dẫn pháp luật chi tiết.** Mỗi trích dẫn phải bao gồm: **[Điều Luật] - [Tên Luật] - [Năm Ban Hành]**(giữ nguyên định dạng trong metadata) và **NỘI DUNG ĐÃ ĐƯỢC TÓM TẮT SÚC TÍCH**.")

            print("=== TREE 2: Tìm kiếm bổ sung (Phân tích bổ sung) ===")
            tree2_start = time.perf_counter()
            reasoning_response_tree2, _ = tree2(RAGRequest.user_input)
            tree2_time = time.perf_counter() - tree2_start
            print(f"Tree 2 execution time: {tree2_time:.2f} seconds\n")

            print("=== Gộp kết quả và sinh câu trả lời cuối cùng ===")
            llm_start = time.perf_counter()
            prompt = create_prompt(reasoning_response_tree1, reasoning_response_tree2, RAGRequest.user_input)
            response = asyncio.run(_get_llm_response_with_timeout(prompt))
            llm_time = time.perf_counter() - llm_start
            print(f"Final LLM response time: {llm_time:.2f} seconds")

            if isinstance(objects_tree1, list) and len(objects_tree1) == 1 and isinstance(objects_tree1[0], list):
                objects_tree1 = objects_tree1[0]

            total_time = time.perf_counter() - start_total
            print(f"\nTổng thời gian: {total_time:.2f}s")
            logger.info(f"total={total_time:.2f}, tree1={tree1_time:.2f}, tree2={tree2_time:.2f}, llm={llm_time:.2f}")

            return RAGResponse(
                answer=response,
                chunks={
                    "chunks": [
                        {
                            "chunk_id": str(idx),
                            "text": c.get("text", ""),
                            "meta": {
                                "metadata": c.get("metadata")
                            },
                        }
                        for idx, c in enumerate(objects_tree1)
                        if isinstance(c, dict)
                    ]
                }
            )
        except Exception as e:
            print(f"Lỗi trong RAG pipeline: {e}")
            logger.error(f"Lỗi trong RAG pipeline: {e}")
            raise e