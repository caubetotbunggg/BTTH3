import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

from app.main import app  # hoặc nơi bạn đăng ký router chứa /rag

client = TestClient(app)

# Dữ liệu mẫu
mock_chunks = {
    "chunks": [
        {
            "chunk_id": "0",
            "text": "Nội dung điều luật mẫu",
            "score": 0.1,
            "meta": {
                "law_id": "L1",
                "section_title": "Điều 1",
                "date": "2024-01-01",
            },
        }
    ]
}

@patch("app.rag.search", return_value=mock_chunks)
@patch("app.rag.get_llm_response_with_timeout", new_callable=AsyncMock)
def test_rag_happy_path(mock_llm, mock_search):
    mock_llm.return_value = "Đây là câu trả lời [Luật Giao Thông – Điều 1]."

    response = client.post("/rag", params={"user_input": "quy định giao thông", "k": 1})
    assert response.status_code == 200
    assert "Điều 1" in response.text

@patch("app.rag.search", return_value=mock_chunks)
@patch("app.rag.get_llm_response_with_timeout", new_callable=AsyncMock)
def test_rag_llm_timeout(mock_llm, mock_search):
    mock_llm.return_value = ""  # giả lập lần 1 timeout
    response = client.post("/rag", params={"user_input": "trách nhiệm pháp lý", "k": 1})
    assert response.status_code == 200 or response.status_code == 500  # tùy bạn định xử lý

@patch("app.rag.search", return_value={"chunks": []})
@patch("app.rag.get_llm_response_with_timeout", new_callable=AsyncMock)
def test_rag_no_chunks(mock_llm, mock_search):
    response = client.post("/rag", params={"user_input": "không có dữ liệu", "k": 1})
    assert response.status_code == 500

@patch("app.rag.search", return_value=mock_chunks)
@patch("app.rag.get_llm_response_with_timeout", new_callable=AsyncMock)
def test_rag_response_format(mock_llm, mock_search):
    mock_llm.return_value = "Căn cứ vào [Điều 1], bạn phải tuân thủ."

    response = client.post("/rag", params={"user_input": "trích dẫn luật", "k": 1})
    assert response.status_code == 200
    assert "[" in response.text  # có citation
