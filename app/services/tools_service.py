import asyncio
import time
from functools import wraps

from app.config.settings import setup_logger
from app.models.retrieve_model import RetrieveResponse
from app.models.tools_model import (
    Format_citation_tool_request,
    Format_citation_tool_response,
    Generate_answer_tool_request,
    Generate_answer_tool_response,
    Retrieve_tool_request,
    Retrieve_tool_response,
)
from app.services.rag_service import _get_llm_response_with_timeout, create_prompt
from app.services.retrieve_service import RetrieveService

logger = setup_logger("tools", "../log/tools_info.log")


def measure_time(step_name: str):
    def decorator(func):
        @wraps(func)
        def step_num(name: str):
            if name == "retrieve_laws":
                return 1
            elif name == "generate_answer":
                return 2
            elif name == "format_citation":
                return 3
            else:
                return "?"

        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            status = "ok"
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                raise e
            finally:
                duration = time.perf_counter() - start
                logger.info(
                    f"[agent] step={step_num(step_name)} "
                    f"name={step_name} duration={duration:.2f}s status={status}"
                )

        return wrapper

    return decorator


class Retrieve_tool:
    @staticmethod
    @measure_time("retrieve_laws")
    def retrieve_laws(req: Retrieve_tool_request) -> RetrieveResponse | None:
        try:
            response = RetrieveService.retrieve(req.user_input, req.k)
            return Retrieve_tool_response(chunks=response)

        except Exception as e:
            logger.error(f"Error occurred while retrieving laws: {e}")
            return None


class Generate_answer_tool:
    @staticmethod
    @measure_time("generate_answer")
    def generate_answer(req: Generate_answer_tool_request) -> str:
        try:
            if not req.chunks:
                prompt = f"Không có điều luật phù hợp với câu hỏi {req.user_input}"
            else:
                prompt = create_prompt(req.chunks.chunks, req.user_input)
            response = asyncio.run(_get_llm_response_with_timeout(prompt))
            return Generate_answer_tool_response(answer=response)

        except Exception as e:
            logger.error(f"Error occurred while generating answer: {e}")
            return None


class Format_citation:
    @staticmethod
    @measure_time("format_citation")
    def format_citation(req: Format_citation_tool_request) -> str:
        try:
            citations = []
            for chunk in req.chunks.chunks:
                section = chunk.meta.get("section_title", "Không rõ")
                date = chunk.meta.get("date", "Không rõ")
                text = chunk.text
                citation = f"- {section} - {date} \n"
                citation += f"{text} \n"
                citations.append(citation)
            formatted = (
                req.answer
                + "\n\n"
                + "Các luật được trích dẫn: "
                + "\n"
                + "\n".join(citations)
            )
            return Format_citation_tool_response(formatted_answer=formatted)

        except Exception as e:
            logger.error(f"Error occurred while formatting citation: {e}")
            return None
