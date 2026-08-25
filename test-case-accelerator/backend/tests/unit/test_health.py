from app.api.v1.endpoints.health import HealthResponse, health_check


def test_health_check_returns_healthy_status() -> None:
    assert health_check() == HealthResponse(status="healthy")
