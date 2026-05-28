from __future__ import annotations

import argparse
import json
from pathlib import Path

from ..project_initializer import ensure_project_contract, initialize_project


def run(args: argparse.Namespace) -> int:
    report = initialize_project(args.path, update_trust=not args.no_trust)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


def run_ensure_contract(args: argparse.Namespace) -> int:
    report = ensure_project_contract(args.path, enable_all_agents=not args.respect_manifest_enabled)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("init-project")
    parser.add_argument("--path", type=Path, required=True)
    parser.add_argument("--no-trust", action="store_true")
    parser.set_defaults(func=run)

    ensure_parser = subparsers.add_parser("ensure-project-contract")
    ensure_parser.add_argument("--path", type=Path, required=True)
    ensure_parser.add_argument("--respect-manifest-enabled", action="store_true")
    ensure_parser.set_defaults(func=run_ensure_contract)
