import hashlib
import io
import json
import logging
import re
import zipfile

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from .config_loader import load_vertical_config
from .dataset_builder import build_eval_dataset_entries, build_golden_dataset, build_golden_dataset_entries
from .generation import build_conversation_plans
from .models import GenerationRequest, IndustryVertical, VerticalConfigResponse
from .scoring import score_dataset
from .template_engine import TemplateEngine

app = FastAPI(title="Eval Dataset Generator")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("eval_dataset_generator")


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok"}


@app.get("/config/verticals/{vertical}", response_model=VerticalConfigResponse)
def get_vertical_config(vertical: IndustryVertical) -> VerticalConfigResponse:
    try:
        payload = load_vertical_config(vertical)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    logger.info(
        "vertical_config_loaded %s",
        json.dumps(
            {
                "vertical": vertical.value,
                "workflows": payload["workflows"],
                "behaviours": payload["behaviours"],
                "axes": payload["axes"],
            },
            ensure_ascii=False,
        ),
    )

    return VerticalConfigResponse(
        vertical=vertical,
        workflows=payload["workflows"],
        behaviours=payload["behaviours"],
        axes=payload["axes"],
    )


def _parse_jsonl_bytes(payload: bytes) -> list[dict]:
    decoded = payload.decode("utf-8")
    entries: list[dict] = []
    for line in decoded.splitlines():
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=400, detail=f"Invalid JSONL: {exc}") from exc
        if not isinstance(entry, dict):
            raise HTTPException(status_code=400, detail="Invalid JSONL entry; expected object")
        entries.append(entry)
    return entries


def _to_jsonl_bytes(entries: list[dict]) -> bytes:
    buffer = io.StringIO()
    for entry in entries:
        buffer.write(json.dumps(entry, ensure_ascii=False))
        buffer.write("\n")
    return buffer.getvalue().encode("utf-8")


def _parse_generation_request(payload: str) -> GenerationRequest:
    if hasattr(GenerationRequest, "model_validate_json"):
        return GenerationRequest.model_validate_json(payload)
    return GenerationRequest.parse_raw(payload)


def _slugify(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "-", value.strip().lower())
    return cleaned.strip("-") or "na"


def _normalize_behaviours(behaviours: list) -> list[str]:
    normalized: list[str] = []
    for behaviour in behaviours:
        if hasattr(behaviour, "value"):
            normalized.append(str(behaviour.value))
        else:
            normalized.append(str(behaviour))
    return normalized


def _normalize_axes(axes: dict) -> dict[str, list[str]]:
    normalized: dict[str, list[str]] = {}
    for axis, values in axes.items():
        if isinstance(values, str):
            normalized[axis] = [values]
        elif isinstance(values, list):
            normalized[axis] = [value for value in values if value]
    return normalized


def _is_all_selected(selected: list[str], all_values: list[str]) -> bool:
    if not all_values:
        return True
    return set(selected) == set(all_values)


def _summarize_list(items: list[str], label: str, max_items: int = 3) -> str | None:
    if not items:
        return None
    slugs = [_slugify(item) for item in items if item]
    if not slugs:
        return None
    if len(slugs) > max_items:
        slugs = slugs[:max_items] + [f"plus{len(items) - max_items}"]
    return f"{label}-" + "+".join(slugs)


def _build_axes_segment(
    selected_axes: dict[str, list[str]],
    config_axes: dict[str, list[str]],
) -> str | None:
    segments: list[str] = []
    for axis, all_values in config_axes.items():
        values = selected_axes.get(axis, [])
        if _is_all_selected(values, all_values):
            continue
        value_segment = _summarize_list(values or ["none"], _slugify(axis))
        if value_segment:
            segments.append(value_segment)
    if not segments:
        return None
    return "scn-" + "-".join(segments)


