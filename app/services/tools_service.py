from app.models.tools_model import Format_Response_tool, RAG_Request_tool, RAG_Response_tool, RetrieveResponse, RetrieveRequest
from app.services.retrieve_service import RetrieveService
from app.services.rag_service import create_prompt, _get_llm_response_with_timeout
import asyncio
from app.config.settings import setup_logger
import time
from functools import wraps

logger = setup_logger("tools", "../BTTH3/log/tools_info.log")

def measure_time(step_name: str):
    def step_list(step: str):
        if step == "retrieve_laws":
            return 1
        elif step == "generate_answer":
            return 2
        elif step == "format_citation":
            return 3
        return 0

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
                    f"[agent] step={step_list(step_name)} "
                    f"name={step_name} duration={duration:.2f}s status={status}"
                )
        return wrapper
    return decorator


class Retrieve_tool:
    @staticmethod
    @measure_time("retrieve_laws")
    def retrieve_laws(request: RetrieveRequest, step: int = 1) -> RetrieveResponse | None:
        try:
            return RetrieveService.retrieve(request)
        except Exception as e:
            logger.error(f"Error occurred while retrieving laws: {e}")
            return RetrieveResponse(chunks=[])


class Generate_answer_tool:
    @staticmethod
    @measure_time("generate_answer")
    def generate_answer(rag_request: RAG_Request_tool) -> RAG_Response_tool:
        try:
            # Handle the case where chunks is None or empty
            if not rag_request.chunks or not rag_request.chunks.chunks:
                prompt = f"Không có điều luật phù hợp với câu hỏi {rag_request.user_input}"
            else:
                # Pass the chunks list directly to create_prompt
                prompt = create_prompt(
                    rag_request.chunks.chunks,  # Access the chunks list from RetrieveResponse
                    rag_request.user_input
                )

            response = asyncio.run(_get_llm_response_with_timeout(prompt))
            return RAG_Response_tool(answer=response, chunks=rag_request.chunks)
            
        except Exception as e:
            logger.error(f"Error occurred while generating answer: {e}")
            return RAG_Response_tool(answer="Có lỗi xảy ra khi tạo câu trả lời", chunks=None)
        

class Format_citation:
    @staticmethod
    @measure_time("format_citation")
    def format_citation(rag_response: RAG_Response_tool) -> Format_Response_tool:
        if not rag_response.chunks or not rag_response.chunks.chunks:
            formatted = rag_response.answer + "\n\n" + "Không có luật nào được trích dẫn!"
            return Format_Response_tool(formatted_answer=formatted)
        else:
            try:
                citations = []
                # Access chunks from the RetrieveResponse object
                for chunk in rag_response.chunks.chunks:
                    section = chunk.meta.get("section_title", "Không rõ")
                    date = chunk.meta.get("date", "Không rõ")
                    text = chunk.text
                    citation = f"- {section} - {date}\n"
                    citation += f"{text}\n"
                    citations.append(citation)
                
                formatted = rag_response.answer + "\n\n" + "Các luật được trích dẫn:\n\n" + "\n".join(citations)
                return Format_Response_tool(formatted_answer=formatted)

            except Exception as e:
                logger.error(f"Error occurred while formatting citation: {e}")
                return Format_Response_tool(formatted_answer=rag_response.answer + "\n\nLỗi khi định dạng trích dẫn")