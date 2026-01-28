from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class IndustryVertical(str, Enum):
    commerce = "commerce"
    banking = "banking"
    insurance = "insurance"
    healthcare = "healthcare"
    retail = "retail"
    telecom = "telecom"


class BehaviourFlag(str, Enum):
    happy_path = "HappyPath"
    constraint_heavy_queries = "ConstraintHeavyQueries"
    ambiguous_queries = "AmbiguousQueries"
    multi_turn_conversations = "MultiTurnConversations"
    user_corrections = "UserCorrections"
    adversarial_trap_queries = "AdversarialTrapQueries"
    impatient_user = "ImpatientUser"
    low_context = "LowContext"
    over_specified = "OverSpecified"
    emotionally_charged = "EmotionallyCharged"
    non_native_speaker = "NonNativeSpeaker"


class GenerationRequest(BaseModel):
    vertical: IndustryVertical
    workflows: List[str] = Field(min_length=1)
    behaviours: List[BehaviourFlag] = Field(default_factory=list)
    axes: Dict[str, str] = Field(default_factory=dict)
    num_samples_per_combo: int = Field(default=1, ge=1)
    language_locale: str = Field(default="en-US")
    channel: str = Field(default="web")
    random_seed: Optional[int] = None


class VerticalConfigResponse(BaseModel):
    vertical: IndustryVertical
    workflows: List[str]
    behaviours: List[str]
    axes: Dict[str, List[str]]


class ConversationPlan(BaseModel):
    vertical: IndustryVertical
    workflow: str
    scenario_id: str
    behaviours: List[BehaviourFlag] = Field(default_factory=list)
    axes: Dict[str, str] = Field(default_factory=dict)
    turn_plan: List[Dict[str, str]] = Field(default_factory=list)
