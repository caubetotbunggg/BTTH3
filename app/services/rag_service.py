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


async def _get_llm_response_with_timeout(prompt: str, timeout: int = 60, max_attempts: int = 3) -> str:
    """Call the LLM with a timeout and retry on transient failures.

    This function will attempt up to `max_attempts` times with exponential backoff
    between attempts. It defensively handles empty or missing `choices` lists and
    logs helpful debug information for triage.
    """
    loop = asyncio.get_event_loop()

    for attempt in range(1, max_attempts + 1):
        try:
            logger.debug(f"LLM attempt {attempt}/{max_attempts}")
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

            # Debug raw response shape for easier triage
            logger.debug(
                "Raw LLM response type: %s | choices: %s",
                type(response),
                getattr(response, "choices", None),
            )

            # If the SDK returns a string already (some wrappers do), pass it through
            if isinstance(response, str):
                return response

            # If the response contains a `choices` attribute, validate it
            if hasattr(response, "choices"):
                try:
                    if not response.choices:
                        logger.warning(
                            "LLM returned empty or None choices list on attempt %s", attempt
                        )
                        raise ValueError("empty_choices")

                    choice = response.choices[0]
                    # SDKs may put content under different attributes
                    if hasattr(choice, "message") and hasattr(choice.message, "content"):
                        return choice.message.content
                    if hasattr(choice, "text"):
                        return choice.text

                    # Fallback: stringify the choice object
                    return str(choice)

                except Exception as e:
                    logger.exception("Unexpected LLM response structure on attempt %s: %s", attempt, e)
                    # let outer exception handling decide whether to retry
                    raise

            # As a last resort, stringify unknown response objects
            return str(response)

        except asyncio.TimeoutError:
            logger.warning("LLM request timeout on attempt %s/%s", attempt, max_attempts)
            if attempt < max_attempts:
                backoff = 2 ** (attempt - 1)
                logger.debug("Retrying after %s seconds (timeout)", backoff)
                await asyncio.sleep(backoff)
                continue
            return "Hệ thống đang bận, vui lòng thử lại sau."

        except Exception as e:
            # For any other exception, log and retry up to max_attempts
            logger.warning("LLM call failed on attempt %s/%s: %s", attempt, max_attempts, e)
            if attempt < max_attempts:
                backoff = 2 ** (attempt - 1)
                logger.debug("Retrying after %s seconds (exception)", backoff)
                await asyncio.sleep(backoff)
                continue
            logger.error("LLM call failed after %s attempts: %s", max_attempts, e, exc_info=True)
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

            total_time = time.perf_counter() - start_total
            print(f"\nTổng thời gian: {total_time:.2f}s")
            logger.info(
                f"total={total_time:.2f}, tree1={tree1_time:.2f}, llm={llm_time:.2f}"
            )

            return RAGResponse(answer=response, reasoning=reasoning_response_tree1)

        except Exception as e:
            error_msg = f"Lỗi trong RAG pipeline: {str(e)}"
            print(error_msg)
            logger.error(error_msg, exc_info=True)
            return RAGResponse(
                answer="Đã xảy ra lỗi nghiêm trọng trong hệ thống. Vui lòng thử lại sau.",
                chunks={"chunks": []},
            )
