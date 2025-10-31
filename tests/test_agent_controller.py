import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from app.main import app
from app.models.retrieve_model import RetrieveResponse, ChunkResponse
from app.models.tools_model import (
    Retrieve_tool_request,
    Retrieve_tool_response,
    Generate_answer_tool_request,
    Generate_answer_tool_response,
    Format_citation_tool_request,
    Format_citation_tool_response,
)

client = TestClient(app)

# ---------- Helper ----------
def make_dummy_retrieve_response():
    dummy_chunk = ChunkResponse(
        chunk_id="c1",
        text="Điều 1: Quy định chung",
        score=0.95,
        meta={"law_id": "L01", "title": "Điều 1", "date": "2020-01-01"},
    )
    return RetrieveResponse(chunks=[dummy_chunk])

# ---------- Happy path ----------
@patch("app.controllers.tools_controller.Retrieve_tool.retrieve_laws")
@patch("app.controllers.tools_controller.Generate_answer_tool.generate_answer")
@patch("app.controllers.tools_controller.Format_citation.format_citation")
def test_agent_happy_path(mock_format, mock_generate, mock_retrieve):
    # Mock BaseModel
    dummy_retrieve = Retrieve_tool_response(chunks=make_dummy_retrieve_response())
    mock_retrieve.return_value = dummy_retrieve

    dummy_answer = Generate_answer_tool_response(answer="Fake answer")
    mock_generate.return_value = dummy_answer

    dummy_format = Format_citation_tool_response(formatted_answer="Fake formatted")
    mock_format.return_value = dummy_format

    response = client.post("/agent", params={"user_input": "Điều luật gì?", "k": 1})
    assert response.status_code == 200
    data = response.json()
    print("Data:", data)
    assert data["status"] == "ok"
    assert data["laws"]["chunks"]["chunks"][0]["text"].startswith("Điều 1")
    assert data["answer"]["answer"] == "Fake answer"
    assert data["formatted"]["formatted_answer"] == "Fake formatted"


# ---------- Timeout path ----------
@patch("app.services.tools_service.Generate_answer_tool.generate_answer")
@patch("app.services.tools_service.Retrieve_tool.retrieve_laws")
def test_agent_timeout_path(mock_retrieve, mock_generate):
    import time

    mock_retrieve.return_value = Retrieve_tool_response(chunks=make_dummy_retrieve_response())

    def slow_generate(req: Generate_answer_tool_request):
        time.sleep(2)
        return Generate_answer_tool_response(answer="Slow answer")

    mock_generate.side_effect = slow_generate

    response = client.post(
        "/agent",
        params={"user_input": "Điều luật gì?", "k": 1, "timeout_sec": 1},
    )
    data = response.json()
    assert response.status_code == 200
    assert "timed out" in data["error"]

# ---------- Error path ----------
@patch("app.services.tools_service.Retrieve_tool.retrieve_laws")
def test_agent_error_path(mock_retrieve):
    mock_retrieve.side_effect = Exception("DB failure")

    response = client.post("/agent", params={"user_input": "Điều luật gì?", "k": 1})
    data = response.json()
    assert response.status_code == 200
    assert "failed" in data["error"]
