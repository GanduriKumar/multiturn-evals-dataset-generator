from fastapi import FastAPI, HTTPException

from .config_loader import load_vertical_config
from .models import IndustryVertical, VerticalConfigResponse

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
