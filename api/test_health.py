"""Spec for feature 004 — api/ scaffold health route (issue #5).

Written before index.py exists; the import below is the failing (red) assertion
that drives the implementation.
"""

from fastapi.testclient import TestClient

from index import app

client = TestClient(app)


def test_health_returns_200_with_status_ok() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
