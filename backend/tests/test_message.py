from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


def test_post_message() -> None:
    response = client.post("/api/message", json={"input": "hi"})
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "hi" in data["message"]


def test_health() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
