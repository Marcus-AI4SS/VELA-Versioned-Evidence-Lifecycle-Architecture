from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, exceptions


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _error_path(error: exceptions.ValidationError) -> str:
    if not error.path:
        return "$"
    return "$." + ".".join(str(part) for part in error.path)


def format_schema_error(error: exceptions.ValidationError, label: str) -> str:
    return f"{label}:{_error_path(error)}:{error.message}"


def collect_schema_errors(payload: Any, schema: dict[str, Any], label: str) -> list[str]:
    validator = Draft202012Validator(schema)
    return [
        format_schema_error(error, label)
        for error in sorted(validator.iter_errors(payload), key=lambda item: list(item.path))
    ]


def collect_schema_document_errors(schema: dict[str, Any], label: str) -> list[str]:
    try:
        Draft202012Validator.check_schema(schema)
    except exceptions.SchemaError as exc:
        return [format_schema_error(exc, label)]
    return []


def validate_json_file(payload_path: Path, schema_path: Path, label: str | None = None) -> list[str]:
    return collect_schema_errors(
        load_json(payload_path),
        load_json(schema_path),
        label or payload_path.name,
    )