def _build_dataset_id(
    request: GenerationRequest,
    vertical_config: dict,
    version: str = "1.0.0",
) -> tuple[str, bool]:
    workflows_all = _is_all_selected(request.workflows, vertical_config.get("workflows", []))

    config_behaviours = vertical_config.get("behaviours", [])
    selected_behaviours = (
        _normalize_behaviours(request.behaviours) if request.behaviours else list(config_behaviours)
    )
    behaviours_all = _is_all_selected(selected_behaviours, config_behaviours)

    config_axes = vertical_config.get("axes", {})
    selected_axes = _normalize_axes(request.axes)
    axes_all = True
    for axis, all_values in config_axes.items():
        values = selected_axes.get(axis, [])
        if not _is_all_selected(values, list(all_values)):
            axes_all = False
            break

    if workflows_all and behaviours_all and axes_all:
        return f"{request.vertical.value}-combined-{version}", True

    workflow_segment = _summarize_list(request.workflows, "wf")
    behaviour_segment = (
        _summarize_list(selected_behaviours, "bhv") if not behaviours_all else None
    )
    axes_segment = _build_axes_segment(selected_axes, config_axes)
    segments = [segment for segment in [workflow_segment, behaviour_segment, axes_segment] if segment]
    summary = "-".join(segments) or "custom"
    summary = re.sub(r"-+", "-", summary).strip("-")

    selection_payload = {
        "workflows": sorted(request.workflows),
        "behaviours": sorted(selected_behaviours),
        "axes": {key: sorted(values) for key, values in selected_axes.items()},
    }
    hash_suffix = hashlib.sha1(
        json.dumps(selection_payload, sort_keys=True).encode("utf-8")
    ).hexdigest()[:8]

    if len(summary) > 120:
        summary = f"{summary[:90].rstrip('-')}-{hash_suffix}"

    return f"{request.vertical.value}-{summary}-{version}", False


@app.post("/generate-dataset")
async def generate_dataset(
    config: str = Form(...),
    domain_schema: UploadFile | None = File(None),
    behaviour_schema: UploadFile | None = File(None),
    axes_schema: UploadFile | None = File(None),
) -> StreamingResponse:
    try:
        request = _parse_generation_request(config)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if domain_schema or behaviour_schema or axes_schema:
        logger.info("schema_overrides_received")

    try:
        plans, manifest = build_conversation_plans(request)
        template_engine = TemplateEngine.from_vertical(request.vertical)
        vertical_config = load_vertical_config(request.vertical)
        
        # Build dataset entries
        eval_entries = build_eval_dataset_entries(plans, template_engine)
        
        # Build golden dataset
        dataset_id, is_combined = _build_dataset_id(request, vertical_config, version="1.0.0")
        golden_dataset_obj = build_golden_dataset(
            plans,
            template_engine,
            vertical_config,
            dataset_id=dataset_id,
            version="1.0.0",
        )
        
        # Build dataset JSON structure
        dataset_json = {
            "dataset_id": dataset_id,
            "version": "1.0.0",
            "metadata": {
                "domain": request.vertical.value,
                "difficulty": "mixed",
                "tags": [
                    "combined" if is_combined else "custom",
                    plans[0].domain_label if plans else request.vertical.value,
                ],
            },
            "conversations": eval_entries,
        }
        
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    archive_buffer = io.BytesIO()
    with zipfile.ZipFile(archive_buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        # Write dataset.json
        dataset_bytes = json.dumps(dataset_json, ensure_ascii=False, indent=2).encode("utf-8")
        archive.writestr(f"{dataset_id}.dataset.json", dataset_bytes)
        
        # Write golden.json
        if hasattr(golden_dataset_obj, "model_dump"):
            golden_dict = golden_dataset_obj.model_dump()
        else:
            golden_dict = golden_dataset_obj.dict()
        golden_bytes = json.dumps(golden_dict, ensure_ascii=False, indent=2).encode("utf-8")
        archive.writestr(f"{dataset_id}.golden.json", golden_bytes)
        
        # Write manifest.json for backward compatibility
        archive.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))

    archive_buffer.seek(0)
    filename = f"{dataset_id}.zip"

    logger.info(
        "dataset_generated %s",
        json.dumps(
            {
                "vertical": request.vertical.value,
                "workflows": request.workflows,
                "behaviours": [b.value for b in request.behaviours],
                "total": len(plans),
            },
            ensure_ascii=False,
        ),
    )

    return StreamingResponse(
        archive_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@app.post("/score-run")
async def score_run(
    golden_dataset: UploadFile = File(...),
    model_outputs: UploadFile = File(...),
    model_id: str = Form(...),
) -> StreamingResponse:
    try:
        golden_payload = await golden_dataset.read()
        model_payload = await model_outputs.read()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    golden_entries = _parse_jsonl_bytes(golden_payload)
    model_entries = _parse_jsonl_bytes(model_payload)

    scored = score_dataset(golden_entries, model_entries)
    for entry in scored:
        entry["model_id"] = model_id

    output_bytes = _to_jsonl_bytes(scored)

    return StreamingResponse(
        io.BytesIO(output_bytes),
        media_type="application/jsonl",
        headers={"Content-Disposition": "attachment; filename=scored_results.jsonl"},
    )
