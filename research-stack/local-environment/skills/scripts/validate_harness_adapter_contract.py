from __future__ import annotations

import json
import re
import sys
from pathlib import Path, PurePosixPath

try:
    from .envctl.schema_validation import collect_schema_document_errors, collect_schema_errors
    from .path_utils import CATALOG_ROOT, SCHEMAS_ROOT, SKILLS_ROOT
except ImportError:
    from envctl.schema_validation import collect_schema_document_errors, collect_schema_errors
    from path_utils import CATALOG_ROOT, SCHEMAS_ROOT, SKILLS_ROOT

ROOT = SKILLS_ROOT
CATALOG = CATALOG_ROOT
SCHEMAS = SCHEMAS_ROOT
ALLOWED_VARS = {"<run_id>", "<agent_id>", "<target_agent_id>"}
FORBIDDEN_WRITE_PREFIXES = [
    ".codex/dispatch/",
    ".codex/context-packets/",
    "outputs/agent-runs/",
    "logs/agent-handoffs/",
    "logs/quality-gates/",
    "logs/project-state/",
]
ALLOWED_RESERVED_PREFIXES = [
    ".codex/harness/",
    "logs/harness-adapter/",
]


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_template_path(path_value: str) -> str:
    if not isinstance(path_value, str) or not path_value.strip():
        raise ValueError("path-template-empty")
    if "\\" in path_value:
        raise ValueError("path-template-backslash")
    if path_value.startswith("/") or re.match(r"^[A-Za-z]:", path_value):
        raise ValueError("path-template-absolute")
    variables = set(re.findall(r"<[^>]+>", path_value))
    unknown = variables - ALLOWED_VARS
    if unknown:
        raise ValueError(f"path-template-unknown-vars:{sorted(unknown)}")
    normalized = str(
        PurePosixPath(
            path_value.replace("<run_id>", "RUN")
            .replace("<agent_id>", "AGENT")
            .replace("<target_agent_id>", "TARGET")
        )
    )
    if normalized == "." or normalized.startswith("../") or "/../" in normalized:
        raise ValueError("path-template-parent-reference")
    return normalized


def main() -> None:
    payload = load_json(CATALOG / "multi_agent_harness_adapter.json")
    schema = load_json(SCHEMAS / "multi_agent_harness_adapter.schema.json")
    modes = load_json(CATALOG / "agent_execution_modes.json")

    errors: list[str] = []
    warnings: list[str] = []
    errors.extend(collect_schema_document_errors(schema, "multi_agent_harness_adapter.schema.json"))
    errors.extend(collect_schema_errors(payload, schema, "multi_agent_harness_adapter.json"))

    if payload.get("status") != "reserved_interface_only":
        errors.append("adapter-status-must-be-reserved-interface-only")
    if payload.get("active_runtime") is not False:
        errors.append("adapter-active-runtime-must-be-false")

    reads = payload.get("reads", {})
    read_required = reads.get("required", [])
    read_optional = reads.get("optional", [])
    reserved_writes = payload.get("reserved_writes", {})
    must_not_mutate = payload.get("must_not_mutate", [])

    canonical = modes.get("canonical_paths", {})
    expected_required_reads = {
        canonical.get("dispatch_card"),
        canonical.get("context_packet"),
        canonical.get("handoff_log"),
        canonical.get("gate_log"),
        canonical.get("project_state_current"),
        canonical.get("project_state_history"),
        "logs/quality-gates/citation-verification-report.json",
        "logs/quality-gates/pipeline-status.json",
        "logs/quality-gates/writing-quality-report.json",
    }
    expected_optional_reads = {
        "material-passport.yaml",
        "evidence-ledger.yaml",
        "research-map.md",
        "findings-memory.md",
    }

    if set(read_required) != expected_required_reads:
        missing = sorted(expected_required_reads - set(read_required))
        extra = sorted(set(read_required) - expected_required_reads)
        if missing:
            errors.append(f"adapter-required-reads-missing:{missing}")
        if extra:
            errors.append(f"adapter-required-reads-extra:{extra}")
    if set(read_optional) != expected_optional_reads:
        missing = sorted(expected_optional_reads - set(read_optional))
        extra = sorted(set(read_optional) - expected_optional_reads)
        if missing:
            errors.append(f"adapter-optional-reads-missing:{missing}")
        if extra:
            errors.append(f"adapter-optional-reads-extra:{extra}")

    for label, path_value in reserved_writes.items():
        try:
            normalized = normalize_template_path(path_value)
        except ValueError as exc:
            errors.append(f"reserved-write-invalid:{label}:{exc}")
            continue
        if not any(normalized.startswith(prefix) for prefix in ALLOWED_RESERVED_PREFIXES):
            errors.append(f"reserved-write-outside-adapter-prefix:{label}:{path_value}")
        if any(normalized.startswith(prefix) for prefix in FORBIDDEN_WRITE_PREFIXES):
            errors.append(f"reserved-write-collides-with-canonical-prefix:{label}:{path_value}")

    for path_value in list(read_required) + list(read_optional) + list(must_not_mutate):
        try:
            normalize_template_path(path_value)
        except ValueError as exc:
            errors.append(f"adapter-path-invalid:{path_value}:{exc}")

    canonical_current = {
        canonical.get("dispatch_card"),
        canonical.get("context_packet"),
        canonical.get("agent_output_dir"),
        canonical.get("handoff_log"),
        canonical.get("gate_log"),
        canonical.get("project_state_current"),
        canonical.get("project_state_history"),
        "logs/quality-gates/citation-verification-report.json",
        "logs/quality-gates/pipeline-status.json",
        "logs/quality-gates/writing-quality-report.json",
        "material-passport.yaml",
        "evidence-ledger.yaml",
        "research-map.md",
        "findings-memory.md",
    }
    missing_must_not_mutate = sorted(canonical_current - set(must_not_mutate))
    if missing_must_not_mutate:
        errors.append(f"adapter-must-not-mutate-missing:{missing_must_not_mutate}")

    checkpoint = payload.get("checkpoint_contract", {})
    required_fields = checkpoint.get("required_fields", [])
    allowed_status = checkpoint.get("allowed_status", [])
    if not {"run_id", "agent_id", "status", "last_completed_step", "input_snapshot", "output_snapshot", "updated_at"}.issubset(set(required_fields)):
        errors.append("adapter-checkpoint-contract-missing-required-fields")
    if set(allowed_status) != {"pending", "running", "paused", "failed", "completed"}:
        errors.append("adapter-checkpoint-contract-status-set-invalid")

    bridge_rules = payload.get("bridge_rules", [])
    if len(bridge_rules) < 2:
        warnings.append("adapter-bridge-rules-too-thin")

    report = {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
