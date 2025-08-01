from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from services.tools import (
    ChunkResponse,
    FormatCitationsInput,
    FormatCitationsResponse,
    GenerateInput,
    GenerateResponse,
    SearchInput,
    SearchResponse,
    format_citations,
    generate_answer,
    retrieve_laws,
)

print("✅ File test được load")

# ------------------------------#
# ✅ Test: retrieve_laws
# ------------------------------#


def test_retrieve_laws_success(mocker):
    # Mock SentenceTransformer.encode
    mock_model = MagicMock()
    mock_model.encode.return_value = [0.1] * 384
    mocker.patch("services.tools.SentenceTransformer", return_value=mock_model)

    # Mock ChromaDB collection.query
    mock_collection = MagicMock()
    mock_collection.query.return_value = {
        "documents": [["Nội dung luật"]],
        "distances": [[0.2]],
        "metadatas": [[{"law_id": "1", "section_title": "Điều 1"}]],
    }

    mock_client = MagicMock()
    mock_client.get_or_create_collection.return_value = mock_collection
    mocker.patch("services.tools.chromadb.PersistentClient", return_value=mock_client)

    input = SearchInput(user_input="Tôi cần hỏi về giao thông", k=1)
    result: SearchResponse = retrieve_laws(input)

    assert len(result.chunks) == 1
    assert result.chunks[0].text == "Nội dung luật"
    assert result.chunks[0].meta["section_title"] == "Điều 1"


def test_retrieve_laws_empty_result(mocker):
    mock_model = MagicMock()
    mock_model.encode.return_value = [0.1] * 384
    mocker.patch("services.tools.SentenceTransformer", return_value=mock_model)

    mock_collection = MagicMock()
    mock_collection.query.return_value = {
        "documents": [[]],
        "distances": [[]],
        "metadatas": [[]],
    }

    mock_client = MagicMock()
    mock_client.get_or_create_collection.return_value = mock_collection
    mocker.patch("services.tools.chromadb.PersistentClient", return_value=mock_client)

    input = SearchInput(user_input="abc", k=1)

    with pytest.raises(HTTPException) as exc_info:
        retrieve_laws(input)

    assert exc_info.value.status_code == 500
    assert "No results found" in str(exc_info.value.detail)


# ------------------------------#
# ✅ Test: generate_answer
# ------------------------------#


def test_generate_answer_success(mocker):
    mock_chunks = [
        ChunkResponse(
            chunk_id="1",
            text="Văn bản luật về điều 1",
            score=0.2,
            meta={"section_title": "Điều 1", "law_id": "001"},
        )
    ]

    input = GenerateInput(user_input="Hỏi về điều 1", chunks=mock_chunks)

    # Mock Gemini LLM
    mocker.patch(
        "services.tools.get_llm_response_with_timeout",
        return_value="Đây là câu trả lời từ LLM",
    )

    result: GenerateResponse = generate_answer(input)

    assert isinstance(result, str)
    assert "LLM" in result


def test_generate_answer_empty_input():
    input = GenerateInput(user_input="", chunks=[])
    with pytest.raises(HTTPException) as exc_info:
        generate_answer(input)

    assert exc_info.value.status_code == 400


# ------------------------------#
# ✅ Test: format_citations
# ------------------------------#


def test_format_citations_success():
    chunks = [
        ChunkResponse(
            chunk_id="1",
            text="Một đoạn văn bản",
            score=0.3,
            meta={"section_title": "Điều 3", "law_id": "ABC"},
        )
    ]

    input = FormatCitationsInput(answer="Đây là câu trả lời", chunks=chunks)

    result: FormatCitationsResponse = format_citations(input)
    assert "Trích dẫn" in result.formatted_answer
    assert "Điều 3" in result.formatted_answer


def test_format_citations_empty_answer():
    input = FormatCitationsInput(answer=" ", chunks=[])
    with pytest.raises(HTTPException) as exc_info:
        format_citations(input)

    assert exc_info.value.status_code == 400
