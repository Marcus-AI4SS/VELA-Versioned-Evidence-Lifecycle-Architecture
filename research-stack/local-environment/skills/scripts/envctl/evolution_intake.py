from __future__ import annotations

import hashlib
import json
import os
import re
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

try:
    from ..path_utils import CATALOG_ROOT, OUTPUTS_ROOT, REPO_ROOT, SCHEMAS_ROOT, SKILLS_ROOT
    from .schema_validation import collect_schema_errors, load_json
except ImportError:  # pragma: no cover
    from path_utils import CATALOG_ROOT, OUTPUTS_ROOT, REPO_ROOT, SCHEMAS_ROOT, SKILLS_ROOT
    from envctl.schema_validation import collect_schema_errors, load_json


POLICY_PATH = CATALOG_ROOT / "evolution_intake_policy.json"
POLICY_SCHEMA_PATH = SCHEMAS_ROOT / "evolution_intake_policy.v1.schema.json"
REPORT_SCHEMA_PATH = SCHEMAS_ROOT / "evolution_intake_report.v1.schema.json"
BACKLOG_PATH = CATALOG_ROOT / "evolution_backlog.json"
PROJECT_MARKERS = {
    "project.yaml",
    "research-map.md",
    "findings-memory.md",
    "material-passport.yaml",
    "evidence-ledger.yaml",
    "AGENTS.md",
}


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _iso_from_timestamp(value: float) -> str:
    return datetime.fromtimestamp(value, timezone.utc).replace(microsecond=0).isoformat()


def _repo_relative_or_absolute(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(REPO_ROOT.resolve())).replace("\\", "/")
    except ValueError:
        return str(resolved).replace("\\", "/")


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip()).lower()


def _fingerprint(project_root: Path, text: str) -> str:
    base = f"{str(project_root.resolve()).lower()}\n{_normalize_text(text)}"
    return hashlib.sha256(base.encode("utf-8", errors="replace")).hexdigest()


def _slug(value: str, fallback: str = "item") -> str:
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "-", value).strip("-").lower()
    return slug[:80] or fallback


def load_policy(path: Path | None = None) -> dict[str, Any]:
    policy_path = path or POLICY_PATH
    policy = load_json(policy_path)
    schema = load_json(POLICY_SCHEMA_PATH)
    errors = collect_schema_errors(policy, schema, "evolution_intake_policy")
    if errors:
        raise ValueError("; ".join(errors))
    return policy


def resolve_scan_roots(policy: dict[str, Any], explicit_roots: Iterable[Path] | None = None) -> list[Path]:
    if explicit_roots:
        candidates = [Path(root).expanduser() for root in explicit_roots]
    else:
        candidates = [
            Path(item["path"]).expanduser()
            for item in policy.get("scan_roots", [])
            if isinstance(item, dict) and item.get("enabled") is True
        ]
    roots: list[Path] = []
    for candidate in candidates:
        try:
            resolved = candidate.resolve()
        except OSError:
            continue
        if resolved.exists() and resolved not in roots:
            roots.append(resolved)
    return roots


def _is_excluded_dir(path: Path, excluded: set[str]) -> bool:
    normalized = str(path).replace("\\", "/")
    name = path.name
    if name in excluded:
        return True
    return any(item in normalized for item in excluded if "/" in item)


def iter_candidate_files(
    roots: Iterable[Path],
    source_file_names: Iterable[str],
    excluded_dir_names: Iterable[str],
) -> Iterable[Path]:
    target_names = set(source_file_names)
    excluded = set(excluded_dir_names)
    for root in roots:
        if not root.exists():
            continue
        for current, dirs, files in os.walk(root):
            current_path = Path(current)
            dirs[:] = [
                dirname
                for dirname in dirs
                if not _is_excluded_dir(current_path / dirname, excluded)
            ]
            for filename in files:
                if filename in target_names:
                    yield current_path / filename


