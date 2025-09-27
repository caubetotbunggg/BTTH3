import logging

from fastapi import APIRouter, HTTPException

from app.config.settings import setup_logger
from app.constants.http import HTTP_STATUS
from app.models.rag_model import RAGRequest, RAGResponse
from app.services.rag_service import RAGService

logger = setup_logger("rag_controller", "../log/rag_info.log")


router = APIRouter()


@router.post("/rag", response_model=RAGResponse)
def rag_endpoint(user_input: str, k: int = 4):
    if not user_input.strip():
        return "Câu hỏi không được để trống"

    try:
        return RAGService.rag_pipeline(RAGRequest(user_input=user_input, k=k))
    except Exception as e:
        logger.exception("RAG pipeline failed")
        raise HTTPException(
            status_code=HTTP_STATUS.INTERNAL_SERVER_ERROR, 
            detail=str(e)
        )
