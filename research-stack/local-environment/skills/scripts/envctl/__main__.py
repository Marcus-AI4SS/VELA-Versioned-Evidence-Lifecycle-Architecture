from __future__ import annotations

import argparse
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from .commands import apply_profile, cnki_zotero, cybernetics, evolution, init_project, memory, plan_team, route, validate


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="envctl")
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate.add_parser(subparsers)
    cnki_zotero.add_parser(subparsers)
    cybernetics.add_parser(subparsers)
    evolution.add_parser(subparsers)
    memory.add_parser(subparsers)
    apply_profile.add_parser(subparsers)
    plan_team.add_parser(subparsers)
    route.add_parser(subparsers)
    init_project.add_parser(subparsers)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
