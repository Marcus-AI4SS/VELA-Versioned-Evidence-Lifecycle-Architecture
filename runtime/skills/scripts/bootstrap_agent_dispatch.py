from __future__ import annotations



import argparse

import json

import sys

from pathlib import Path



try:

    from .envctl.dispatch import build_dispatch_result

    from .envctl.validator_envelope import build_validator_result, exit_code_for_result

except ImportError:  # pragma: no cover

    from envctl.dispatch import build_dispatch_result

    from envctl.validator_envelope import build_validator_result, exit_code_for_result





def parse_args() -> argparse.Namespace:

    parser = argparse.ArgumentParser()

    parser.add_argument("--project-root", type=Path, required=True)

    parser.add_argument("--route-id", required=True)

    parser.add_argument("--project-type")

    parser.add_argument("--stage", default="planning")

    parser.add_argument("--run-id")

    parser.add_argument(

        "--execution-mode",

        default="sequential_multi_agent_execution",

        choices=[

            "multi_perspective_reasoning",

            "sequential_multi_agent_execution",

            "parallel_multi_agent_execution",

        ],

    )

    parser.add_argument("--agent", action="append", dest="agents", required=True)

    parser.add_argument("--review-pair", action="append", default=[])

    parser.add_argument("--deliverable-type", action="append", default=[])

    parser.add_argument("--quality-gate", default=None)

    parser.add_argument("--route-confirmation-required", action="store_true")

    parser.add_argument("--route-confirmation-question", default="")

    parser.add_argument("--user-confirmed-route", action="store_true")

    parser.add_argument("--conflict-resolution", default="project-manager")

    parser.add_argument("--merge-owner", default=None)

    parser.add_argument("--user-veto-window", default="confirmed-in-thread")

    parser.add_argument("--overwrite", action="store_true")

    return parser.parse_args()





def main() -> None:

    if hasattr(sys.stdout, "reconfigure"):

        sys.stdout.reconfigure(encoding="utf-8")

    args = parse_args()

    try:

        report = build_dispatch_result(args)

    except SystemExit as exc:

        error = str(exc.code)

        report = build_validator_result(

            validator="bootstrap_agent_dispatch",

            scope="project",

            errors=[error] if error and error != "0" else [],

            details={"error": error},

            compatibility={"error": error},

        )

    print(json.dumps(report, ensure_ascii=False, indent=2))

    sys.exit(exit_code_for_result(report))





if __name__ == "__main__":

    main()
