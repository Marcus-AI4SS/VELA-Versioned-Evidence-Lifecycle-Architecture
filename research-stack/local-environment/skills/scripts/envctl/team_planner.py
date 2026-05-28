from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    from ..path_utils import CATALOG_ROOT
except ImportError:  # pragma: no cover
    from pathlib import Path as _Path
    import sys as _sys

    _sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))
    from path_utils import CATALOG_ROOT


REVIEWER_AGENT_IDS = {"reviewer"}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_research_team_playbooks(catalog_root: Path = CATALOG_ROOT) -> dict[str, Any]:
    path = catalog_root / "research_team_playbooks.json"
    if not path.exists():
        return {"playbooks": []}
    return load_json(path)


def load_route_playbook(route_id: str, catalog_root: Path = CATALOG_ROOT) -> dict[str, Any] | None:
    payload = load_research_team_playbooks(catalog_root)
    for playbook in payload.get("playbooks", []):
        if playbook.get("route_id") == route_id:
            return playbook
    return None


def _as_set(card: dict[str, Any], key: str) -> set[str]:
    return set(card.get(key) or [])


def _condition_group_matches(card: dict[str, Any], group: dict[str, Any]) -> bool:
    if "route_id_is" in group and card.get("route_id") not in set(group["route_id_is"]):
        return False
    if "work_units_contains_any" in group and not (_as_set(card, "work_units") & set(group["work_units_contains_any"])):
        return False
    if "deliverable_types_contains_any" in group and not (_as_set(card, "deliverable_types") & set(group["deliverable_types_contains_any"])):
        return False
    if "sync_targets_contains_any" in group and not (_as_set(card, "sync_targets") & set(group["sync_targets_contains_any"])):
        return False
    if "explicit_project_mode_is" in group and card.get("explicit_project_mode") not in set(group["explicit_project_mode_is"]):
        return False
    if "target_item_count_gte" in group and int(card.get("target_item_count") or 0) < int(group["target_item_count_gte"]):
        return False
    if "target_item_count_gt" in group and int(card.get("target_item_count") or 0) <= int(group["target_item_count_gt"]):
        return False
    if "needs_clarification_is" in group and bool(card.get("needs_clarification")) is not bool(group["needs_clarification_is"]):
        return False
    return True


def include_when_matches(card: dict[str, Any], include_when: dict[str, Any]) -> bool:
    return any(_condition_group_matches(card, group) for group in include_when.get("any_of", []))


def pick_producers(route_id: str, card: dict[str, Any], team_playbook: dict[str, Any] | None = None) -> list[str]:
    if team_playbook is None:
        team_playbook = load_route_playbook(route_id)

    selected: list[str] = []

    def add(agent_id: str) -> None:
        if agent_id not in REVIEWER_AGENT_IDS and agent_id not in selected:
            selected.append(agent_id)

    if team_playbook is None:
        add("project-manager")
        return selected

    for agent_id in team_playbook.get("default_agents", []):
        add(agent_id)
    for optional_agent in team_playbook.get("optional_agents", []):
        if include_when_matches(card, optional_agent.get("include_when", {})):
            add(optional_agent["agent_id"])
    if not selected:
        add("project-manager")
    return selected


def build_review_pairs(
    route_id: str,
    producers: list[str],
    available_agents: dict[str, dict[str, Any]],
    team_playbook: dict[str, Any] | None = None,
) -> tuple[list[str], dict[str, str], list[str]]:
    reviewers: list[str] = []
    review_pairs: dict[str, str] = {}
    excluded: list[str] = []

    def add_pair(producer: str, reviewer: str) -> None:
        if producer not in producers:
            return
        if reviewer not in available_agents:
            if reviewer not in excluded:
                excluded.append(reviewer)
            return
        if reviewer not in reviewers:
            reviewers.append(reviewer)
        review_pairs[producer] = reviewer

    if team_playbook is not None:
        for item in team_playbook.get("review_chain", []):
            add_pair(item["producer"], item["reviewer"])

    default_reviewer = "reviewer"
    for producer in producers:
        if producer not in review_pairs:
            add_pair(producer, default_reviewer)

    return reviewers, review_pairs, excluded
