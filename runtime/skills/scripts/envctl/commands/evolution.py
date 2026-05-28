from __future__ import annotations



import argparse

import json

from pathlib import Path



try:

    from ..evolution_intake import (

        append_report_items_to_backlog,

        build_evolution_intake_report,

        validate_report,

        write_evolution_intake_report,

    )

except ImportError:  # pragma: no cover

    from envctl.evolution_intake import (

        append_report_items_to_backlog,

        build_evolution_intake_report,

        validate_report,

        write_evolution_intake_report,

    )





def run(args: argparse.Namespace) -> int:

    if args.action == "intake":

        report = build_evolution_intake_report(

            scan_roots=[Path(item) for item in args.scan_root] if args.scan_root else None,

            lookback_days=args.lookback_days,

        )

        errors = validate_report(report)

        if errors:

            print(json.dumps({**report, "schema_errors": errors}, ensure_ascii=False, indent=2))

            return 1

        if args.append_backlog:

            append_result = append_report_items_to_backlog(report)

            report = {

                **report,

                "mode": "backlog_append",

                "source_files_written": bool(append_result.get("source_file_written")),

                "backlog_append": append_result,

            }

            errors = validate_report(report)

            if errors:

                print(json.dumps({**report, "schema_errors": errors}, ensure_ascii=False, indent=2))

                return 1

        if args.write_report:

            output = None if args.output == "auto" else Path(args.output) if args.output else None

            markdown_path, json_path = write_evolution_intake_report(report, output)

            report = {

                **report,

                "report_written": str(markdown_path),

                "json_report_written": str(json_path),

            }

        print(json.dumps(report, ensure_ascii=False, indent=2))

        return 0

    raise ValueError(f"unsupported evolution action: {args.action}")





def add_parser(subparsers: argparse._SubParsersAction) -> None:

    parser = subparsers.add_parser("evolution")

    action = parser.add_subparsers(dest="action", required=True)



    intake = action.add_parser("intake")

    intake.add_argument(

        "--scan-root",

        action="append",

        default=[],

        help="Root directory to scan. Can be repeated. Defaults to enabled roots in evolution_intake_policy.json.",

    )

    intake.add_argument(

        "--lookback-days",

        type=int,

        help="Only include candidate files modified within this many days.",

    )

    intake.add_argument(

        "--write-report",

        action="store_true",

        help="Write a Markdown and JSON report under skills/outputs/reports/evolution-intake, or --output.",

    )

    intake.add_argument(

        "--output",

        help="Markdown report path, or omit for skills/outputs/reports/evolution-intake/YYYY-MM-DD.md.",

    )

    intake.add_argument(

        "--append-backlog",

        action="store_true",

        help="Append observed candidates to skills/catalog/evolution_backlog.json. Use only in a dedicated update thread.",

    )

    intake.set_defaults(func=run)