def _infer_project_root(path: Path) -> Path:
    parent = path.parent.resolve()
    for candidate in [parent, *parent.parents]:
        if any((candidate / marker).exists() for marker in PROJECT_MARKERS):
            return candidate
        if candidate.parent == candidate:
            break
    return parent


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _extract_title_and_snippet(text: str) -> tuple[str, str]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    title = ""
    for line in lines:
        if line.startswith("#"):
            title = line.lstrip("#").strip()
            break
    if not title and lines:
        title = lines[0]
    if not title:
        title = "Untitled evolution signal"
    snippet = " ".join(lines[:4])[:360] or title
    return title[:160], snippet


def classify_item(text: str, source_file: Path, policy: dict[str, Any]) -> dict[str, Any]:
    searchable = f"{source_file.name}\n{text}".lower()
    matched: list[dict[str, Any]] = []
    for rule in policy.get("risk_rules", []):
        keywords = [str(item) for item in rule.get("keywords", [])]
        hits = [keyword for keyword in keywords if keyword.lower() in searchable]
        if hits:
            matched.append({**rule, "hits": hits})
    if not matched:
        fallback = {
            "id": "unclassified",
            "risk_level": "low",
            "severity": "p3",
            "recommended_action": "backlog_candidate",
            "proposed_target": "docs",
            "hits": ["unclassified"],
        }
        matched.append(fallback)
    priority = {"high": 0, "medium": 1, "low": 2}
    selected = sorted(matched, key=lambda item: priority[item["risk_level"]])[0]
    return {
        "risk_level": selected["risk_level"],
        "severity": selected["severity"],
        "recommended_action": selected["recommended_action"],
        "proposed_target": selected["proposed_target"],
        "signals": [f"{selected['id']}:{hit}" for hit in selected.get("hits", [])],
    }


def build_evolution_intake_report(
    scan_roots: Iterable[Path] | None = None,
    lookback_days: int | None = None,
    policy_path: Path | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    policy = load_policy(policy_path)
    resolved_roots = resolve_scan_roots(policy, scan_roots)
    effective_days = int(lookback_days or policy["default_lookback_days"])
    current_time = now or _utc_now()
    cutoff = current_time - timedelta(days=effective_days)

    items: list[dict[str, Any]] = []
    for path in iter_candidate_files(
        resolved_roots,
        policy["source_file_names"],
        policy["excluded_dir_names"],
    ):
        try:
            modified_at = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).replace(microsecond=0)
        except OSError:
            continue
        if modified_at < cutoff:
            continue
        try:
            text = _read_text(path)
        except OSError:
            continue
        project_root = _infer_project_root(path)
        title, snippet = _extract_title_and_snippet(text)
        classification = classify_item(text, path, policy)
        fingerprint = _fingerprint(project_root, text)
        item_id = f"{modified_at.date().isoformat()}-{_slug(project_root.name)}-{path.stem}-{fingerprint[:10]}"
        items.append(
            {
                "id": item_id,
                "project_root": _repo_relative_or_absolute(project_root),
                "source_file": _repo_relative_or_absolute(path),
                "source_file_name": path.name,
                "modified_at": modified_at.isoformat(),
                "title": title,
                "snippet": snippet,
                **classification,
                "fingerprint": fingerprint,
            }
        )

    items.sort(key=lambda item: (item["modified_at"], item["source_file"]), reverse=True)
    counts = Counter(item["recommended_action"] for item in items)
    fingerprints = Counter(item["fingerprint"] for item in items)
    duplicate_groups = [
        {
            "fingerprint": fingerprint,
            "count": count,
            "source_files": sorted(
                item["source_file"] for item in items if item["fingerprint"] == fingerprint
            ),
        }
        for fingerprint, count in sorted(fingerprints.items())
        if count > 1
    ]
    return {
        "schema_version": "evolution_intake_report.v1",
        "generated_at": current_time.isoformat(),
        "mode": policy["default_mode"],
        "source_files_written": False,
        "lookback_days": effective_days,
        "scan_roots": [str(root).replace("\\", "/") for root in resolved_roots],
        "candidate_count": len(items),
        "recommendation_counts": dict(sorted(counts.items())),
        "items": items,
        "duplicate_groups": duplicate_groups,
        "next_actions": [
            "Review high-risk runtime or configuration signals manually.",
            "Automation may append observed candidates to evolution_backlog.json, but must not mutate skills, MCP, plugin, runtime cache, or user config directly.",
            "Run validate memory, validate cybernetics, and validate stack before turning backlog items into source changes."
        ],
    }


