import pytest
from app import app

@pytest.fixture
def client():
    app.testing = True
    return app.test_client()

def test_metrics_endpoint(client):
    """تأكد إن /metrics بيرجع 200"""
    response = client.get("/metrics")
    assert response.status_code == 200

