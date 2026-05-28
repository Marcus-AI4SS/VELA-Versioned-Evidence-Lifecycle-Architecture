from __future__ import annotations

import argparse
import json

try:
    from ..route_explain import (
        build_route_explanation,
        build_startup_context_summary,
        summarize_route_report,
        validate_route_explanation_report,
        validate_startup_context_summary,
    )
except ImportError:  # pragma: no cover
    from envctl.route_explain import (
        build_route_explanation,
        build_startup_context_summary,
        summarize_route_report,
        validate_route_explanation_report,
        validate_startup_context_summary,
    )


def run(args: argparse.Namespace) -> int:
    if args.action == "explain":
        report = build_route_explanation(args.query, max_candidates=args.max_candidates)
        errors = validate_route_explanation_report(report)
        if errors:
            print(json.dumps({**report, "schema_errors": errors}, ensure_ascii=False, indent=2))
            return 1
        print(json.dumps(summarize_route_report(report) if args.summary else report, ensure_ascii=False, indent=2))
        return 0
    if args.action == "startup-summary":
        report = build_startup_context_summary(args.route_id)
        errors = validate_startup_context_summary(report)
        if errors:
            print(json.dumps({**report, "schema_errors": errors}, ensure_ascii=False, indent=2))
            return 1
        if args.summary:
            report = {
                "schema_version": report["schema_version"],
                "total_entry": report["total_entry"],
                "layer_order": report["layer_order"],
                "runtime_adapters": [item["id"] for item in report["runtime_adapters"]],
                "selected_route_context": report["selected_route_context"],
            }
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    raise ValueError(f"unsupported route action: {args.action}")


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("route")
    action = parser.add_subparsers(dest="action", required=True)

    explain = action.add_parser("explain")
    explain.add_argument("query")
    explain.add_argument("--max-candidates", type=int, default=5)
    explain.add_argument("--summary", action="store_true")
    explain.set_defaults(func=run)

    startup = action.add_parser("startup-summary")
    startup.add_argument("--route-id")
    startup.add_argument("--summary", action="store_true")
    startup.set_defaults(func=run)
