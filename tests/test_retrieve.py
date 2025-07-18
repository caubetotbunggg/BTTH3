import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.retrieve import router

client = TestClient(app)


@pytest.fixture
def mock_embedding():
    return np.array([0.1] * 384)


# ---- Happy path ----
def test_search_happy_path(mocker, mock_embedding):
    mock_results = {
        "documents": [["Đây là chunk văn bản 1", "Chunk 2"]],
        "distances": np.array([[0.3, 0.6]]),
        "metadatas": [
            [
                {"law_id": "L01", "title": "Điều 1", "date": "2024-01-01"},
                {"law_id": "L02", "title": "Điều 2", "date": "2024-01-02"},
            ]
        ],
    }

    mocker.patch("app.retrieve.collection.query", return_value=mock_results)
    mocker.patch("app.retrieve.model.encode", return_value=mock_embedding)

    response = client.post("/search", params={"user_input": "hợp đồng"})
    data = response.json()

    assert response.status_code == 200
    assert "chunks" in data
    assert len(data["chunks"]) == 2
    assert data["chunks"][0]["meta"]["law_id"] == "L01"


# ---- No result (tất cả điểm > 0.7) ----
def test_search_no_result(mocker, mock_embedding):
    mock_results = {
        "documents": [["Chunk thấp"]],
        "distances": np.array([[0.9]]),
        "metadatas": [[{"law_id": "L03", "title": "Điều 3", "date": "2024-01-03"}]],
    }

    mocker.patch("app.retrieve.collection.query", return_value=mock_results)
    mocker.patch("app.retrieve.model.encode", return_value=mock_embedding)

    response = client.post("/search", params={"user_input": "abc"})
    assert response.status_code == 500
    assert response.json()["detail"] == "Vector search failed: 200: No results found"


# ---- Invalid input ----
def test_search_missing_query_param():
    response = client.post("/search")
    assert response.status_code == 422


# ---- Internal error (query fail) ----
def test_search_query_exception(mocker, mock_embedding):
    mocker.patch("app.retrieve.model.encode", return_value=mock_embedding)
    mocker.patch("app.retrieve.collection.query", side_effect=Exception("Boom"))

    response = client.post("/search", params={"user_input": "test"})
    assert response.status_code == 500
    assert "Vector search failed" in response.json()["detail"]
