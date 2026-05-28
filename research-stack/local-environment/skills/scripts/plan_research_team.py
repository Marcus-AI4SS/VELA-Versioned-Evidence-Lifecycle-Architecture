from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    from .envctl.team_plan import build_team_plan_result
except ImportError:  # pragma: no cover
    from envctl.team_plan import build_team_plan_result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--route-id", required=True)
    parser.add_argument("--project-type")
    parser.add_argument("--stage", default="planning")
    parser.add_argument("--run-id")
    parser.add_argument("--target-item-count", type=int, default=0)
    parser.add_argument("--work-unit", action="append", default=[])
    parser.add_argument("--deliverable-type", action="append", default=[])
    parser.add_argument("--sync-target", action="append", default=[])
    parser.add_argument(
        "--explicit-project-mode",
        default="auto",
        choices=["auto", "force_multi_agent", "force_single_agent"],
    )
    parser.add_argument("--needs-clarification", action="store_true")
    parser.add_argument("--quality-gate", default=None)
    parser.add_argument("--conflict-resolution", default="project-manager")
    parser.add_argument("--merge-owner", default=None)
    parser.add_argument("--user-veto-window", default="confirmed-in-thread")
    parser.add_argument("--bootstrap", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument(
        "--no-auto-init-project-contract",
        dest="auto_init_project_contract",
        action="store_false",
        default=True,
    )
    return parser.parse_args()


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    report = build_team_plan_result(parse_args())
    print(json.dumps(report, ensure_ascii=False, indent=2))
    sys.exit(0 if report.get("ok") is True else 1)


if __name__ == "__main__":
    main()
