import pytest
import numpy as np
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
from app.main import app

client = TestClient(app, raise_server_exceptions=True)


@pytest.fixture
def mock_weaviate_query(monkeypatch):
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

    # patch the DOCUMENT_COLLECTION.query.hybrid to return our mock_results
    import app.services.retrieve_service as retrieve_service

    monkeypatch.setattr(retrieve_service.DOCUMENT_COLLECTION.query, "hybrid", lambda *a, **k: mock_results)
    return mock_results


@pytest.fixture
def mock_models(monkeypatch):
    """Mock get_embedding to avoid calling external service"""
    import app.services.retrieve_service as retrieve_service

    monkeypatch.setattr(retrieve_service, "get_embedding", lambda *a, **k: np.array([0.9] * 384))


def test_retrieve_happy_path(mock_weaviate_query, mock_models):
    response = client.post("/retrieve", params={"user_input": "hợp đồng"})
    assert response.status_code == 200
    data = response.json()
    assert "chunks" in data
    assert len(data["chunks"]) >= 1
    assert data["chunks"][0]["meta"]["law_id"] == "L01"


def test_retrieve_invalid_input():
    response = client.post("/retrieve", params={})
    assert response.status_code == 422


def test_retrieve_no_results(monkeypatch):
    import app.services.retrieve_service as retrieve_service

    monkeypatch.setattr(retrieve_service, "get_embedding", lambda *a, **k: np.array([0.1] * 384))
    mock_results = MagicMock()
    mock_results.objects = []
    monkeypatch.setattr(retrieve_service.DOCUMENT_COLLECTION.query, "hybrid", lambda *a, **k: mock_results)

    response = client.post("/retrieve", params={"user_input": "xyzabc"})
    assert response.status_code == 200
    data = response.json()
    assert data.get("chunks") == []


def test_retrieve_score_below_threshold(monkeypatch):
    import app.services.retrieve_service as retrieve_service

    monkeypatch.setattr(retrieve_service, "get_embedding", lambda *a, **k: np.array([0.1] * 384))
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
    monkeypatch.setattr(retrieve_service.DOCUMENT_COLLECTION.query, "hybrid", lambda *a, **k: mock_results)

    response = client.post("/retrieve", params={"user_input": "something"})
    assert response.status_code == 200
    assert response.json().get("chunks") == []


def test_retrieve_exception_handling(monkeypatch):
    import app.services.retrieve_service as retrieve_service

    monkeypatch.setattr(retrieve_service, "get_embedding", lambda *a, **k: np.array([0.1] * 384))
    def raise_exc(*a, **k):
        raise Exception("DB failure")
    monkeypatch.setattr(retrieve_service.DOCUMENT_COLLECTION.query, "hybrid", raise_exc)

    response = client.post("/retrieve", params={"user_input": "hợp đồng"})
    assert response.status_code == 500
    assert "Vector search failed" in response.text
