from __future__ import annotations

import hashlib
import random
from itertools import product
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


def _generate_conversation_id(
    domain_label: str,
    behavior_label: str,
    axes: Mapping[str, str],
    workflow: str,
) -> str:
    """Generate conversation ID in format: domain.behavior.axes_key=value,....hash"""
    # Convert domain and behavior to URL-safe format
    domain_slug = domain_label.lower().replace(" ", "-").replace("/", "-")
    behavior_slug = behavior_label.lower().replace(" ", "-").replace("/", "-")
    
    # Build axes string
    sorted_axes = sorted(axes.items())
    axes_str = ",".join(f"{k}={v}" for k, v in sorted_axes)
    
    # Generate hash from workflow + axes for uniqueness
    hash_input = f"{workflow}:{axes_str}".encode("utf-8")
    hash_suffix = hashlib.sha256(hash_input).hexdigest()[:10]
    
    return f"{domain_slug}.{behavior_slug}.{axes_str}.{hash_suffix}"


def _get_domain_label(vertical: str, workflow: str, config: Mapping[str, Any]) -> str:
    """Get human-readable domain label from config."""
    workflows_config = config.get("workflows_config", {})
    workflow_data = workflows_config.get(workflow, {})
    return workflow_data.get("domain_label", vertical.title())


def _get_behavior_label(workflow: str, config: Mapping[str, Any]) -> str:
    """Get human-readable behavior label from config."""
    workflows_config = config.get("workflows_config", {})
    workflow_data = workflows_config.get(workflow, {})
    return workflow_data.get("label", workflow.replace("_", " ").title())


def _get_policy_excerpt(workflow: str, config: Mapping[str, Any]) -> str:
    """Get policy excerpt from config."""
    workflows_config = config.get("workflows_config", {})
    workflow_data = workflows_config.get(workflow, {})
    return workflow_data.get("policy_excerpt", "")


def _generate_facts_bullets(
    workflow: str,
    axes: Mapping[str, str],
    config: Mapping[str, Any],
) -> str:
    """Generate facts bullets based on axes values."""
    workflows_config = config.get("workflows_config", {})
    workflow_data = workflows_config.get(workflow, {})
    facts_template = workflow_data.get("facts_template", "")
    
    if not facts_template:
        # Generate default facts from axes
        facts = []
        for key, value in sorted(axes.items()):
            facts.append(f"- {key.replace('_', ' ').title()}: {value}")
        return "\n".join(facts)
    
    # Use template if available with default values
    context = dict(axes)
    context["workflow"] = workflow
    context.setdefault("delivery_days", "20")
    context.setdefault("quantity", "1")
    return _safe_format(facts_template, context)


def _generate_short_description(
    behavior_label: str,
    axes: Mapping[str, str],
) -> str:
    """Generate short description of the conversation scenario."""
    axes_str = ", ".join(f"'{k}': '{v}'" for k, v in sorted(axes.items()))
    return f"{behavior_label} with axes {{{axes_str}}}"


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
    axes: Mapping[str, Sequence[str]],
    config_axes: Mapping[str, Sequence[str]],
) -> Dict[str, list[str]]:
    if axes:
        return {key: list(values) for key, values in axes.items()}
    defaults: Dict[str, list[str]] = {}
    for key, values in config_axes.items():
        if values:
            defaults[key] = [values[0]]
    return defaults


def _normalize_axes_options(
    axes: Mapping[str, Sequence[str]],
    config_axes: Mapping[str, Sequence[str]],
) -> Dict[str, list[str]]:
    if axes:
        normalized: Dict[str, list[str]] = {}
        for key, values in axes.items():
            if isinstance(values, str):
                normalized[key] = [values]
            else:
                normalized[key] = [value for value in values if value]
        return normalized
    return _default_axes(axes, config_axes)


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
    axes_options = _normalize_axes_options(request.axes, config.get("axes", {}))

    if axes_options:
        axes_keys = list(axes_options.keys())
        axes_combinations = [
            dict(zip(axes_keys, combo, strict=False))
            for combo in product(*(axes_options[key] for key in axes_keys))
        ]
    else:
        axes_combinations = [{}]

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
            for axes in axes_combinations:
                for _ in range(request.num_samples_per_combo):
                    counter += 1

                    # Get metadata from config
                    domain_label = _get_domain_label(vertical_key, workflow, config)
                    behavior_label = _get_behavior_label(workflow, config)
                    policy_excerpt = _get_policy_excerpt(workflow, config)
                    facts_bullets = _generate_facts_bullets(workflow, axes, config)
                    short_description = _generate_short_description(behavior_label, axes)

                    # Generate new conversation ID format
                    scenario_id = _generate_conversation_id(
                        domain_label=domain_label,
                        behavior_label=behavior_label,
                        axes=axes,
                        workflow=workflow,
                    )

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
                            domain_label=domain_label,
                            behavior_label=behavior_label,
                            policy_excerpt=policy_excerpt,
                            facts_bullets=facts_bullets,
                            short_description=short_description,
                        )
                    )

    manifest = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "vertical": vertical_key,
        "workflows": list(request.workflows),
        "behaviours": [b.value for b in behaviours],
        "axes": axes_options,
        "num_samples_per_combo": request.num_samples_per_combo,
        "language_locale": request.language_locale,
        "channel": request.channel,
        "random_seed": request.random_seed,
        "total_conversations": len(plans),
    }

    return plans, manifest
