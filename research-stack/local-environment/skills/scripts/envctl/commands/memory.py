from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from ..memory_system import (
        build_memory_reconciliation_report,
        build_memory_status_report,
        candidate_from_text,
        decide_candidate,
        validate_memory_reconciliation_report,
        validate_memory_status_report,
        write_memory_reconciliation_report,
        write_memory_status_report,
    )
except ImportError:  # pragma: no cover
    from envctl.memory_system import (
        build_memory_reconciliation_report,
        build_memory_status_report,
        candidate_from_text,
        decide_candidate,
        validate_memory_reconciliation_report,
        validate_memory_status_report,
        write_memory_reconciliation_report,
        write_memory_status_report,
    )


def run(args: argparse.Namespace) -> int:
    if args.action in {"status", "doctor"}:
        report = build_memory_status_report()
        errors = validate_memory_status_report(report)
        if errors:
            print(json.dumps({**report, "schema_errors": errors}, ensure_ascii=False, indent=2))
            return 1
        if args.output and not args.dry_run:
            output = None if args.output == "auto" else Path(args.output)
            written = write_memory_status_report(report, output)
            report = {**report, "report_written": str(written)}
        if args.dry_run:
            report = {**report, "dry_run": True, "report_written": None}
        if args.summary:
            print(json.dumps(_summarize_status(report), ensure_ascii=False, indent=2))
        else:
            print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    if args.action == "reconcile":
        report = build_memory_reconciliation_report(probe_agentmemory=args.probe_agentmemory)
        errors = validate_memory_reconciliation_report(report)
        if errors:
            print(json.dumps({**report, "schema_errors": errors}, ensure_ascii=False, indent=2))
            return 1
        if args.output and not args.dry_run:
            output = None if args.output == "auto" else Path(args.output)
            written = write_memory_reconciliation_report(report, output)
            report = {**report, "report_written": str(written)}
        if args.dry_run:
            report = {**report, "dry_run": True, "report_written": None}
        if args.summary:
            print(json.dumps(_summarize_reconciliation(report), ensure_ascii=False, indent=2))
        else:
            print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    if args.action == "score":
        if args.input:
            candidate = json.loads(Path(args.input).read_text(encoding="utf-8"))
        else:
            candidate = candidate_from_text(
                text=args.text or "",
                source_type=args.source_type,
                source_ref=args.source_ref,
                memory_layer=args.memory_layer,
                privacy_scope=args.privacy_scope,
                proposed_target=args.proposed_target,
                occurrence_count=args.occurrence_count,
                user_confirmed=args.user_confirmed,
            )
        result = decide_candidate(candidate)
        payload = {
            "schema_version": "memory_score_result.v1",
            "source_files_written": False,
            "candidate": candidate,
            "result": result,
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0 if not result["schema_errors"] else 1
    raise ValueError(f"unsupported memory action: {args.action}")


def _summarize_status(report: dict) -> dict:
    return {
        "schema_version": report["schema_version"],
        "mode": report["mode"],
        "source_files_written": report["source_files_written"],
        "selected_plan": report["selected_plan"],
        "memory_layers": [item["id"] for item in report["memory_layers"]],
        "lightweight_constraints": report["lightweight_constraints"],
        "required_gates": report["automation"]["required_gates"],
        "report_written": report.get("report_written"),
    }


def _summarize_reconciliation(report: dict) -> dict:
    return {
        "schema_version": report["schema_version"],
        "mode": report["mode"],
        "source_files_written": report["source_files_written"],
        "agentmemory": report["agentmemory"],
        "automation_reports": report["automation_reports"],
        "evolution_backlog": report["evolution_backlog"],
        "reconciliation": report["reconciliation"],
        "report_written": report.get("report_written"),
    }


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("memory")
    action = parser.add_subparsers(dest="action", required=True)

    for name in ["status", "doctor"]:
        status = action.add_parser(name)
        status.add_argument("--summary", action="store_true")
        status.add_argument(
            "--output",
            help="Write a status report to a path, or use 'auto' for skills/outputs/reports/local-memory-system/YYYY-MM-DD.json.",
        )
        status.add_argument("--dry-run", action="store_true")
        status.set_defaults(func=run)

    reconcile = action.add_parser("reconcile")
    reconcile.add_argument("--summary", action="store_true")
    reconcile.add_argument("--probe-agentmemory", action="store_true")
    reconcile.add_argument(
        "--output",
        help="Write a reconciliation report to a path, or use 'auto' for skills/outputs/reports/local-memory-system/YYYY-MM-DD-reconciliation.json.",
    )
    reconcile.add_argument("--dry-run", action="store_true")
    reconcile.set_defaults(func=run)

    score = action.add_parser("score")
    score.add_argument("--input", help="Path to a memory_candidate.v1 JSON file.")
    score.add_argument("--text", help="Candidate memory text when --input is not provided.")
    score.add_argument(
        "--source-type",
        default="explicit_preference",
        choices=[
            "user_correction",
            "route_override",
            "validator_failure",
            "project_retrospective",
            "tool_health",
            "explicit_preference",
            "daily_audit",
            "weekly_review",
        ],
    )
    score.add_argument("--source-ref", default="manual-cli")
    score.add_argument(
        "--memory-layer",
        default="procedural_memory",
        choices=[
            "ephemeral_session",
            "project_memory",
            "private_preference",
            "procedural_memory",
            "control_memory",
            "discarded_noise",
        ],
    )
    score.add_argument(
        "--privacy-scope",
        default="public_repo",
        choices=["public_repo", "project_private", "local_private", "session_only"],
    )
    score.add_argument(
        "--proposed-target",
        default="skill",
        choices=["control_kernel", "skill", "obsidian", "codex_native", "evolution_backlog", "discard"],
    )
    score.add_argument("--occurrence-count", type=int, default=1)
    score.add_argument("--user-confirmed", action="store_true")
    score.set_defaults(func=run)
