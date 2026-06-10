from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from ..memory_system import (
        append_thread_memory_report_to_backlog,
        build_memory_reconciliation_report,
        build_memory_status_report,
        build_thread_memory_intake_report,
        candidate_from_text,
        decide_candidate,
        validate_memory_reconciliation_report,
        validate_memory_status_report,
        validate_thread_memory_intake_report,
        write_memory_reconciliation_report,
        write_memory_status_report,
        write_thread_memory_intake_report,
    )
except ImportError:  # pragma: no cover
    from envctl.memory_system import (
        append_thread_memory_report_to_backlog,
        build_memory_reconciliation_report,
        build_memory_status_report,
        build_thread_memory_intake_report,
        candidate_from_text,
        decide_candidate,
        validate_memory_reconciliation_report,
        validate_memory_status_report,
        validate_thread_memory_intake_report,
        write_memory_reconciliation_report,
        write_memory_status_report,
        write_thread_memory_intake_report,
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
        report = build_memory_reconciliation_report(probe_external_memory_service=args.probe_external_memory_service)
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
    if args.action == "intake-thread":
        observations = None
        text = args.text
        if args.input:
            payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                text = payload.get("text", text)
                observations = payload.get("observations")
                args.source_ref = payload.get("source_ref") or args.source_ref
                args.thread_id = payload.get("thread_id") or args.thread_id
                args.route_id = payload.get("route_id") or args.route_id
                args.user_confirmed = bool(payload.get("user_confirmed", args.user_confirmed))
            elif isinstance(payload, list):
                observations = payload
            else:
                raise ValueError("intake-thread input must be a JSON object or list")
        report = build_thread_memory_intake_report(
            source_ref=args.source_ref,
            text=text,
            observations=observations,
            thread_id=args.thread_id,
            route_id=args.route_id,
            user_confirmed=args.user_confirmed,
        )
        errors = validate_thread_memory_intake_report(report)
        if errors:
            public_report = {key: value for key, value in report.items() if not key.startswith("_")}
            print(json.dumps({**public_report, "schema_errors": errors}, ensure_ascii=False, indent=2))
            return 1
        if args.write_report and not args.dry_run:
            output = None if args.output == "auto" else Path(args.output) if args.output else None
            written = write_thread_memory_intake_report(report, output)
            report = {**report, "report_written": str(written)}
        if args.append_backlog and not args.dry_run:
            append_result = append_thread_memory_report_to_backlog(report)
            report = {**report, "source_files_written": append_result["source_file_written"], "backlog_append": append_result}
        if args.dry_run:
            report = {**report, "dry_run": True, "report_written": None, "backlog_append": None}
        public_report = {key: value for key, value in report.items() if not key.startswith("_")}
        if args.summary:
            print(json.dumps(_summarize_thread_intake(public_report), ensure_ascii=False, indent=2))
        else:
            print(json.dumps(public_report, ensure_ascii=False, indent=2))
        return 0
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
        "external_memory_service": report["external_memory_service"],
        "automation_reports": report["automation_reports"],
        "evolution_backlog": report["evolution_backlog"],
        "reconciliation": report["reconciliation"],
        "report_written": report.get("report_written"),
    }


def _summarize_thread_intake(report: dict) -> dict:
    return {
        "schema_version": report["schema_version"],
        "mode": report["mode"],
        "source_files_written": report["source_files_written"],
        "source_ref": report["source_ref"],
        "thread_id": report["thread_id"],
        "route_id": report["route_id"],
        "raw_transcript_ingested": report["raw_transcript_ingested"],
        "observation_count": report["observation_count"],
        "skill_evolution_candidate_count": len(report["skill_evolution_candidates"]),
        "backlog_event_count": len(report["backlog_events"]),
        "rejected_count": report["rejected_count"],
        "decisions": [
            {
                "signal_type": item["signal_type"],
                "target_skill": item["target_skill"],
                "decision": item["decision"]["decision"],
                "score": item["decision"]["admission_score"],
            }
            for item in report["observations"]
        ],
        "report_written": report.get("report_written"),
        "backlog_append": report.get("backlog_append"),
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
    reconcile.add_argument("--probe-external_memory_service", action="store_true")
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

    intake = action.add_parser("intake-thread")
    intake.add_argument("--input", help="JSON object/list containing extracted thread observations.")
    intake.add_argument("--text", help="Compact thread summary or extracted user preference text.")
    intake.add_argument("--source-ref", default="thread:manual", help="Stable source reference, such as thread id or handoff path.")
    intake.add_argument("--thread-id", default="")
    intake.add_argument("--route-id", default="")
    intake.add_argument("--user-confirmed", action="store_true")
    intake.add_argument("--write-report", action="store_true")
    intake.add_argument("--append-backlog", action="store_true")
    intake.add_argument("--output", default="auto", help="Report path, or auto for skills/outputs/reports/thread-memory-intake/YYYY-MM-DD.json.")
    intake.add_argument("--summary", action="store_true")
    intake.add_argument("--dry-run", action="store_true")
    intake.set_defaults(func=run)
