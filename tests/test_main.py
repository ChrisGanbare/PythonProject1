from fastapi.testclient import TestClient

from loan_comparison.api.main import app


client = TestClient(app)


def test_health_check() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "OK"


def test_root_endpoint() -> None:
    response = client.get("/")
    assert response.status_code == 200
    payload = response.json()
    assert payload["service"]
    assert payload["version"] == "1.0.0"
    assert "endpoints" in payload
