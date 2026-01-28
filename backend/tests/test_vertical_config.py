import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.mark.parametrize(
    "vertical",
    [
        "commerce",
        "banking",
        "insurance",
        "healthcare",
        "retail",
        "telecom",
    ],
)
def test_get_vertical_config_for_all_verticals(vertical: str) -> None:
    client = TestClient(app)
    response = client.get(f"/config/verticals/{vertical}")

    assert response.status_code == 200
    payload = response.json()

    assert payload["vertical"] == vertical
    assert "workflows" in payload
    assert "behaviours" in payload
    assert "axes" in payload

    assert isinstance(payload["workflows"], list)
    assert isinstance(payload["behaviours"], list)
    assert isinstance(payload["axes"], dict)

    assert len(payload["workflows"]) > 0
    assert len(payload["behaviours"]) > 0
    assert len(payload["axes"]) > 0


def test_get_vertical_config_with_invalid_vertical() -> None:
    client = TestClient(app)
    response = client.get("/config/verticals/not-a-vertical")

    assert response.status_code == 422
