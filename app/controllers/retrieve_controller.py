import logging

from fastapi import APIRouter, HTTPException, Query

from app.config.settings import setup_logger
from app.constants.http import HTTP_STATUS
from app.models.retrieve_model import RetrieveResponse
from app.services.retrieve_service import RetrieveService

logger = setup_logger("retrieve_controller", "../log/retrieve_info.log")

router = APIRouter()


@router.post("/retrieve", response_model=RetrieveResponse)
def retrieve(user_input: str = Query(...), k: int = Query(5)):
    logger.info(f"Received query: question='{user_input}', top_k={k}")
    try:
        response = RetrieveService.retrieve(user_input, k)
        if not response:
            raise HTTPException(
                status_code=HTTP_STATUS.NO_CONTENT, detail="No results found"
            )
        return response

    except Exception as e:
        logger.exception("Vector search failed")
        raise HTTPException(
            status_code=HTTP_STATUS.INTERNAL_SERVER_ERROR,
            detail=f"Vector search failed: {str(e)}",
        )   
