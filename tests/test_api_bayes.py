"""HTTP regression checks for the Bayes calculation endpoint."""
import pytest
from fastapi.testclient import TestClient
from agents.api import app

client = TestClient(app)


def test_api_positive_update():
    response = client.post("/api/calculate", json={
        "pretest_probability": 30, "sensitivity": 90,
        "specificity": 80, "result": "positive"
    })
    assert response.status_code == 200
    assert response.json()["posttest_probability"] == pytest.approx(65.85365853658537)


def test_api_negative_update():
    response = client.post("/api/calculate", json={
        "pretest_probability": 30, "sensitivity": 90,
        "specificity": 80, "result": "negative"
    })
    assert response.status_code == 200
    assert response.json()["posttest_probability"] == pytest.approx(5.084745762711864)


def test_api_invalid_update():
    response = client.post("/api/calculate", json={
        "pretest_probability": 200, "likelihood_ratio": 3
    })
    assert response.status_code == 422


def test_home_and_health():
    assert client.get("/").status_code == 200
    assert client.get("/health").status_code == 200
