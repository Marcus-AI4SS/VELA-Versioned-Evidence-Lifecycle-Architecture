from __future__ import annotations



import json

from pathlib import Path

from typing import Any



from jsonschema import Draft202012Validator, exceptions



try:  # Optional dependency for YAML handoff packets.

    import yaml

except ImportError:  # pragma: no cover - exercised only in minimal Python installs

    yaml = None  # type: ignore[assignment]





SCHEMAS_ROOT = Path(__file__).resolve().parents[1] / "schemas"

VALIDATION_REPORT_SCHEMA_VERSION = "vela.validation.report.v1"





def schema_path(schema_name: str) -> Path:

    if schema_name.endswith(".json"):

        return SCHEMAS_ROOT / schema_name

    if schema_name.endswith(".schema"):

        return SCHEMAS_ROOT / f"{schema_name}.json"

    if schema_name.endswith(".schema.json"):

        return SCHEMAS_ROOT / schema_name

    return SCHEMAS_ROOT / f"{schema_name}.schema.json"





def load_schema(schema_name: str) -> dict[str, Any]:

    path = schema_path(schema_name)

    return json.loads(path.read_text(encoding="utf-8"))





def _error_path(error: exceptions.ValidationError) -> str:

    if not error.path:

        return "$"

    return "$." + ".".join(str(part) for part in error.path)





def _format_schema_error(error: exceptions.ValidationError, label: str) -> str:

    return f"{label}:{_error_path(error)}:{error.message}"





def validate_payload(payload: Any, schema_name: str, label: str) -> list[str]:

    try:

        schema = load_schema(schema_name)

    except (OSError, json.JSONDecodeError) as exc:

        return [f"{label}:schema-load-error:{exc}"]

    try:

        Draft202012Validator.check_schema(schema)

    except exceptions.SchemaError as exc:

        return [_format_schema_error(exc, f"{schema_name}:schema")]

    validator = Draft202012Validator(schema)

    return [

        _format_schema_error(error, label)

        for error in sorted(validator.iter_errors(payload), key=lambda item: list(item.path))

    ]





def load_json_or_yaml(path: Path) -> tuple[Any | None, list[str]]:

    if not path.exists():

        return None, [f"{path}:file-not-found"]

    try:

        text = path.read_text(encoding="utf-8")

    except OSError as exc:

        return None, [f"{path}:read-error:{exc}"]



    if path.suffix.lower() == ".json":

        try:

            return json.loads(text), []

        except json.JSONDecodeError as exc:

            return None, [f"{path}:json-parse-error:{exc}"]



    try:

        return json.loads(text), []

    except json.JSONDecodeError:

        pass



    if yaml is None:

        return None, [f"{path}:yaml-unavailable:install PyYAML or use JSON handoff packets"]

    try:

        return yaml.safe_load(text), []

    except Exception as exc:  # noqa: BLE001 - parser exceptions vary across PyYAML versions

        return None, [f"{path}:yaml-parse-error:{exc}"]





def validation_report(

    *,

    validator: str,

    scope: str,

    errors: list[str],

    warnings: list[str] | None = None,

    checks: list[dict[str, Any]] | None = None,

    decision: str | None = None,

    **extra: Any,

) -> dict[str, Any]:

    warnings = warnings or []

    if decision is None:

        decision = "pass" if not errors else "needs_review"

    payload: dict[str, Any] = {

        "schema_version": VALIDATION_REPORT_SCHEMA_VERSION,

        "validator": validator,

        "scope": scope,

        "decision": decision,

        "ok": decision == "pass" and not errors,

        "errors": errors,

        "warnings": warnings,

    }

    if checks is not None:

        payload["checks"] = checks

    payload.update(extra)

    return payload
