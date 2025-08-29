import pytest
from app.services import tools_service
from app.models.retrieve_model import RetrieveResponse, ChunkResponse
from app.models.tools_model import (
    Retrieve_tool_request,
    Generate_answer_tool_request,
    Format_citation_tool_request,
)


# ---------- Helpers ----------
def make_dummy_retrieve_response():
    dummy_chunk = ChunkResponse(
        chunk_id="c1",
        text="Điều 1: Quy định chung",
        score=0.95,
        meta={"law_id": "L01", "title": "Điều 1", "date": "2020-01-01"},
    )
    return RetrieveResponse(chunks=[dummy_chunk])


# ---------- RETRIEVE TOOL ----------
def test_retrieve_tool_happy_path(mocker):
    mock_result = make_dummy_retrieve_response()
    mocker.patch(
        "app.services.retrieve_service.RetrieveService.retrieve",
        return_value=mock_result,
    )

    req = Retrieve_tool_request(user_input="luật gì?", k=1)
    resp = tools_service.Retrieve_tool.retrieve_laws(req)

    assert resp is not None
    assert len(resp.chunks.chunks) == 1
    assert resp.chunks.chunks[0].text.startswith("Điều 1")


def test_retrieve_tool_exception(mocker):
    mocker.patch(
        "app.services.retrieve_service.RetrieveService.retrieve",
        side_effect=Exception("DB failure"),
    )

    req = Retrieve_tool_request(user_input="luật gì?", k=1)
    resp = tools_service.Retrieve_tool.retrieve_laws(req)

    assert resp is None


# ---------- GENERATE ANSWER TOOL ----------
def test_generate_answer_tool_with_chunks(mocker):
    mocker.patch(
        "app.services.tools_service._get_llm_response_with_timeout",
        return_value="Fake LLM answer",
    )

    req = Generate_answer_tool_request(
        user_input="Hỏi gì đó",
        chunks=make_dummy_retrieve_response(),
    )
    resp = tools_service.Generate_answer_tool.generate_answer(req)

    assert resp is not None
    assert resp.answer == "Fake LLM answer"


def test_generate_answer_tool_no_chunks(mocker):
    mocker.patch(
        "app.services.tools_service._get_llm_response_with_timeout",
        return_value="No laws",
    )

    empty_resp = RetrieveResponse(chunks=[])
    req = Generate_answer_tool_request(user_input="Hỏi gì đó", chunks=empty_resp)
    resp = tools_service.Generate_answer_tool.generate_answer(req)

    assert resp is not None
    assert "Không có điều luật phù hợp" in resp.answer or resp.answer == "No laws"


def test_generate_answer_tool_exception(mocker):
    mocker.patch(
        "app.services.tools_service._get_llm_response_with_timeout",
        side_effect=Exception("LLM failure"),
    )

    req = Generate_answer_tool_request(
        user_input="Hỏi gì đó",
        chunks=make_dummy_retrieve_response(),
    )
    resp = tools_service.Generate_answer_tool.generate_answer(req)

    assert resp is None


# ---------- FORMAT CITATION TOOL ----------
def test_format_citation_tool_happy_path():
    req = Format_citation_tool_request(
        answer="Đây là câu trả lời",
        chunks=make_dummy_retrieve_response(),
    )
    resp = tools_service.Format_citation.format_citation(req)

    assert resp is not None
    assert "Đây là câu trả lời" in resp.formatted_answer
    assert "Các luật được trích dẫn" in resp.formatted_answer
    assert "Điều 1" in resp.formatted_answer


def test_format_citation_tool_exception():
    bad_resp = RetrieveResponse(chunks=[])  # không có chunks

    req = Format_citation_tool_request(answer="Test", chunks=bad_resp)
    resp = tools_service.Format_citation.format_citation(req)

    # tùy implement bạn có thể expect resp = None hoặc trả về answer thô
    assert resp is None or resp.formatted_answer.startswith("Test")
