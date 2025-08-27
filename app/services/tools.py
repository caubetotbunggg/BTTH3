from app.services.retrieve_service import RetrieveService
from app.models.retrieve_model import RetrieveResponse
from app.services.rag_service import create_prompt, _get_llm_response_with_timeout
import asyncio
from app.config.settings import setup_logger
import time
from functools import wraps

logger = setup_logger("tools", "../BTTH3/log/tools_info.log")

def measure_time(step_name: str):
    def decorator(func):
        @wraps(func)
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
                    f"[agent] step={kwargs.get('step', '?')} "
                    f"name={step_name} duration={duration:.2f}s status={status}"
                )
        return wrapper
    return decorator


class Retrieve_tool:
    @staticmethod
    @measure_time("retrieve_laws")
    def retrieve_laws(user_input: str, k: int) -> RetrieveResponse | None:
        try:
            return RetrieveService.retrieve(user_input, k)
        
        except Exception as e:
            logger.error(f"Error occurred while retrieving laws: {e}")
            return None


class Generate_answer_tool:
    @staticmethod
    @measure_time("generate_answer")
    def generate_answer(user_input: str, chunks: RetrieveResponse | None) -> str:
        try:
            if not chunks:
                prompt = f"Không có điều luật phù hợp với câu hỏi {user_input}"
            else:
                prompt = create_prompt(chunks["chunks"], user_input)
            response = asyncio.run(_get_llm_response_with_timeout(prompt))
            return response
            
        except Exception as e:
            logger.error(f"Error occurred while generating answer: {e}")
            return None
        
class Format_citation:
    @staticmethod
    @measure_time("format_citation")
    def format_citation(answer: str, chunks: RetrieveResponse) -> str:
        try:
            citations = []
            for chunk in chunks["chunks"]:
                section = chunk.meta.get("section_title", "Không rõ")
                date = chunk.meta.get("date", "Không rõ")
                text = chunk.text
                citation = f"- {section} - {date} \n"
                citation += f"{text} \n"
                citations.append(citation)
            formatted = answer + "\n\n" + "Các luật được trích dẫn: " + "\n" + "\n".join(citations)
            return formatted

        except Exception as e:
            logger.error(f"Error occurred while formatting citation: {e}")
            return None