import httpx
from app.config.settings import GEMINI_CLIENT, RAG_CONFIG, WEAVIATE_CLIENT


class HealthService:
    @staticmethod
    def check_database() -> bool:
        try:
            return WEAVIATE_CLIENT.is_ready()
        except Exception as e:
            return False

    @staticmethod
    def check_llm() -> bool:
        try:
            GEMINI_CLIENT.models.generate_content(
                    model=RAG_CONFIG["MODEL_NAME"],
                    contents="hello",
                )
            return True
        except Exception:
            return False

    @staticmethod
    def check_baseurl() -> bool:
        try:
            resp = httpx.get("http://localhost:8000/", timeout=2.0)
            return resp.status_code == 200
        except Exception:
            return False

    @staticmethod
    def health_status() -> dict:
        return {
            "database": HealthService.check_database(),
            "llm_api": HealthService.check_llm(),
            "baseurl": HealthService.check_baseurl(),
        }
