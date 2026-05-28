from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    from .envctl.pipeline_contracts import build_pipeline_contract_result
    from .envctl.validator_envelope import exit_code_for_result
except ImportError:  # pragma: no cover
    from envctl.pipeline_contracts import build_pipeline_contract_result
    from envctl.validator_envelope import exit_code_for_result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = build_pipeline_contract_result(args.project_root)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    sys.exit(exit_code_for_result(report))


if __name__ == "__main__":
    main()
