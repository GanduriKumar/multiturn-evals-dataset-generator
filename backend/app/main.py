import io
import json

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from .config_loader import load_vertical_config
from .models import IndustryVertical, VerticalConfigResponse
from .scoring import score_dataset

app = FastAPI(title="Eval Dataset Generator")


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
