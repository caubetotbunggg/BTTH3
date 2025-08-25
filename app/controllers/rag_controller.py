import logging

from fastapi import APIRouter, HTTPException, Query

from app.config.settings import setup_logger
from app.constants.http import HTTP_STATUS
from app.models.rag_model import RAGResponse
from app.services.rag_service import RAGService

logger = setup_logger("rag_controller", "../BTTH3/log/rag_info.log")


router = APIRouter()


@router.post("/rag", response_model=RAGResponse)
def rag_endpoint(
    user_input: str = Query(
        ..., description="Câu hỏi hoặc truy vấn người dùng"
    ),
    k: int = Query(5, description="Số lượng chunks muốn truy vấn"),
):
    if not user_input.strip():
        raise HTTPException(
            status_code=HTTP_STATUS.BAD_REQUEST, 
            detail="Câu hỏi không được để trống"
        )

    try:
        return RAGService.rag_pipeline(user_input, k)
    except Exception as e:
        logger.exception("RAG pipeline failed")
        raise HTTPException(
            status_code=HTTP_STATUS.INTERNAL_SERVER_ERROR, 
            detail=str(e)
        )
