from __future__ import annotations

import json

from fastapi.testclient import TestClient

from app.main import app


def _jsonl_line(payload: dict) -> bytes:
    return (json.dumps(payload) + "\n").encode("utf-8")


def test_score_run_success() -> None:
    client = TestClient(app)

    golden_entry = {
        "conversation_id": "conv-1",
        "expected_actions": ["refund"],
        "key_facts": {"status": "approved"},
        "scoring_rules": {"disallowed_phrases": ["guarantee"]},
    }
    model_entry = {
        "conversation_id": "conv-1",
        "text": "Your refund is approved. I cannot guarantee timing.",
    }

    files = {
        "golden_dataset": ("golden.jsonl", _jsonl_line(golden_entry), "application/jsonl"),
        "model_outputs": ("model.jsonl", _jsonl_line(model_entry), "application/jsonl"),
    }
    data = {"model_id": "demo-model"}

    response = client.post("/score-run", files=files, data=data)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/jsonl")

    lines = response.text.strip().splitlines()
    assert len(lines) == 1

    scored = json.loads(lines[0])
    assert scored["conversation_id"] == "conv-1"
    assert scored["model_id"] == "demo-model"
    assert scored["expected_actions"]["matched"] == ["refund"]
    assert scored["key_facts"]["matched"] == ["status"]
    assert scored["policy_violations"]["violation_count"] == 1


def test_score_run_invalid_jsonl_returns_400() -> None:
    client = TestClient(app)

    files = {
        "golden_dataset": ("golden.jsonl", b"{not-json}\n", "application/jsonl"),
        "model_outputs": ("model.jsonl", b"{}\n", "application/jsonl"),
    }
    data = {"model_id": "demo-model"}

    response = client.post("/score-run", files=files, data=data)

    assert response.status_code == 400
