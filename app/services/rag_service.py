import asyncio
import time
from pathlib import Path

from app.config.settings import GROQ_CLIENT_B, setup_logger, LLM_MODEL
from app.config.tree_config import tree1
from app.models.rag_model import RAGResponse, RAGRequest

logger = setup_logger("rag", "../log/rag_info.log")

PROMPT_DIR = Path(__file__).parent.parent / "prompts"


def load_prompt(name: str) -> str:
    path = PROMPT_DIR / f"{name}.txt"
    if not path.exists():
        raise FileNotFoundError(f"Prompt '{name}' không tồn tại tại {path}")
    return path.read_text(encoding="utf-8")


def format_prompt(template: str, **kwargs) -> str:
    return template.format(**kwargs)


def create_prompt(reasoning_response_tree1: str, question: str) -> str:
    template = load_prompt("llm_prompt")
    return format_prompt(
        template,
        reasoning_response_tree1=reasoning_response_tree1,
        question=question,
    )


def build_reasoning_prompt_tree1(user_question: str) -> str:
    template = load_prompt("tree_prompt")
    return format_prompt(template, user_question=user_question)


async def _get_llm_response_with_timeout(prompt: str, timeout: int = 60) -> str:
    loop = asyncio.get_event_loop()
    try:
        response = await asyncio.wait_for(
            loop.run_in_executor(
                None,
                lambda: GROQ_CLIENT_B.chat.completions.create(
                    messages=[{"role": "assistant", "content": prompt}],
                    model=LLM_MODEL,
                    temperature=0.0,
                ),
            ),
            timeout=timeout,
        )
        return response.choices[0].message.content

    except asyncio.TimeoutError:
        logger.error("LLM request timeout")
        return "Hệ thống đang bận, vui lòng thử lại sau."
    except Exception as e:
        logger.error(f"Error in _get_llm_response_with_timeout: {str(e)}")
        return "Đã xảy ra lỗi khi xử lý yêu cầu. Vui lòng thử lại."


class RAGService:
    @staticmethod
    def rag_pipeline(rag_request: RAGRequest) -> RAGResponse:
        try:
            start_total = time.perf_counter()

            print("\n=== TREE 1: Tìm kiếm Semantic + Hybrid ===")
            tree1_start = time.perf_counter()
            reasoning_response_tree1, objects_tree1 = tree1(
                build_reasoning_prompt_tree1(rag_request.user_input)
            )
            tree1_time = time.perf_counter() - tree1_start
            print(f"Tree 1 execution time: {tree1_time:.2f} seconds\n")

            print("=== Gộp kết quả và sinh câu trả lời cuối cùng ===")
            llm_start = time.perf_counter()
            prompt = create_prompt(reasoning_response_tree1, rag_request.user_input)
            response = asyncio.run(_get_llm_response_with_timeout(prompt))
            llm_time = time.perf_counter() - llm_start
            print(f"Final LLM response time: {llm_time:.2f} seconds")

            # Flatten nested list if needed
            if (
                isinstance(objects_tree1, list)
                and len(objects_tree1) == 1
                and isinstance(objects_tree1[0], list)
            ):
                objects_tree1 = objects_tree1[0]

            total_time = time.perf_counter() - start_total
            print(f"\nTổng thời gian: {total_time:.2f}s")
            logger.info(
                f"total={total_time:.2f}, tree1={tree1_time:.2f}, llm={llm_time:.2f}"
            )

            chunks_list = [
                {
                    "chunk_id": str(idx),
                    "text": c.get("text", ""),
                    "meta": {"metadata": c.get("metadata")},
                }
                for idx, c in enumerate(objects_tree1)
                if isinstance(c, dict)
            ]

            return RAGResponse(answer=response, chunks={"chunks": chunks_list})

        except Exception as e:
            error_msg = f"Lỗi trong RAG pipeline: {str(e)}"
            print(error_msg)
            logger.error(error_msg, exc_info=True)
            return RAGResponse(
                answer="Đã xảy ra lỗi nghiêm trọng trong hệ thống. Vui lòng thử lại sau.",
                chunks={"chunks": []},
            )
