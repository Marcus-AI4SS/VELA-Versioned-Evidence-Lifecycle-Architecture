from __future__ import annotations



from pathlib import Path

from typing import Any



if __package__ in {None, ""}:

    import sys



    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

    from scripts import vela_contract as contract

    from scripts import vela_schema

else:

    from scripts import vela_contract as contract

    from scripts import vela_schema





HANDOFF_SCHEMA = "vela.codex.handoff.v1"





def next_handoff_id(handoffs_dir: Path) -> str:

    handoffs_dir.mkdir(parents=True, exist_ok=True)

    existing = sorted(handoffs_dir.glob("H*.yaml"))

    if not existing:

        return "H001"

    numbers = []

    for path in existing:

        stem = path.stem.upper()

        if stem.startswith("H") and stem[1:].isdigit():

            numbers.append(int(stem[1:]))

    return f"H{(max(numbers) + 1 if numbers else 1):03d}"





def _handoff_template(handoff_id: str, template: str) -> str:

    task = (

        "Review whether a claim is supported by named evidence."

        if template == "claim-check"

        else "Read the relevant files and produce a bounded next-step note."

    )

    return "\n".join(

        [

            "schema_version: vela.codex.handoff.v1",

            f"handoff_id: {handoff_id}",

            f'created_at: "{contract.utc_now()}"',

            "created_by: human",

            "surface: cli",

            "mode: review_only",

            "project:",

            "  title: TODO",

            "  stage: research_design",

            "scope:",

            f"  task: {task}",

            "  relevant_files:",

            "    - research-map.md",

            "    - evidence-ledger.yaml",

            "  excluded_files:",

            "    - private-notes/",

            "    - credentials/",

            "constraints:",

            "  - Do not add new claims.",

            "  - Do not treat material notes as verified evidence.",

            "expected_output:",

            "  format: markdown",

            f"  path: logs/codex-runs/{handoff_id}-result.md",

            "review_standard:",

            "  - Every support judgment must cite an evidence_id.",

            "  - Unsupported or uncertain claims must remain marked as needs_review.",

            "completion:",

            "  validation_commands:",

            f"    - vela handoff lint handoffs/{handoff_id}.yaml",

            "  human_review_required: true",

            "",

        ]

    )





def create_handoff(project_root: Path, template: str) -> dict[str, object]:

    project_root = project_root.expanduser().resolve()

    handoffs_dir = project_root / "handoffs"

    handoff_id = next_handoff_id(handoffs_dir)

    target = handoffs_dir / f"{handoff_id}.yaml"

    target.write_text(_handoff_template(handoff_id, template), encoding="utf-8")

    lint_report = lint_handoff(target)

    if not lint_report["ok"]:

        return {

            "ok": False,

            "handoff": str(target),

            "prompt": None,

            "validation": lint_report,

        }

    prompt_target = handoffs_dir / f"{handoff_id}.prompt.md"

    prompt_target.write_text(render_handoff_prompt(target), encoding="utf-8")

    return {"ok": True, "handoff": str(target), "prompt": str(prompt_target), "validation": lint_report}





def lint_handoff(path: Path) -> dict[str, Any]:

    payload, parse_errors = vela_schema.load_json_or_yaml(path)

    errors = list(parse_errors)

    if payload is None:

        return vela_schema.validation_report(

            validator="handoff_lint",

            scope=str(path),

            errors=errors,

            warnings=[],

        )

    if not isinstance(payload, dict):

        errors.append(f"{path}:root-must-be-object")

    else:

        errors.extend(vela_schema.validate_payload(payload, HANDOFF_SCHEMA, str(path)))

    return vela_schema.validation_report(

        validator="handoff_lint",

        scope=str(path),

        errors=errors,

        warnings=[],

    )





def render_handoff_prompt(path: Path) -> str:

    report = lint_handoff(path)

    if not report["ok"]:

        raise ValueError("Invalid handoff packet: " + "; ".join(report["errors"]))

    text = path.read_text(encoding="utf-8")

    return "\n".join(

        [

            "# VELA Codex Handoff",

            "",

            "Read this bounded handoff before acting. Do not expand scope unless the user approves.",

            "",

            "```yaml",

            text.rstrip(),

            "```",

            "",

            "Return changed files, validation reports, unsupported claims, and remaining blockers.",

            "",

        ]

    )
