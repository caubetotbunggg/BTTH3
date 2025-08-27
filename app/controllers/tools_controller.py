from fastapi import APIRouter
from contextlib import contextmanager
from app.services.tools import Retrieve_tool, Generate_answer_tool, Format_citation
import concurrent.futures

router = APIRouter()

# Context manager timeout
@contextmanager
def timeout(seconds: int):
    def run_with_timeout(func, *args, **kwargs):
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(func, *args, **kwargs)
            return future.result(timeout=seconds)
    yield run_with_timeout


@router.post("/agent")
def agent_endpoint(user_input: str, k: int, max_steps: int = 3, timeout_sec: int = 10):

    steps = [
        lambda prev: {"laws": Retrieve_tool.retrieve_laws(user_input, k)},
        lambda prev: {"answer": Generate_answer_tool.generate_answer(user_input, prev["laws"]), 
                      "laws": prev["laws"]},
        lambda prev: {"formatted": Format_citation.format_citation(prev["answer"], prev["laws"]), 
                      "laws": prev["laws"], "answer": prev["answer"]}
    ]

    result = {}
    executed_steps = []
    
    try:
        with timeout(timeout_sec) as run_with_timeout:
            for idx, step in enumerate(steps[:max_steps]):
                try:
                    # chạy step với timeout
                    result = run_with_timeout(step, result)
                    executed_steps.append({"step": idx + 1, "result": list(result.keys())})
                except concurrent.futures.TimeoutError:
                    return {"error": f"Step {idx+1} timed out after {timeout_sec}s"}
                except Exception as e:
                    return {"error": f"Step {idx+1} failed: {e}"}

    except Exception as e:
        return {"error": str(e)}

    return {
        "status": "ok",
        "steps_executed": executed_steps,
        "laws": result.get("laws"),
        "answer": result.get("answer"),
        "formatted": result.get("formatted"),
    }
