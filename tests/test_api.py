from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_paye_endpoint():
    response = client.get("/paye", params={"basic": 5000})
    assert response.status_code == 200
    body = response.json()
    assert body["paye"] == 785.75
    assert body["net_pay"] == 3939.25


def test_negative_salary_is_rejected():
    assert client.get("/paye", params={"basic": -100}).status_code == 422


def test_basic_is_required():
    assert client.get("/paye").status_code == 422
