from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response

from app.config.settings import logger
from app.constants.http import HTTP_STATUS
from app.models.retrieve_models import RetrieveResponse
from app.services.retrieve_service import retrieve_chunks

router = APIRouter()


@router.post("/retrieve", response_model=RetrieveResponse)
def retrieve(
    user_input: str = Query(..., description="Câu hỏi người dùng"),
    k: int = Query(5, description="Số lượng kết quả cần trả về"),
):
    try:
        logger.info(f"Received query: {user_input}, top_k={k}")
        response_chunks = retrieve_chunks(user_input, k)

        if not response_chunks:
            return Response(
                status_code=HTTP_STATUS["NO_CONTENT"], 
                content="No results found"
            )

        return {"chunks": response_chunks}

    except Exception as e:
        logger.exception("Vector search failed")
        raise HTTPException(
            status_code=HTTP_STATUS["INTERNAL_ERROR"],
            detail=f"Vector search failed: {str(e)}",
        )
