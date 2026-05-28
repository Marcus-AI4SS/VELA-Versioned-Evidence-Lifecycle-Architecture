# VELA Contract-First Refactor Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Turn VELA into a schema-backed Codex workflow wrapper that can be installed into a user's project, validated locally, and read by HELM without relying on private environment assumptions.

**Architecture:** VELA owns the public workflow package, project scaffold, Codex handoff packets, `.vela/context.json`, validators, and installable CLI. VELA must not become a desktop app, hidden agent loop, private research automation platform, or HELM dependency.

**Tech Stack:** Python CLI, JSON Schema draft 2020-12, small YAML/JSON parser layer, file-system starter package, unittest.

---

## Cross-Repository Consistency Contract

This plan must stay consistent with:

- HELM plan: `<GIT_FOLDERS_ROOT>\HELM\docs\desktop-contract-refactor-plan.md`
- Local environment plan: `<LOCAL_ENV_ROOT>\skills\docs\20-architecture\local-environment-contract-refactor-plan.md`

Shared product boundary:

| Product | Owns | Must not own |
| --- | --- | --- |
| VELA | Public Codex workflow wrapper, starter package, `.vela/context.json`, Codex handoff schema, validation reports | Desktop UI, local dashboard, private harness runtime |
| HELM | Desktop local board, safe local file access, local validator invocation, copyable Codex handoff display | Creating research projects silently, executing Codex work, owning VELA state |
| Local environment | Private/source governance for skills, MCP, profiles, harness, playbooks, vetting, environment validation | Public product branding, HELM UI, VELA public runtime assumptions |

Shared schema names:

- `vela.project.context.v1`: VELA writes; HELM reads.
- `vela.codex.handoff.v1`: VELA writes/lints/renders for Codex.
- `helm.codex.handoff.v1`: HELM prepares; VELA may store only after explicit user export/save.
- `vela.validation.report.v1`: VELA validators emit.
- `vela.project.initializer.v1`: VELA public starter package manifest.
- `project_initializer_manifest.v1`: local environment private initializer manifest.

Required data flow:

```text
Local environment -> promotes stable contract ideas into VELA
VELA -> writes schema-valid local project state
HELM Desktop -> reads VELA state and prepares schema-valid copyable Codex handoff
Codex/user -> performs and reviews research work
```

Forbidden data flow:

```text
HELM silently writes research state into VELA projects
VELA depends on HELM to function
VELA imports private local environment paths or app payloads
Local environment publishes private harness/app assumptions as VELA public defaults
```

## Current Problems

### P1. Handoff lint is marker-based, not schema-backed

File: `scripts/vela.py`

Current behavior:

- `_lint_handoff()` checks whether text contains marker strings such as `schema_version:` and `relevant_files:`.
- It does not parse YAML or JSON.
- It does not validate against `schemas/vela.codex.handoff.v1.schema.json`.

Required behavior:

- `vela handoff lint` must parse handoff packets.
- Parsed payloads must be validated against `vela.codex.handoff.v1`.
- Type errors, missing nested fields, and invalid structure must fail.

### P1. Validation schema and CLI output are inconsistent

Files:

- `schemas/vela.validation.result.v1.schema.json`
- `scripts/vela.py`
- `scripts/vela_contract.py`

Current behavior:

- The schema declares `vela.validation.result.v1` with `ok/errors/warnings`.
- CLI validators emit `vela.validation.report.v1` with `decision`, `checks`, and `context_schema`.

Required behavior:

- Replace or supersede the current result schema with `vela.validation.report.v1.schema.json`.
- Every VELA validator should emit the same envelope:

```json
{
  "schema_version": "vela.validation.report.v1",
  "validator": "handoff_lint",
  "scope": "handoffs/H001.yaml",
  "decision": "pass",
  "ok": true,
  "errors": [],
  "warnings": [],
  "checks": []
}
```

### P1. Initializer validation is partially schema-driven

Files:

- `scripts/vela_initializer.py`
- `schemas/vela.project.initializer.v1.schema.json`

Current behavior:

- `validate_manifest()` manually checks some shape and path constraints.
- The JSON Schema exists but is not used by runtime validation.

Required behavior:

- Use JSON Schema for structural validation.
- Keep Python path-safety checks for rules JSON Schema cannot express cleanly.
- Return a `vela.validation.report.v1` envelope.

### P2. CLI file is still carrying business logic

File: `scripts/vela.py`

Current behavior:

- `vela.py` handles argparse, handoff creation, marker linting, prompt rendering, validation, and context export.

Required behavior:

- Keep `vela.py` as a thin CLI adapter.
- Move handoff logic into `scripts/vela_handoff.py`.
- Move schema logic into `scripts/vela_schema.py`.

## Target File Structure

Create:

```text
scripts/vela_schema.py
scripts/vela_handoff.py
schemas/vela.validation.report.v1.schema.json
tests/test_vela_schema.py
tests/test_vela_handoff.py
```

Modify:

```text
scripts/vela.py
scripts/vela_contract.py
scripts/vela_initializer.py
schemas/vela.codex.handoff.v1.schema.json
schemas/vela.project.initializer.v1.schema.json
README.md
README.zh-CN.md
docs/codex-wrapper.md
```

Remove or deprecate:

```text
schemas/vela.validation.result.v1.schema.json
```

If removing is too disruptive, keep it as a compatibility schema but stop using it for current CLI output.

## Implementation Plan

### Task 1: Add a schema validation module

Files:

- Create: `scripts/vela_schema.py`
- Test: `tests/test_vela_schema.py`

