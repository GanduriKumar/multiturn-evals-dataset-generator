from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence

from .models import BehaviourFlag, ConversationPlan
from .template_engine import TemplateEngine


def build_eval_dataset_entries(
    plans: Sequence[ConversationPlan],
    template_engine: TemplateEngine,
) -> List[Dict[str, Any]]:
    """Build eval dataset entries with user-only turns."""
    entries: List[Dict[str, Any]] = []
    for plan in plans:
        turns = _build_user_turns(plan, template_engine)
        entries.append(_build_conversation_payload(plan, turns))
    return entries


def build_golden_dataset_entries(
    plans: Sequence[ConversationPlan],
    template_engine: TemplateEngine,
) -> List[Dict[str, Any]]:
    """Build golden dataset entries with user + agent_expected turns."""
    entries: List[Dict[str, Any]] = []
    for plan in plans:
        turns = _build_full_turns(plan, template_engine)
        entries.append(_build_conversation_payload(plan, turns))
    return entries


def write_eval_dataset_jsonl(
    plans: Sequence[ConversationPlan],
    template_engine: TemplateEngine,
    output_path: Path | str,
) -> None:
    """Write eval_dataset.jsonl to disk."""
    entries = build_eval_dataset_entries(plans, template_engine)
    _write_jsonl(entries, output_path)


def write_golden_dataset_jsonl(
    plans: Sequence[ConversationPlan],
    template_engine: TemplateEngine,
    output_path: Path | str,
) -> None:
    """Write golden_dataset.jsonl to disk."""
    entries = build_golden_dataset_entries(plans, template_engine)
    _write_jsonl(entries, output_path)


def _build_user_turns(
    plan: ConversationPlan,
    template_engine: TemplateEngine,
) -> List[Dict[str, Any]]:
    """Render only user turns from the plan."""
    turns: List[Dict[str, Any]] = []
    for index, turn in enumerate(plan.turn_plan):
        if turn.get("speaker") != "user":
            continue
        text = _render_turn_text(plan, turn, template_engine)
        turns.append(
            {
                "turn_index": index,
                "speaker": "user",
                "role": turn.get("role", ""),
                "text": text,
            }
        )
    return turns


def _build_full_turns(
    plan: ConversationPlan,
    template_engine: TemplateEngine,
) -> List[Dict[str, Any]]:
    """Render user + agent_expected turns from the plan."""
    turns: List[Dict[str, Any]] = []
    for index, turn in enumerate(plan.turn_plan):
        speaker = turn.get("speaker")
        if speaker not in {"user", "agent", "assistant"}:
            continue
        text = _render_turn_text(plan, turn, template_engine)
        if speaker == "user":
            turns.append(
                {
                    "turn_index": index,
                    "speaker": "user",
                    "role": turn.get("role", ""),
                    "text": text,
                }
            )
        else:
            turns.append(
                {
                    "turn_index": index,
                    "speaker": "assistant",
                    "role": turn.get("role", "assistant"),
                    "agent_expected": text,
                }
            )
    return turns


def _render_turn_text(
    plan: ConversationPlan,
    turn: Mapping[str, Any],
    template_engine: TemplateEngine,
) -> str:
    """Render text using templates unless explicit text is provided."""
    if isinstance(turn.get("text"), str):
        return turn["text"]

    axes = dict(plan.axes)
    if isinstance(turn.get("axes"), Mapping):
        axes.update(turn["axes"])

    behaviour = _coerce_behaviour(turn.get("behaviour"), plan.behaviours)
    variables = turn.get("variables") if isinstance(turn.get("variables"), Mapping) else {}

    return template_engine.realise_turn(
        vertical=plan.vertical,
        workflow=plan.workflow,
        speaker=turn.get("speaker", "user"),
        role=turn.get("role", ""),
        behaviour=behaviour,
        axes=axes,
        variables=variables,
    )


def _build_conversation_payload(
    plan: ConversationPlan,
    turns: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Assemble the conversation payload for JSONL output."""
    return {
        "conversation_id": plan.scenario_id,
        "scenario_id": plan.scenario_id,
        "vertical": plan.vertical.value,
        "workflow": plan.workflow,
        "behaviours": [_behaviour_value(b) for b in plan.behaviours],
        "axes": dict(plan.axes),
        "turns": turns,
    }


def _coerce_behaviour(
    behaviour: Any,
    behaviours: Sequence[BehaviourFlag],
) -> str | None:
    """Pick a behaviour for template selection."""
    if isinstance(behaviour, BehaviourFlag):
        return behaviour.value
    if isinstance(behaviour, str):
        return behaviour
    if behaviours:
        return behaviours[0].value
    return None


def _behaviour_value(behaviour: BehaviourFlag) -> str:
    """Normalize BehaviourFlag for serialization."""
    return behaviour.value


def _write_jsonl(entries: Sequence[Dict[str, Any]], output_path: Path | str) -> None:
    """Write newline-delimited JSON to disk."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for entry in entries:
            handle.write(json.dumps(entry, ensure_ascii=False))
            handle.write("\n")
