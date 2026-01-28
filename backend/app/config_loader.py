from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import yaml

from .models import IndustryVertical

BASE_DIR = Path(__file__).resolve().parents[2]
CONFIG_DIR = BASE_DIR / "config" / "verticals"


def _load_yaml(path: Path) -> Any:
    if not path.exists():
        raise FileNotFoundError(f"Missing config file: {path}")
    try:
        content = path.read_text(encoding="utf-8")
        return yaml.safe_load(content)
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML in {path}: {exc}") from exc


def _load_list_config(path: Path, key: str) -> List[str]:
    data = _load_yaml(path)
    if data is None:
        return []
    if isinstance(data, dict):
        data = data.get(key, [])
    if not isinstance(data, list) or not all(isinstance(item, str) for item in data):
        raise ValueError(f"Invalid {key} config in {path}")
    return data


def _load_axes_config(path: Path) -> Dict[str, List[str]]:
    data = _load_yaml(path)
    if data is None:
        return {}
    if isinstance(data, dict) and "axes" in data:
        data = data["axes"]
    if not isinstance(data, dict):
        raise ValueError(f"Invalid axes config in {path}")
    axes: Dict[str, List[str]] = {}
    for axis_name, axis_values in data.items():
        if not isinstance(axis_name, str) or not isinstance(axis_values, list):
            raise ValueError(f"Invalid axes config in {path}")
        if not all(isinstance(value, str) for value in axis_values):
            raise ValueError(f"Invalid axes config in {path}")
        axes[axis_name] = axis_values
    return axes


def _coerce_vertical(vertical: IndustryVertical | str) -> str:
    if isinstance(vertical, IndustryVertical):
        return vertical.value
    return vertical


def load_vertical_config(vertical: IndustryVertical | str) -> Dict[str, object]:
    vertical_key = _coerce_vertical(vertical)
    vertical_dir = CONFIG_DIR / vertical_key
    if not vertical_dir.exists():
        raise FileNotFoundError(f"Missing vertical directory: {vertical_dir}")

    workflows = _load_list_config(vertical_dir / "workflows.yaml", "workflows")
    behaviours = _load_list_config(vertical_dir / "behaviours.yaml", "behaviours")
    axes = _load_axes_config(vertical_dir / "axes.yaml")

    return {
        "vertical": vertical_key,
        "workflows": workflows,
        "behaviours": behaviours,
        "axes": axes,
    }


def load_vertical_templates(vertical: IndustryVertical | str) -> Dict[str, Any]:
    vertical_key = _coerce_vertical(vertical)
    templates_dir = CONFIG_DIR / vertical_key / "templates"
    if not templates_dir.exists():
        raise FileNotFoundError(f"Missing templates directory: {templates_dir}")

    template_files = sorted(
        [path for path in templates_dir.glob("*.y*ml") if path.is_file()]
    )
    if not template_files:
        raise FileNotFoundError(f"No template files found in: {templates_dir}")

    templates: Dict[str, Any] = {}
    for template_file in template_files:
        data = _load_yaml(template_file)
        if data is None:
            raise ValueError(f"Empty template file: {template_file}")
        templates[template_file.stem] = data

    return templates
