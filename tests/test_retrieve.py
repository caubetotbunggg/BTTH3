import pytest
import numpy as np
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
from app.main import app

# Do not create TestClient at import time because app startup may require external
# services (Weaviate). Each test will instantiate TestClient after applying mocks.


@pytest.fixture
def mock_weaviate_query(mocker):
    """Fixture mock query.hybrid để trả về 1 kết quả giả định"""
    mock_results = MagicMock()
    mock_obj = MagicMock()
    mock_obj.properties = {
        "text": "Nội dung về hợp đồng lao động.",
        "metadata": {
            "law_id": "L01",
            "title": "Điều 5 - Bộ luật Lao động",
            "date": "2019-11-20"
        }
    }
    mock_obj.metadata.score = 0.9
    mock_obj.metadata.explain_score = "Score explained here"
    mock_results.objects = [mock_obj]

    mocker.patch("app.services.retrieve_service.DOCUMENT_COLLECTION.query.hybrid", return_value=mock_results)
    return mock_results


@pytest.fixture
def mock_models(mocker):
    """Mock embedding model để tránh gọi thật"""
    mocker.patch("app.services.retrieve_service.get_embedding", return_value=np.array([0.9] * 384))


def test_retrieve_happy_path(mock_weaviate_query, mock_models):
    client = TestClient(app)
    response = client.post("/retrieve", params={"user_input": "hợp đồng"})
    assert response.status_code == 200
    data = response.json()
    assert "chunks" in data
    assert len(data["chunks"]) >= 1
    assert data["chunks"][0]["meta"]["law_id"] == "L01"


def test_retrieve_invalid_input():
    client = TestClient(app)
    response = client.post("/retrieve", params={})
    assert response.status_code == 422


def test_retrieve_no_results(mocker):
    mocker.patch("app.services.retrieve_service.get_embedding", return_value=np.array([0.1] * 384))
    mock_results = MagicMock()
    mock_results.objects = []
    mocker.patch("app.services.retrieve_service.DOCUMENT_COLLECTION.query.hybrid", return_value=mock_results)

    client = TestClient(app)
    response = client.post("/retrieve", params={"user_input": "xyzabc"})
    assert response.status_code == 204


def test_retrieve_score_below_threshold(mocker):
    mocker.patch("app.services.retrieve_service.get_embedding", return_value=np.array([0.1] * 384))
    mock_obj = MagicMock()
    mock_obj.properties = {
        "text": "irrelevant",
        "metadata": {
            "law_id": "X01",
            "title": "irrelevant",
            "date": "2000-01-01"
        }
    }
    mock_obj.metadata.score = 0.1
    mock_obj.metadata.explain_score = "Not important"

    mock_results = MagicMock()
    mock_results.objects = [mock_obj]
    mocker.patch("app.services.retrieve_service.DOCUMENT_COLLECTION.query.hybrid", return_value=mock_results)

    client = TestClient(app)
    response = client.post("/retrieve", params={"user_input": "something"})
    assert response.status_code == 204


def test_retrieve_exception_handling(mocker):
    mocker.patch("app.services.retrieve_service.get_embedding", return_value=np.array([0.1] * 384))
    mocker.patch("app.services.retrieve_service.DOCUMENT_COLLECTION.query.hybrid", side_effect=Exception("DB failure"))
    client = TestClient(app)
    response = client.post("/retrieve", params={"user_input": "hợp đồng"})
    assert response.status_code == 500
    assert "Vector search failed" in response.text
