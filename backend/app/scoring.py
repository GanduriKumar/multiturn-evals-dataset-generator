from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Mapping, Sequence


def score_dataset(
    golden_entries: Sequence[Mapping[str, Any]],
    model_entries: Sequence[Mapping[str, Any]],
) -> List[Dict[str, Any]]:
    """Score a dataset by aligning conversations and applying heuristics."""
    model_index = _index_model_entries(model_entries)
    results: List[Dict[str, Any]] = []
    for golden in golden_entries:
        conversation_id = _conversation_id(golden)
        model = model_index.get(conversation_id)
        results.append(score_conversation(golden, model))
    return results


def score_conversation(
    golden: Mapping[str, Any],
    model: Mapping[str, Any] | None,
) -> Dict[str, Any]:
    """Score a single conversation using heuristic rules."""
    conversation_id = _conversation_id(golden)
    model_text = _extract_model_text(model) if model else ""

    expected_actions = golden.get("expected_actions", [])
    key_facts = golden.get("key_facts", {})
    scoring_rules = golden.get("scoring_rules", {})

    actions_result = score_expected_actions(expected_actions, model_text)
    facts_result = score_key_facts(key_facts, model_text)
    policy_result = score_policy_violations(scoring_rules, model_text)

    overall_pass = (
        actions_result["all_matched"]
        and facts_result["all_matched"]
        and policy_result["violation_count"] == 0
    )

    return {
        "conversation_id": conversation_id,
        "overall_pass": overall_pass,
        "expected_actions": actions_result,
        "key_facts": facts_result,
        "policy_violations": policy_result,
        "model_text_present": bool(model_text),
    }


def score_expected_actions(
    expected_actions: Iterable[Any],
    model_text: str,
) -> Dict[str, Any]:
    """Check whether expected actions appear in the model output text."""
    actions = [str(action) for action in expected_actions if action is not None]
    matched = [action for action in actions if _contains_text(model_text, action)]
    missed = [action for action in actions if action not in matched]
    return {
        "total": len(actions),
        "matched": matched,
        "missed": missed,
        "all_matched": len(missed) == 0,
    }


def score_key_facts(
    key_facts: Mapping[str, Any],
    model_text: str,
) -> Dict[str, Any]:
    """Check whether key fact values appear in the model output text."""
    facts = {str(key): str(value) for key, value in key_facts.items()}
    matched = [key for key, value in facts.items() if _contains_text(model_text, value)]
    missed = [key for key in facts if key not in matched]
    return {
        "total": len(facts),
        "matched": matched,
        "missed": missed,
        "all_matched": len(missed) == 0,
    }


def score_policy_violations(
    scoring_rules: Mapping[str, Any],
    model_text: str,
) -> Dict[str, Any]:
    """Detect disallowed phrases based on policy rules."""
    disallowed = scoring_rules.get("disallowed_phrases", [])
    phrases = [str(item) for item in disallowed if item is not None]
    violations = [phrase for phrase in phrases if _contains_text(model_text, phrase)]
    return {
        "violation_count": len(violations),
        "violations": violations,
    }


def _index_model_entries(
    model_entries: Sequence[Mapping[str, Any]],
) -> Dict[str, Mapping[str, Any]]:
    """Index model entries by conversation id."""
    index: Dict[str, Mapping[str, Any]] = {}
    for entry in model_entries:
        index[_conversation_id(entry)] = entry
    return index


def _conversation_id(entry: Mapping[str, Any]) -> str:
    """Resolve a conversation identifier from common keys."""
    return str(
        entry.get("conversation_id")
        or entry.get("scenario_id")
        or entry.get("id")
        or ""
    )


def _extract_model_text(model: Mapping[str, Any] | None) -> str:
    """Extract a unified text string from a model output entry."""
    if not model:
        return ""

    for key in ("text", "output", "response", "model_output"):
        value = model.get(key)
        if isinstance(value, str) and value.strip():
            return value

    turns = model.get("turns")
    if isinstance(turns, list):
        parts: List[str] = []
        for turn in turns:
            if not isinstance(turn, Mapping):
                continue
            if turn.get("speaker") in {"assistant", "agent"}:
                text = turn.get("text") or turn.get("output")
                if isinstance(text, str):
                    parts.append(text)
        return " ".join(parts)

    return ""


def _contains_text(haystack: str, needle: str) -> bool:
    """Case-insensitive substring match with whitespace normalization."""
    if not haystack or not needle:
        return False
    return re.sub(r"\s+", " ", needle.strip().lower()) in re.sub(
        r"\s+", " ", haystack.lower()
    )
