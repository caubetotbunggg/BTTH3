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
        raise FileNotFoundError(f"Prompt '{name}' not found at {path}")
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
        # Normalize response: handle several possible SDK return shapes
        # If the SDK returns a string (already an error/short message), pass it through
        if isinstance(response, str):
            return response

        # If the response contains a `choices` list, try to extract a message
        if hasattr(response, "choices"):
            try:
                if len(response.choices) == 0:
                    logger.error("LLM returned empty choices list")
                    return "Đã xảy ra lỗi khi xử lý yêu cầu. Vui lòng thử lại."

                choice = response.choices[0]
                # Newer SDKs may put text under `message.content` or under `text`
                if hasattr(choice, "message") and hasattr(choice.message, "content"):
                    return choice.message.content
                if hasattr(choice, "text"):
                    return choice.text

                # Fallback: stringify
                return str(choice)
            except Exception as e:
                logger.error(f"Unexpected LLM response structure: {e}", exc_info=True)
                return "Đã xảy ra lỗi khi xử lý yêu cầu. Vui lòng thử lại."

        # Fallback for unknown response types
        return str(response)

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
            print("\n=== TREE 1: Semantic + Hybrid search ===")
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

            # Validate and normalize objects_tree1
            if objects_tree1 is None:
                logger.warning("tree1 returned None for objects")
                return RAGResponse(answer="No results from retrieval.", chunks={"chunks": []})

            if isinstance(objects_tree1, list) and len(objects_tree1) == 1 and isinstance(objects_tree1[0], list):
                objects_tree1 = objects_tree1[0]

            if not isinstance(objects_tree1, list) or len(objects_tree1) == 0:
                logger.warning(f"tree1 returned unexpected objects: {type(objects_tree1)} -> {objects_tree1}")
                return RAGResponse(answer="No relevant documents found.", chunks={"chunks": []})

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
