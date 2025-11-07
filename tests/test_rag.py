import pytest
from unittest.mock import MagicMock

from app.services.rag_service import RAGService
from app.models.rag_model import RAGRequest
import asyncio


def test_rag_pipeline_success(mocker):
    # --- Prepare fake retrieval output ---
    fake_chunk = MagicMock()
    fake_chunk.text = "Điều 1: Quy định..."
    fake_chunk.meta = {"section_title": "Điều 1"}

    # tree1 should return (reasoning, objects). objects is a list of dicts
    fake_objects = [{"text": fake_chunk.text, "metadata": fake_chunk.meta}]
    mock_tree = mocker.patch("app.config.tree_config.tree1", return_value=("reasoning", fake_objects))

    # --- Mock LLM response ---
    # patch asyncio.run to return the expected LLM string since the service
    # calls `asyncio.run(_get_llm_response_with_timeout(...))`.
    mock_llm = mocker.patch("asyncio.run", return_value="Trả lời hợp lệ [Luật A – Điều 1]")

    # --- Run rag pipeline with correct request object ---
    req = RAGRequest(user_input="quy định gì?", k=1)
    result = RAGService.rag_pipeline(req)

    # --- Assertions ---
    mock_tree.assert_called_once()
    mock_llm.assert_called_once()
    assert result.answer == "Trả lời hợp lệ [Luật A – Điều 1]"
    # reasoning should come from the mocked tree1 return value
    assert result.reasoning == "reasoning"


def test_rag_pipeline_timeout(mocker):
    fake_objects = [{"text": "Điều 2: Nội dung...", "metadata": {"section_title": "Điều 2"}}]
    mocker.patch("app.config.tree_config.tree1", return_value=("reasoning", fake_objects))

    # Mock LLM timeout response
    mocker.patch("asyncio.run", return_value="Hệ thống đang bận, vui lòng thử lại sau.")

    req = RAGRequest(user_input="câu hỏi?", k=1)
    result = RAGService.rag_pipeline(req)

    assert result.answer == "Hệ thống đang bận, vui lòng thử lại sau."
    assert result.reasoning == "reasoning"
