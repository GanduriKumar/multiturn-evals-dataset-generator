from pathlib import Path

import pytest

from app import config_loader
from app.template_engine import TemplateEngine


@pytest.fixture()
def demo_config_dir() -> Path:
    return (
        Path(__file__).resolve().parent
        / "data"
        / "config"
        / "verticals"
    )


def test_load_vertical_config(monkeypatch: pytest.MonkeyPatch, demo_config_dir: Path) -> None:
    monkeypatch.setattr(config_loader, "CONFIG_DIR", demo_config_dir)

    payload = config_loader.load_vertical_config("demo")

    assert payload["vertical"] == "demo"
    assert payload["workflows"] == ["DemoWorkflow"]
    assert payload["behaviours"] == ["HappyPath", "LowContext"]
    assert payload["axes"] == {
        "intent": ["refund", "exchange"],
        "channel": ["web", "mobile"],
    }


def test_load_vertical_templates(monkeypatch: pytest.MonkeyPatch, demo_config_dir: Path) -> None:
    monkeypatch.setattr(config_loader, "CONFIG_DIR", demo_config_dir)

    templates = config_loader.load_vertical_templates("demo")

    assert "demo_workflow" in templates
    assert "templates" in templates["demo_workflow"]


def test_template_engine_realise_turn(monkeypatch: pytest.MonkeyPatch, demo_config_dir: Path) -> None:
    monkeypatch.setattr(config_loader, "CONFIG_DIR", demo_config_dir)

    engine = TemplateEngine.from_vertical("demo")
    rendered = engine.realise_turn(
        vertical="demo",
        workflow="DemoWorkflow",
        speaker="user",
        role="customer",
        behaviour="HappyPath",
        axes={"intent": "refund", "channel": "web"},
        variables={"customer_name": "Alex"},
    )

    assert rendered == "Hi Alex, I need a refund for my order placed via web."
