from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence

from .models import BehaviourFlag, ConversationPlan, GoldenDataset, GoldenEntry, GoldenTurnExpectation
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


def build_golden_dataset(
    plans: Sequence[ConversationPlan],
    template_engine: TemplateEngine,
    config: Mapping[str, Any],
    dataset_id: str = "",
    version: str = "1.0.0",
) -> GoldenDataset:
    """Build golden dataset with evaluation expectations."""
    entries: List[GoldenEntry] = []
    
    for plan in plans:
        # Determine which turn to evaluate (typically last assistant turn)
        num_turns = len(plan.turn_plan)
        eval_turn_index = num_turns - 1  # Last turn (0-indexed)
        
        # Get expected response variants based on policy_boundary
        policy_boundary = plan.axes.get("policy_boundary", "within_policy")
        expected_responses = _get_expected_responses(
            plan.workflow,
            policy_boundary,
            config,
        )
        
        # Determine outcome based on policy_boundary
        decision = "DENY" if "outside" in policy_boundary else "ALLOW"
        
        entry = GoldenEntry(
            conversation_id=plan.scenario_id,
            turns=[
                GoldenTurnExpectation(
                    turn_index=eval_turn_index,
                    expected={"variants": expected_responses},
                )
            ],
            final_outcome={"decision": decision},
            constraints={"respect_policy": True},
        )
        entries.append(entry)
    
    # Generate dataset_id if not provided
    if not dataset_id and plans:
        vertical = plans[0].vertical.value
        dataset_id = f"{vertical}-combined-{version}"
    
    return GoldenDataset(
        dataset_id=dataset_id,
        version=version,
        entries=entries,
    )


def _get_expected_responses(
    workflow: str,
    policy_boundary: str,
    config: Mapping[str, Any],
) -> List[str]:
    """Get expected response variants from config."""
    workflows_config = config.get("workflows_config", {})
    workflow_data = workflows_config.get(workflow, {})
    expected_responses_config = workflow_data.get("expected_responses", {})
    
    # Get responses for the specific policy boundary
    boundary_config = expected_responses_config.get(policy_boundary, {})
    variants = boundary_config.get("variants", [])
    
    if variants:
        return variants
    
    # Fallback to generic response
    return [
        "I can help you with that request according to our policy."
    ]


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
                "role": "user",
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
                    "role": "user",
                    "text": text,
                }
            )
        else:
            turns.append(
                {
                    "role": "assistant",
                    "text": text,
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
    """Assemble the conversation payload for JSON output."""
    return {
        "conversation_id": plan.scenario_id,
        "metadata": {
            "domain_label": plan.domain_label,
            "behavior": plan.behavior_label,
            "axes": dict(plan.axes),
            "policy_excerpt": plan.policy_excerpt,
            "facts_bullets": plan.facts_bullets,
            "short_description": plan.short_description,
        },
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
