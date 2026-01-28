import io
import json
import logging
import zipfile

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from .config_loader import load_vertical_config
from .dataset_builder import build_eval_dataset_entries, build_golden_dataset_entries
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
        eval_entries = build_eval_dataset_entries(plans, template_engine)
        golden_entries = build_golden_dataset_entries(plans, template_engine)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    archive_buffer = io.BytesIO()
    with zipfile.ZipFile(archive_buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("eval_dataset.jsonl", _to_jsonl_bytes(eval_entries))
        archive.writestr("golden_dataset.jsonl", _to_jsonl_bytes(golden_entries))
        archive.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))

    archive_buffer.seek(0)
    filename = f"{request.vertical.value}_dataset.zip"

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
