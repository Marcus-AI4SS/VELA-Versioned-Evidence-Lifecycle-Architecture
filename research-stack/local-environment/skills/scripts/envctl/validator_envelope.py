from __future__ import annotations

from typing import Any


SCHEMA_VERSION = "validator_result.v1"
DECISIONS = {"pass", "needs_review", "fail"}


def decision_from_errors(errors: list[str], *, needs_review: bool = False) -> str:
    if errors:
        return "fail"
    if needs_review:
        return "needs_review"
    return "pass"


def build_validator_result(
    *,
    validator: str,
    scope: str,
    errors: list[str] | None = None,
    warnings: list[str] | None = None,
    details: dict[str, Any] | None = None,
    decision: str | None = None,
    compatibility: dict[str, Any] | None = None,
) -> dict[str, Any]:
    normalized_errors = list(errors or [])
    normalized_warnings = list(warnings or [])
    normalized_decision = decision or decision_from_errors(normalized_errors)
    if normalized_decision not in DECISIONS:
        raise ValueError(f"invalid validator decision: {normalized_decision}")
    envelope: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "validator": validator,
        "scope": scope,
        "ok": normalized_decision == "pass",
        "decision": normalized_decision,
        "errors": normalized_errors,
        "warnings": normalized_warnings,
        "details": details or {},
    }
    if compatibility:
        envelope.update(compatibility)
    return envelope


def exit_code_for_result(result: dict[str, Any]) -> int:
    return 0 if result.get("ok") is True else 1