Required API:

```python
from pathlib import Path
from typing import Any

def schema_path(schema_name: str) -> Path:
    ...

def load_schema(schema_name: str) -> dict[str, Any]:
    ...

def validate_payload(payload: Any, schema_name: str, label: str) -> list[str]:
    ...

def load_json_or_yaml(path: Path) -> tuple[Any | None, list[str]]:
    ...
```

Implementation rules:

- Use `jsonschema.Draft202012Validator`.
- Support JSON directly.
- Support YAML through `yaml.safe_load` if PyYAML is available.
- If PyYAML is unavailable and the file is not JSON, return a clear validation error telling the user to install PyYAML or use JSON.
- Do not silently accept unparsed text.

Validation:

```powershell
python -m unittest skills.tests.test_vela_schema
```

### Task 2: Add the validation report schema

Files:

- Create: `schemas/vela.validation.report.v1.schema.json`
- Modify: `schemas/vela.validation.result.v1.schema.json` only if kept as compatibility.

Schema requirements:

- Required:
  - `schema_version`
  - `validator`
  - `scope`
  - `decision`
  - `ok`
  - `errors`
  - `warnings`
- `schema_version` const: `vela.validation.report.v1`
- `decision` enum: `pass`, `needs_review`, `fail`
- `errors` and `warnings` arrays of strings.
- `checks` optional array.

Validation:

```powershell
python -m json.tool schemas\vela.validation.report.v1.schema.json > $null
```

### Task 3: Move handoff logic into `vela_handoff.py`

Files:

- Create: `scripts/vela_handoff.py`
- Modify: `scripts/vela.py`
- Test: `tests/test_vela_handoff.py`

Required API:

```python
from pathlib import Path

def next_handoff_id(handoffs_dir: Path) -> str:
    ...

def create_handoff(project_root: Path, template: str) -> dict[str, object]:
    ...

def lint_handoff(path: Path) -> dict[str, object]:
    ...

def render_handoff_prompt(path: Path) -> str:
    ...
```

Behavior:

- `create_handoff()` writes `handoffs/Hxxx.yaml` and `handoffs/Hxxx.prompt.md`.
- `lint_handoff()` parses payload and validates against `vela.codex.handoff.v1`.
- `lint_handoff()` returns `vela.validation.report.v1`.
- Prompt rendering must fail if lint fails unless a `--force` flag is added later.

### Task 4: Make project validation schema-backed

Files:

- Modify: `scripts/vela_contract.py`
- Test: `tests/test_vela_contract.py` or extend existing tests.

Behavior:

- `validate_project()` emits `vela.validation.report.v1`.
- If `.vela/context.json` exists, validate it against `vela.project.context.v1`.
- If `repair_context=True`, write context then validate the written file.
- Required path checks should remain in `checks`.

### Task 5: Make initializer validation schema-backed

Files:

- Modify: `scripts/vela_initializer.py`
- Test: `tests/test_vela_initializer.py`

Behavior:

- `validate_manifest()` validates using `vela.project.initializer.v1`.
- Keep path safety checks:
  - no absolute paths;
  - no `..`;
  - no duplicate file or directory entries;
  - agent file names must end with `.json`.
- Return `vela.validation.report.v1`, not `vela.validation.result.v1`.

### Task 6: Keep `vela.py` as CLI only

File:

- Modify: `scripts/vela.py`

After refactor, `vela.py` should only:

- define argparse;
- call `init_research_project`;
- call `vela_handoff`;
- call `vela_contract`;
- call `vela_initializer` for `doctor`;
- print JSON or rendered prompt.

No marker linting, no handoff template literals, and no schema logic should remain in `vela.py`.

### Task 7: Update docs and examples

Files:

- Modify: `README.md`
- Modify: `README.zh-CN.md`
- Modify: `docs/codex-wrapper.md`
- Modify or add: `examples/00-minimal-wrapper`

Required public wording:

- VELA = `Versioned Evidence Lifecycle Architecture`.
- VELA is a portable Codex workflow wrapper.
- VELA prepares bounded work for Codex; Codex performs the work; people review the result.
- HELM is optional and reads VELA state.

## Acceptance Tests

Run from the VELA repository root.

```powershell
python -m py_compile `
  scripts\vela.py `
  scripts\vela_schema.py `
  scripts\vela_handoff.py `
  scripts\vela_contract.py `
  scripts\vela_initializer.py `
  scripts\init_research_project.py
```

```powershell
python -m unittest discover -s tests
```

```powershell
python scripts\vela.py doctor
```

Smoke test:

```powershell
$tmp = Join-Path $env:TEMP ("vela-contract-" + [guid]::NewGuid().ToString("N"))
python scripts\vela.py init $tmp --skip-codex-trust --route-hint literature-review
python scripts\vela.py validate $tmp --repair-context
python scripts\vela.py handoff new --project $tmp --template claim-check
python scripts\vela.py handoff lint (Join-Path $tmp "handoffs\H001.yaml")
python scripts\vela.py handoff render (Join-Path $tmp "handoffs\H001.yaml")
Remove-Item -LiteralPath $tmp -Recurse -Force
```

## Non-Goals

- Do not add Rust.
- Do not make VELA a desktop app.
- Do not make HELM required for VELA.
- Do not import private local environment paths into public package defaults.
- Do not implement a hidden Codex execution loop.
- Do not silently run `codex exec`.

## Final Target

VELA should read as:

```text
schemas define contracts
Python modules implement contract-aware operations
CLI exposes small commands
starter package materializes a project
HELM reads only schema-valid project state
```

