from __future__ import annotations

import json
from typing import Any

from app.dataset_builder import (
    build_eval_dataset_entries,
    build_golden_dataset_entries,
    write_eval_dataset_jsonl,
    write_golden_dataset_jsonl,
)
from app.models import BehaviourFlag, ConversationPlan, IndustryVertical


class DummyTemplateEngine:
    def realise_turn(self, *args: Any, **kwargs: Any) -> str:
        raise AssertionError("Template rendering should not be called for explicit text.")


def _build_plan() -> ConversationPlan:
    return ConversationPlan(
        vertical=IndustryVertical.commerce,
        workflow="ReturnsRefunds",
        scenario_id="scenario-001",
        behaviours=[BehaviourFlag.happy_path],
        axes={"policy_boundary": "allowed"},
        turn_plan=[
            {"speaker": "user", "role": "customer", "text": "I need a refund."},
            {"speaker": "assistant", "role": "agent", "text": "I can help with that."},
            {"speaker": "user", "role": "customer", "text": "Here is my order."},
        ],
    )


def test_build_eval_dataset_entries_user_only() -> None:
    plan = _build_plan()
    entries = build_eval_dataset_entries([plan], DummyTemplateEngine())

    assert len(entries) == 1
    payload = entries[0]

    assert payload["vertical"] == "commerce"
    assert payload["workflow"] == "ReturnsRefunds"
    assert payload["behaviours"] == ["HappyPath"]

    turns = payload["turns"]
    assert [turn["speaker"] for turn in turns] == ["user", "user"]
    assert all("text" in turn for turn in turns)
    assert all("agent_expected" not in turn for turn in turns)


def test_build_golden_dataset_entries_includes_agent_expected() -> None:
    plan = _build_plan()
    entries = build_golden_dataset_entries([plan], DummyTemplateEngine())

    assert len(entries) == 1
    turns = entries[0]["turns"]

    assert [turn["speaker"] for turn in turns] == ["user", "assistant", "user"]
    assert turns[1]["agent_expected"] == "I can help with that."


def test_write_jsonl_outputs_lines(tmp_path) -> None:
    plan = _build_plan()
    eval_path = tmp_path / "eval_dataset.jsonl"
    golden_path = tmp_path / "golden_dataset.jsonl"

    write_eval_dataset_jsonl([plan], DummyTemplateEngine(), eval_path)
    write_golden_dataset_jsonl([plan], DummyTemplateEngine(), golden_path)

    eval_lines = eval_path.read_text(encoding="utf-8").strip().splitlines()
    golden_lines = golden_path.read_text(encoding="utf-8").strip().splitlines()

    assert len(eval_lines) == 1
    assert len(golden_lines) == 1

    assert json.loads(eval_lines[0])["turns"][0]["speaker"] == "user"
    assert json.loads(golden_lines[0])["turns"][1]["speaker"] == "assistant"
