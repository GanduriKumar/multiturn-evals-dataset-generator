from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping

from .config_loader import load_vertical_templates
from .models import BehaviourFlag, IndustryVertical


@dataclass(frozen=True)
class TemplateCandidate:
    text: str
    workflow: str | None = None
    speaker: str | None = None
    role: str | None = None
    behaviour: str | None = None
    axes: Dict[str, Any] | None = None

    def match_score(
        self,
        workflow: str,
        speaker: str,
        role: str,
        behaviour: str | None,
        axes: Mapping[str, str],
    ) -> int | None:
        if self.workflow is not None and self.workflow != workflow:
            return None
        if self.speaker is not None and self.speaker != speaker:
            return None
        if self.role is not None and self.role != role:
            return None
        if self.behaviour is not None and behaviour is not None:
            if self.behaviour != behaviour:
                return None
        if self.behaviour is not None and behaviour is None:
            return None

        score = 0
        if self.workflow is not None:
            score += 1
        if self.speaker is not None:
            score += 1
        if self.role is not None:
            score += 1
        if self.behaviour is not None:
            score += 1
        if self.axes:
            for key, value in self.axes.items():
                if key not in axes:
                    return None
                if isinstance(value, list):
                    if axes[key] not in value:
                        return None
                elif axes[key] != value:
                    return None
                score += 1
        return score


class TemplateEngine:
    def __init__(self, templates: Dict[str, Any]) -> None:
        self._raw_templates = templates
        self._candidates = self._build_candidates(templates)

    @classmethod
    def from_vertical(cls, vertical: IndustryVertical | str) -> "TemplateEngine":
        templates = load_vertical_templates(vertical)
        return cls(templates)

    def realise_turn(
        self,
        *,
        vertical: IndustryVertical | str,
        workflow: str,
        speaker: str,
        role: str,
        behaviour: BehaviourFlag | str | None,
        axes: Mapping[str, str],
        variables: Mapping[str, Any] | None = None,
    ) -> str:
        behaviour_value = behaviour.value if isinstance(behaviour, BehaviourFlag) else behaviour
        selected = self._select_candidate(
            workflow=workflow,
            speaker=speaker,
            role=role,
            behaviour=behaviour_value,
            axes=axes,
        )
        if not selected:
            raise ValueError(
                "No template matched for "
                f"vertical={vertical}, workflow={workflow}, speaker={speaker}, "
                f"role={role}, behaviour={behaviour_value}, axes={dict(axes)}"
            )

        render_context: Dict[str, Any] = {
            "vertical": vertical.value if isinstance(vertical, IndustryVertical) else vertical,
            "workflow": workflow,
            "speaker": speaker,
            "role": role,
            "behaviour": behaviour_value,
            **axes,
        }
        if variables:
            render_context.update(variables)

        try:
            return selected.text.format(**render_context)
        except KeyError as exc:
            raise ValueError(
                f"Missing template variable: {exc} for template '{selected.text}'"
            ) from exc

    def _select_candidate(
        self,
        *,
        workflow: str,
        speaker: str,
        role: str,
        behaviour: str | None,
        axes: Mapping[str, str],
    ) -> TemplateCandidate | None:
        best_score = -1
        best_candidate: TemplateCandidate | None = None
        for candidate in self._candidates:
            score = candidate.match_score(workflow, speaker, role, behaviour, axes)
            if score is None:
                continue
            if score > best_score:
                best_score = score
                best_candidate = candidate
        return best_candidate

    def _build_candidates(self, templates: Dict[str, Any]) -> List[TemplateCandidate]:
        candidates: List[TemplateCandidate] = []
        for _, data in templates.items():
            for entry in self._extract_entries(data):
                text = (
                    entry.get("text")
                    or entry.get("utterance")
                    or entry.get("template")
                )
                if not text or not isinstance(text, str):
                    raise ValueError("Template entry missing text/utterance/template")
                candidates.append(
                    TemplateCandidate(
                        text=text,
                        workflow=entry.get("workflow"),
                        speaker=entry.get("speaker"),
                        role=entry.get("role"),
                        behaviour=entry.get("behaviour"),
                        axes=entry.get("axes") if isinstance(entry.get("axes"), dict) else None,
                    )
                )
        if not candidates:
            raise ValueError("No template candidates found in templates")
        return candidates

    def _extract_entries(self, data: Any) -> Iterable[Dict[str, Any]]:
        if data is None:
            return []
        if isinstance(data, list):
            return [entry for entry in data if isinstance(entry, dict)]
        if isinstance(data, dict):
            if "templates" in data and isinstance(data["templates"], list):
                return [entry for entry in data["templates"] if isinstance(entry, dict)]
        raise ValueError("Unsupported template structure; expected list or {templates: [...]}.")
