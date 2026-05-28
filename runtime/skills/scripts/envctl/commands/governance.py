from __future__ import annotations



import argparse

import json

from pathlib import Path



try:

    from ..governance import (

        build_evolution_backlog_summary,

        build_reading_status,

        build_skill_audit_report,

        write_report,

    )

except ImportError:  # pragma: no cover

    from envctl.governance import (

        build_evolution_backlog_summary,

        build_reading_status,

        build_skill_audit_report,

        write_report,

    )





def run(args: argparse.Namespace) -> int:

    if args.action == "audit-skills":

        report = build_skill_audit_report()

        if args.output and not args.dry_run:

            output = None if args.output == "auto" else Path(args.output)

            written = write_report(report, output)

            report = {**report, "report_written": str(written)}

        if args.dry_run:

            report = {**report, "dry_run": True, "report_written": None}

        print(json.dumps(report, ensure_ascii=False, indent=2))

        return 0

    if args.action in {"reading-status", "source-evidence"}:

        print(json.dumps(build_reading_status(), ensure_ascii=False, indent=2))

        return 0

    if args.action == "evolution-backlog":

        print(json.dumps(build_evolution_backlog_summary(), ensure_ascii=False, indent=2))

        return 0

    raise ValueError(f"unsupported governance action: {args.action}")





def add_parser(subparsers: argparse._SubParsersAction) -> None:

    parser = subparsers.add_parser("governance")

    action = parser.add_subparsers(dest="action", required=True)



    audit = action.add_parser("audit-skills")

    audit.add_argument(

        "--output",

        help="Write the generated audit report to a path, or use 'auto' for skills/outputs/reports/governance-daily/YYYY-MM-DD.json.",

    )

    audit.add_argument(

        "--dry-run",

        action="store_true",

        help="Do not write an audit report even when --output is provided.",

    )

    audit.set_defaults(func=run)



    reading = action.add_parser("reading-status")

    reading.set_defaults(func=run)



    evidence = action.add_parser("source-evidence")

    evidence.set_defaults(func=run)



    backlog = action.add_parser("evolution-backlog")

    backlog.set_defaults(func=run)
