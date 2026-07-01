from fastapi.testclient import TestClient

def test_read_root(client: TestClient):
    """Verifies that hitting root returns welcome payload with correct version."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "version" in data
    assert "CampusGPT X" in data["message"]

def test_check_health(client: TestClient):
    """Verifies that hitting health check route succeeds and reports statuses."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["api"]["status"] == "healthy"
    assert data["database"]["status"] == "healthy"
