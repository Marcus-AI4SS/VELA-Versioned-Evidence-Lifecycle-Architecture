from __future__ import annotations



import argparse

import json

from pathlib import Path



try:

    from ..apply_profile import apply_profile, rollback_profile

except ImportError:  # pragma: no cover

    from envctl.apply_profile import apply_profile, rollback_profile





def run(args: argparse.Namespace) -> int:

    if args.rollback:

        report = rollback_profile(

            config_path=args.config,

            backup_root=args.backup_root,

            backup_id=args.rollback,

        )

    else:

        report = apply_profile(

            args.profile,

            config_path=args.config,

            profiles_root=args.profiles_root,

            backup_root=args.backup_root,

            dry_run=args.dry_run,

            commit=args.commit,

        )

    print(json.dumps(report, ensure_ascii=False, indent=2))

    return 0 if report.get("ok") is True else 1





def add_parser(subparsers: argparse._SubParsersAction) -> None:

    parser = subparsers.add_parser("apply-profile")

    parser.add_argument("profile", nargs="?", help="Profile name from skills/profiles/<name>.toml.")

    mode = parser.add_mutually_exclusive_group(required=True)

    mode.add_argument("--dry-run", action="store_true", help="Preview config.toml changes without writing.")

    mode.add_argument("--commit", action="store_true", help="Back up and write config.toml changes.")

    mode.add_argument("--rollback", nargs="?", const="latest", help="Restore a backup by file name/path, or latest.")

    parser.add_argument("--config", type=Path, default=None, help="Override config.toml path. Defaults to CODEX_HOME/config.toml.")

    parser.add_argument("--profiles-root", type=Path, default=None, help="Override profiles directory.")

    parser.add_argument("--backup-root", type=Path, default=None, help="Override backup directory.")

    parser.set_defaults(func=_normalize_and_run)





def _normalize_and_run(args: argparse.Namespace) -> int:

    from ..apply_profile import DEFAULT_BACKUP_ROOT

    from ...path_utils import CONFIG_PATH, PROFILES_ROOT



    args.config = args.config or CONFIG_PATH

    args.profiles_root = args.profiles_root or PROFILES_ROOT

    args.backup_root = args.backup_root or DEFAULT_BACKUP_ROOT

    if not args.rollback and not args.profile:

        report = {

            "ok": False,

            "mode": "apply-profile",

            "errors": ["profile-is-required-unless-rollback-is-used"],

            "warnings": [],

            "source_files_written": False,

            "config_written": False,

        }

        print(json.dumps(report, ensure_ascii=False, indent=2))

        return 1

    return run(args)
