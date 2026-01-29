from __future__ import annotations

from app.main import _build_dataset_id
from app.models import BehaviourFlag, GenerationRequest, IndustryVertical


def _config() -> dict:
    return {
        "workflows": ["ReturnsRefunds", "PricingPromotions"],
        "behaviours": ["HappyPath", "AmbiguousQueries"],
        "axes": {
            "policy_boundary": ["within_policy", "outside_policy"],
            "availability": ["in_stock", "limited_stock"],
        },
    }


def _base_request() -> GenerationRequest:
    return GenerationRequest(
        vertical=IndustryVertical.commerce,
        workflows=["ReturnsRefunds", "PricingPromotions"],
        behaviours=[BehaviourFlag.happy_path, BehaviourFlag.ambiguous_queries],
        axes={
            "policy_boundary": ["within_policy", "outside_policy"],
            "availability": ["in_stock", "limited_stock"],
        },
        num_samples_per_combo=1,
        language_locale="en-US",
        channel="web",
        random_seed=None,
        min_turns=5,
        max_turns=9,
    )


def test_dataset_id_combined_when_all_selected() -> None:
    dataset_id, is_combined = _build_dataset_id(_base_request(), _config(), version="1.0.0")

    assert dataset_id == "commerce-combined-1.0.0"
    assert is_combined is True


def test_dataset_id_custom_when_partial_workflows() -> None:
    request = _base_request()
    request.workflows = ["ReturnsRefunds"]

    dataset_id, is_combined = _build_dataset_id(request, _config(), version="1.0.0")

    assert dataset_id.startswith("commerce-wf-returnsrefunds-")
    assert dataset_id.endswith("-1.0.0")
    assert "combined" not in dataset_id
    assert is_combined is False


def test_dataset_id_custom_when_partial_axes() -> None:
    request = _base_request()
    request.axes = {"policy_boundary": ["within_policy"]}

    dataset_id, is_combined = _build_dataset_id(request, _config(), version="1.0.0")

    assert "scn-policy-boundary-within-policy" in dataset_id
    assert is_combined is False