def validate_report(report: dict[str, Any]) -> list[str]:
    return collect_schema_errors(report, load_json(REPORT_SCHEMA_PATH), "evolution_intake_report")


def _render_markdown_report(report: dict[str, Any]) -> str:
    lines = [
        "# 自适应演化输入报告",
        "",
        f"- generated_at: `{report['generated_at']}`",
        f"- mode: `{report['mode']}`",
        f"- source_files_written: `{report['source_files_written']}`",
        f"- lookback_days: `{report['lookback_days']}`",
        f"- candidate_count: `{report['candidate_count']}`",
        "",
        "## Scan Roots",
        "",
    ]
    lines.extend(f"- `{root}`" for root in report["scan_roots"])
    lines.extend(["", "## Candidates", ""])
    if not report["items"]:
        lines.append("No project retrospective or environment-change proposal files were found in the lookback window.")
    else:
        lines.extend(
            [
                "| Risk | Action | Target | Source | Title |",
                "| --- | --- | --- | --- | --- |",
            ]
        )
        for item in report["items"]:
            title = item["title"].replace("|", "\\|")
            source = item["source_file"].replace("|", "\\|")
            lines.append(
                f"| `{item['risk_level']}` | `{item['recommended_action']}` | "
                f"`{item['proposed_target']}` | `{source}` | {title} |"
            )
    lines.extend(["", "## Next Actions", ""])
    lines.extend(f"- {action}" for action in report["next_actions"])
    lines.append("")
    return "\n".join(lines)


def write_evolution_intake_report(report: dict[str, Any], output: Path | None = None) -> tuple[Path, Path]:
    if output is None:
        date = datetime.now().strftime("%Y-%m-%d")
        output = OUTPUTS_ROOT / "reports" / "evolution-intake" / f"{date}.md"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(_render_markdown_report(report), encoding="utf-8")
    json_output = output.with_suffix(".json")
    json_output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return output, json_output


def _event_from_item(item: dict[str, Any]) -> dict[str, Any]:
    observed_at = item["modified_at"].split("T", 1)[0]
    return {
        "id": f"{observed_at}-intake-{item['fingerprint'][:12]}",
        "observed_at": observed_at,
        "source": item["source_file"],
        "signal_type": "daily_audit",
        "severity": item["severity"],
        "description": f"{item['title']} :: {item['snippet'][:220]}",
        "proposed_target": item["proposed_target"],
        "controller": "project-retrospective-evolver",
        "required_gates": [
            "envctl validate memory",
            "envctl validate cybernetics",
            "validate_research_stack"
        ],
        "status": "observed",
        "rollback": "Remove this observed intake event from evolution_backlog.json if manual review rejects it."
    }


def append_report_items_to_backlog(
    report: dict[str, Any],
    backlog_path: Path | None = None,
) -> dict[str, Any]:
    target = backlog_path or BACKLOG_PATH
    original = target.read_text(encoding="utf-8")
    backlog = load_json(target)
    events = backlog.setdefault("events", [])
    existing_ids = {item.get("id") for item in events if isinstance(item, dict)}
    added: list[str] = []
    skipped: list[str] = []
    for item in report["items"]:
        event = _event_from_item(item)
        if event["id"] in existing_ids:
            skipped.append(event["id"])
            continue
        events.append(event)
        existing_ids.add(event["id"])
        added.append(event["id"])
    if added:
        backlog["generated_at"] = datetime.now().date().isoformat()
        target.write_text(json.dumps(backlog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        errors = collect_schema_errors(backlog, load_json(SCHEMAS_ROOT / "evolution_event.v1.schema.json"), "evolution_backlog")
        if errors:
            target.write_text(original, encoding="utf-8")
            raise ValueError("; ".join(errors))
    return {
        "backlog_path": _repo_relative_or_absolute(target),
        "added": added,
        "skipped_existing": skipped,
        "source_file_written": bool(added),
    }
