import httpx
from app.config.settings import GEMINI_CLIENT, RAG_CONFIG, WEAVIATE_CLIENT
from gradio_client import Client


class HealthService:
    @staticmethod
    def check_database() -> bool:
        try:
            return WEAVIATE_CLIENT.is_ready()
        except Exception as e:
            return False, str(e)

    @staticmethod
    def check_llm() -> bool:
        try:
            GEMINI_CLIENT.models.generate_content(
                    model=RAG_CONFIG["MODEL_NAME"],
                    contents="hello",
                )
            return True
        except Exception as e:
            return False, str(e)

    @staticmethod
    def check_baseurl() -> bool:
        try:
            resp = httpx.get("http://localhost:8000/", timeout=2.0)
            return resp.status_code == 200
        except Exception as e:
            return False, str(e)

    @staticmethod
    def check_reranker() -> bool:
        try:
            client = Client("caubetotbunggg/reranker")
            result = client.predict(
                    batch_pairs=[["AI là gì?","AI là trí tuệ nhân tạo."]],
                    api_name="/rerank"
            )
            if result:
                return True
        except Exception as e:
            return False, str(e)

    @staticmethod
    def check_embedder() -> bool:
        try:
            client = Client("caubetotbunggg/api")
            embedding = client.predict(
                text=f"test",
                api_name="/embed_text"
            )
            if embedding:
                return True
        except Exception as e:
            return False, str(e)

    @staticmethod
    def health_status() -> dict:
        return {
            "database": HealthService.check_database(),
            "llm_api": HealthService.check_llm(),
            "baseurl": HealthService.check_baseurl(),
            "reranker": HealthService.check_reranker(),
            "embedder": HealthService.check_embedder(),
        }

