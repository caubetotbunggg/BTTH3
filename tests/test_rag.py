import pytest
from unittest.mock import MagicMock

from app.services.rag_service import RAGService


def test_rag_pipeline_success(mocker):
    # --- Mock retrieve ---
    fake_chunk = MagicMock()
    fake_chunk.text = "Điều 1: Quy định..."
    fake_chunk.meta = {"section_title": "Điều 1"}
    fake_chunk.dict.return_value = {"id": "1", "text": fake_chunk.text, "meta": fake_chunk.meta}

    mock_retrieve = mocker.patch(
        "app.services.rag_service.RetrieveService.retrieve",
        return_value={"chunks": [fake_chunk]},
    )

    # --- Mock LLM response ---
    mock_llm = mocker.patch(
        "app.services.rag_service._get_llm_response_with_timeout",
        return_value="Trả lời hợp lệ [Luật A – Điều 1]"
    )

    # --- Run rag pipeline ---
    result = RAGService.rag_pipeline("quy định gì?", k=1)

    # --- Assertions ---
    mock_retrieve.assert_called_once_with("quy định gì?", 1)
    mock_llm.assert_called_once()
    assert "answer" in result
    assert result["answer"] == "Trả lời hợp lệ [Luật A – Điều 1]"
    assert len(result["used_chunks"]) == 1


def test_rag_pipeline_timeout(mocker):
    # Mock retrieve trả về chunk hợp lệ
    fake_chunk = MagicMock()
    fake_chunk.text = "Điều 2: Nội dung..."
    fake_chunk.meta = {"section_title": "Điều 2"}
    fake_chunk.dict.return_value = {"id": "2", "text": fake_chunk.text, "meta": fake_chunk.meta}

    mocker.patch(
        "app.services.rag_service.RetrieveService.retrieve",
        return_value={"chunks": [fake_chunk]},
    )

    # Mock LLM timeout
    mocker.patch(
        "app.services.rag_service._get_llm_response_with_timeout",
        return_value="Hệ thống đang bận, vui lòng thử lại sau."
    )

    result = RAGService.rag_pipeline("câu hỏi?", k=1)

    assert result["answer"] == "Hệ thống đang bận, vui lòng thử lại sau."
    assert len(result["used_chunks"]) == 1
