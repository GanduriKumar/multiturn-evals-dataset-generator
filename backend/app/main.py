from pathlib import Path

import yaml
from fastapi import FastAPI, HTTPException

from .models import IndustryVertical, VerticalConfigResponse

app = FastAPI(title="Eval Dataset Generator")

BASE_DIR = Path(__file__).resolve().parents[2]
CONFIG_DIR = BASE_DIR / "config" / "verticals"


def _load_yaml(path: Path) -> object:
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Missing config file: {path}")
    try:
        content = path.read_text(encoding="utf-8")
        return yaml.safe_load(content)
    except yaml.YAMLError as exc:
        raise HTTPException(status_code=500, detail=f"Invalid YAML in {path}: {exc}") from exc


def _load_list_config(path: Path, key: str) -> list[str]:
    data = _load_yaml(path)
    if data is None:
        return []
    if isinstance(data, dict):
        data = data.get(key, [])
    if not isinstance(data, list) or not all(isinstance(item, str) for item in data):
        raise HTTPException(status_code=500, detail=f"Invalid {key} config in {path}")
    return data


def _load_axes_config(path: Path) -> dict[str, list[str]]:
    data = _load_yaml(path)
    if data is None:
        return {}
    if isinstance(data, dict) and "axes" in data:
        data = data["axes"]
    if not isinstance(data, dict):
        raise HTTPException(status_code=500, detail=f"Invalid axes config in {path}")
    axes: dict[str, list[str]] = {}
    for axis_name, axis_values in data.items():
        if not isinstance(axis_name, str) or not isinstance(axis_values, list):
            raise HTTPException(status_code=500, detail=f"Invalid axes config in {path}")
        if not all(isinstance(value, str) for value in axis_values):
            raise HTTPException(status_code=500, detail=f"Invalid axes config in {path}")
        axes[axis_name] = axis_values
    return axes


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok"}


@app.get("/config/verticals/{vertical}", response_model=VerticalConfigResponse)
def get_vertical_config(vertical: IndustryVertical) -> VerticalConfigResponse:
    vertical_dir = CONFIG_DIR / vertical.value
    workflows = _load_list_config(vertical_dir / "workflows.yaml", "workflows")
    behaviours = _load_list_config(vertical_dir / "behaviours.yaml", "behaviours")
    axes = _load_axes_config(vertical_dir / "axes.yaml")
    return VerticalConfigResponse(
        vertical=vertical,
        workflows=workflows,
        behaviours=behaviours,
        axes=axes,
    )
