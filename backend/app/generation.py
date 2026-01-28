from __future__ import annotations

import random
from datetime import datetime
from string import Formatter
from typing import Any, Dict, Iterable, Mapping, Sequence

from .config_loader import load_vertical_config
from .models import BehaviourFlag, ConversationPlan, GenerationRequest
from .template_engine import TemplateEngine


class _SafeDict(dict[str, Any]):
    def __missing__(self, key: str) -> str:
        return f"<{key}>"


def _safe_format(template: str, values: Mapping[str, Any]) -> str:
    return template.format_map(_SafeDict(values))


def _extract_placeholders(template: str) -> Iterable[str]:
    formatter = Formatter()
    for _, field_name, _, _ in formatter.parse(template):
        if field_name:
            yield field_name


def _coerce_behaviour_list(
    behaviours: Sequence[BehaviourFlag],
    fallback_values: Sequence[str],
) -> list[BehaviourFlag]:
    if behaviours:
        return list(behaviours)
    for value in fallback_values:
        try:
            return [BehaviourFlag(value)]
        except ValueError:
            continue
    return []


def _default_axes(
    axes: Mapping[str, str],
    config_axes: Mapping[str, Sequence[str]],
) -> Dict[str, str]:
    if axes:
        return dict(axes)
    defaults: Dict[str, str] = {}
    for key, values in config_axes.items():
        if values:
            defaults[key] = values[0]
    return defaults


def _render_turn_text(
    template_engine: TemplateEngine,
    *,
    vertical: str,
    workflow: str,
    behaviour: str | None,
    axes: Mapping[str, str],
    variables: Mapping[str, Any],
) -> str:
    candidate = template_engine.select_candidate(
        workflow=workflow,
        speaker="user",
        role="customer",
        behaviour=behaviour,
        axes=axes,
    )
    if candidate is None:
        return f"{workflow} request from user."

    render_context: Dict[str, Any] = {
        "vertical": vertical,
        "workflow": workflow,
        "speaker": "user",
        "role": "customer",
        "behaviour": behaviour,
        **axes,
        **variables,
    }

    for placeholder in _extract_placeholders(candidate.text):
        if placeholder not in render_context:
            render_context[placeholder] = f"{placeholder}"

    return _safe_format(candidate.text, render_context)


def _build_multi_turn_plan(
    *,
    vertical_key: str,
    workflow: str,
    behaviour_value: str | None,
    axes: Mapping[str, str],
    template_engine: TemplateEngine,
    variables: Mapping[str, Any],
    num_turns: int = 3,
) -> list[Dict[str, Any]]:
    """Build a multi-turn conversation plan with multiple user turns and agent responses."""
    turn_plan: list[Dict[str, Any]] = []
    
    agent_responses = [
        "I can help you with that.",
        "Let me check that for you.",
        "I've processed your request.",
        "Thank you for providing that information.",
        "I understand your concern.",
        "I'm looking into that now.",
        "That's a great question.",
        "I can certainly assist you.",
    ]
    
    # Generate turns in alternating user-agent pattern
    for turn_index in range(num_turns):
        if turn_index % 2 == 0:
            # User turn - generate distinct utterance for each user turn
            text = _render_turn_text(
                template_engine,
                vertical=vertical_key,
                workflow=workflow,
                behaviour=behaviour_value,
                axes=axes,
                variables=variables,
            )
            turn_plan.append({
                "speaker": "user",
                "role": "customer",
                "behaviour": behaviour_value,
                "axes": dict(axes),
                "text": text,
            })
        else:
            # Assistant turn with expected response
            response_idx = turn_index // 2
            response_text = agent_responses[response_idx % len(agent_responses)]
            turn_plan.append({
                "speaker": "assistant",
                "role": "agent",
                "text": response_text,
            })
    
    return turn_plan


def build_conversation_plans(request: GenerationRequest) -> tuple[list[ConversationPlan], dict]:
    vertical_key = request.vertical.value
    config = load_vertical_config(request.vertical)

    behaviours = _coerce_behaviour_list(request.behaviours, config.get("behaviours", []))
    axes = _default_axes(request.axes, config.get("axes", {}))

    rng = random.Random(request.random_seed or 0)
    template_engine = TemplateEngine.from_vertical(request.vertical)

    plans: list[ConversationPlan] = []
    counter = 0

    for workflow in request.workflows:
        if behaviours:
            behaviour_iter = behaviours
        else:
            behaviour_iter = [None]

        for behaviour in behaviour_iter:
            for _ in range(request.num_samples_per_combo):
                counter += 1
                scenario_id = f"{vertical_key}-{workflow}-{counter:04d}"
                behaviour_value = behaviour.value if isinstance(behaviour, BehaviourFlag) else None
                variables = {
                    "channel": request.channel,
                    "language_locale": request.language_locale,
                    "customer_name": "Customer",
                }
                
                turn_plan = _build_multi_turn_plan(
                    vertical_key=vertical_key,
                    workflow=workflow,
                    behaviour_value=behaviour_value,
                    axes=axes,
                    template_engine=template_engine,
                    variables=variables,
                    num_turns=rng.randint(request.min_turns, request.max_turns),
                )
                
                plans.append(
                    ConversationPlan(
                        vertical=request.vertical,
                        workflow=workflow,
                        scenario_id=scenario_id,
                        behaviours=[behaviour] if isinstance(behaviour, BehaviourFlag) else [],
                        axes=axes,
                        turn_plan=turn_plan,
                    )
                )

    manifest = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "vertical": vertical_key,
        "workflows": list(request.workflows),
        "behaviours": [b.value for b in behaviours],
        "axes": axes,
        "num_samples_per_combo": request.num_samples_per_combo,
        "language_locale": request.language_locale,
        "channel": request.channel,
        "random_seed": request.random_seed,
        "total_conversations": len(plans),
    }

    return plans, manifest
