from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

try:
    from ..cross_repo_drift import validate_cross_repo_drift
    from ..cnki_zotero import validate_cnki_zotero_workflow
    from ..conflict_matrix import validate_conflict_matrix
    from ..cybernetics import validate_cybernetics_contracts
    from ..empirical_quant_workflow import validate_empirical_quant_workflow
    from ..environment_layers import validate_environment_layer_contract
    from ..external_adoption_readiness import validate_external_adoption_readiness
    from ..helm_snapshot import validate_helm_snapshot_contract
    from ..initializer_policy import validate_initializer_policy
    from ..manuscript_writing_workflow import validate_manuscript_writing_workflow
    from ..memory_system import validate_local_memory_system
    from ..peer_review_workflow import validate_peer_review_workflow
    from ..research_presentation_workflow import validate_research_presentation_workflow
    from ..scholar_browser_patterns import validate_scholar_browser_patterns
    from ..scientific_figure_workflow import validate_scientific_figure_workflow
    from ..skill_workbench_policy import validate_skill_workbench_policy
    from ..validator_envelope import build_validator_result, exit_code_for_result
    from ...validate_vela_contracts import collect_contract_errors
except ImportError:  # pragma: no cover
    from envctl.cross_repo_drift import validate_cross_repo_drift
    from envctl.cnki_zotero import validate_cnki_zotero_workflow
    from envctl.conflict_matrix import validate_conflict_matrix
    from envctl.cybernetics import validate_cybernetics_contracts
    from envctl.empirical_quant_workflow import validate_empirical_quant_workflow
    from envctl.environment_layers import validate_environment_layer_contract
    from envctl.external_adoption_readiness import validate_external_adoption_readiness
    from envctl.helm_snapshot import validate_helm_snapshot_contract
    from envctl.initializer_policy import validate_initializer_policy
    from envctl.manuscript_writing_workflow import validate_manuscript_writing_workflow
    from envctl.memory_system import validate_local_memory_system
    from envctl.peer_review_workflow import validate_peer_review_workflow
    from envctl.research_presentation_workflow import validate_research_presentation_workflow
    from envctl.scholar_browser_patterns import validate_scholar_browser_patterns
    from envctl.scientific_figure_workflow import validate_scientific_figure_workflow
    from envctl.skill_workbench_policy import validate_skill_workbench_policy
    from envctl.validator_envelope import build_validator_result, exit_code_for_result
    from validate_vela_contracts import collect_contract_errors


def run(args: argparse.Namespace) -> int:
    if args.target in {"contracts", "vela"}:
        errors, warnings, payload = collect_contract_errors()
        report = build_validator_result(
            validator="validate_vela_contracts",
            scope="contracts",
            errors=errors,
            warnings=warnings,
            details={"target": args.target, **payload},
            compatibility={"target": args.target, **payload},
        )
    elif args.target == "initializer-policy":
        report = validate_initializer_policy()
    elif args.target == "helm-snapshot":
        report = validate_helm_snapshot_contract()
    elif args.target == "drift":
        report = validate_cross_repo_drift()
    elif args.target == "cybernetics":
        report = validate_cybernetics_contracts()
    elif args.target == "memory":
        report = validate_local_memory_system()
    elif args.target == "environment-layers":
        report = validate_environment_layer_contract()
    elif args.target == "adoption-readiness":
        report = validate_external_adoption_readiness()
    elif args.target == "conflicts":
        report = validate_conflict_matrix()
    elif args.target == "cnki-zotero":
        report = validate_cnki_zotero_workflow()
    elif args.target == "scholar-browser-patterns":
        report = validate_scholar_browser_patterns()
    elif args.target == "peer-review-workflow":
        report = validate_peer_review_workflow()
    elif args.target == "scientific-figure-workflow":
        report = validate_scientific_figure_workflow()
    elif args.target == "manuscript-writing":
        report = validate_manuscript_writing_workflow()
    elif args.target == "research-presentation-workflow":
        report = validate_research_presentation_workflow()
    elif args.target == "skill-workbench":
        report = validate_skill_workbench_policy()
    elif args.target == "empirical-quant-workflow":
        report = validate_empirical_quant_workflow()
    elif args.target == "stack":
        report = _run_stack_validator()
    else:  # pragma: no cover
        raise ValueError(f"unsupported validate target: {args.target}")
    if args.summary:
        print(json.dumps(_summarize_report(report), ensure_ascii=False, indent=2))
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return exit_code_for_result(report)


def _run_stack_validator() -> dict:
    root = Path(__file__).resolve().parents[2]
    script = root / "validate_research_stack.py"
    result = subprocess.run(
        [sys.executable, str(script)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if result.returncode != 0:
        return build_validator_result(
            validator="validate_research_stack",
            scope="stack",
            errors=[f"validate_research_stack-exit:{result.returncode}"],
            warnings=[],
            details={"stdout": result.stdout.strip(), "stderr": result.stderr.strip()},
        )
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        return build_validator_result(
            validator="validate_research_stack",
            scope="stack",
            errors=[f"validate_research_stack-invalid-json:{exc}"],
            details={"stdout": result.stdout.strip(), "stderr": result.stderr.strip()},
        )
    command_errors = [
        name
        for name, item in payload.get("commands", {}).items()
        if isinstance(item, dict) and item.get("ok") is not True
    ]
    drift_errors = []
    drift = payload.get("cross_repo_drift", {})
    if isinstance(drift, dict) and drift.get("ok") is not True:
        drift_errors = [f"cross-repo-drift:{item}" for item in drift.get("errors", [])]
    return build_validator_result(
        validator="validate_research_stack",
        scope="stack",
        errors=[f"command-probe-failed:{name}" for name in command_errors] + drift_errors,
        warnings=[],
        details=payload,
    )


def _summarize_report(report: dict) -> dict:
    details = report.get("details", {})
    commands = details.get("commands", {}) if isinstance(details, dict) else {}
    failed_commands = [
        name
        for name, payload in commands.items()
        if isinstance(payload, dict) and payload.get("ok") is not True
    ]
    return {
        "schema_version": "validator_result.summary.v1",
        "validator": report.get("validator"),
        "scope": report.get("scope"),
        "ok": report.get("ok"),
        "decision": report.get("decision"),
        "error_count": len(report.get("errors", [])),
        "warning_count": len(report.get("warnings", [])),
        "errors": report.get("errors", []),
        "warnings": report.get("warnings", []),
        "failed_commands": failed_commands,
        "detail_keys": sorted(details.keys()) if isinstance(details, dict) else [],
    }


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("validate")
    parser.add_argument(
        "target",
        choices=[
            "vela",
            "contracts",
            "stack",
            "initializer-policy",
            "helm-snapshot",
            "drift",
            "cybernetics",
            "memory",
            "environment-layers",
            "adoption-readiness",
            "conflicts",
            "cnki-zotero",
            "scholar-browser-patterns",
            "peer-review-workflow",
            "scientific-figure-workflow",
            "manuscript-writing",
            "research-presentation-workflow",
            "skill-workbench",
            "empirical-quant-workflow",
        ],
        default="contracts",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print a compact result for chat stability; exit code still reflects the full validator result.",
    )
    parser.set_defaults(func=run)
