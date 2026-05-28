from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from scripts import init_research_project
    from scripts import vela_handoff
    from scripts import vela_bootstrap
    from scripts import vela_local_environment
    from scripts import vela_privacy
    from scripts import vela_public_export
    from scripts import vela_runtime
    from scripts import public_release_env as pre
    from scripts import vela_contract as contract
    from scripts import vela_initializer as initializer
else:
    from scripts import init_research_project
    from scripts import vela_handoff
    from scripts import vela_bootstrap
    from scripts import vela_local_environment
    from scripts import vela_privacy
    from scripts import vela_public_export
    from scripts import vela_runtime
    from scripts import public_release_env as pre
    from scripts import vela_contract as contract
    from scripts import vela_initializer as initializer


def _print_json(payload: object) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def cmd_doctor(_args: argparse.Namespace) -> int:
    pre.ensure_app_state_dirs()
    codex_home = pre.CODEX_HOME
    initializer_report = initializer.validate_manifest()
    payload = {
        "ok": True,
        "vela_repo": str(pre.REPO_ROOT),
        "python": sys.executable,
        "codex_home": str(codex_home),
        "codex_home_exists": codex_home.exists(),
        "vela_home": str(pre.APP_STATE_HOME),
        "package_exists": contract.package_root().exists(),
        "initializer_manifest": str(initializer.default_manifest_path()),
        "initializer_manifest_ok": initializer_report["ok"],
        "initializer_manifest_errors": initializer_report["errors"],
        "git": shutil.which("git"),
        "next_action": "Run `vela init <project>` or `python scripts/vela.py init <project>`.",
    }
    payload["ok"] = bool(payload["package_exists"] and payload["initializer_manifest_ok"])
    _print_json(payload)
    return 0 if payload["ok"] else 1


def cmd_init(args: argparse.Namespace) -> int:
    result = init_research_project.initialize_project(
        Path(args.path),
        skip_codex_trust=args.skip_codex_trust,
        route_hint=args.route_hint or args.profile,
    )
    _print_json(result)
    return 0


def cmd_handoff_new(args: argparse.Namespace) -> int:
    result = vela_handoff.create_handoff(Path(args.project or "."), args.template)
    _print_json(result)
    return 0 if result.get("ok") else 1


def cmd_handoff_lint(args: argparse.Namespace) -> int:
    result = vela_handoff.lint_handoff(Path(args.path))
    _print_json(result)
    return 0 if result["ok"] else 1


def cmd_handoff_render(args: argparse.Namespace) -> int:
    path = Path(args.path)
    try:
        rendered = vela_handoff.render_handoff_prompt(path)
    except ValueError:
        _print_json(vela_handoff.lint_handoff(path))
        return 1
    if args.out:
        target = Path(args.out)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(rendered, encoding="utf-8")
        _print_json({"ok": True, "output": str(target)})
    else:
        print(rendered)
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    result = contract.validate_project(Path(args.path), repair_context=args.repair_context)
    _print_json(result)
    return 0 if result["decision"] == "pass" else 1


def cmd_export_helm_context(args: argparse.Namespace) -> int:
    context = contract.write_project_context(Path(args.path))
    _print_json({"ok": True, "context": str(Path(args.path).expanduser().resolve() / ".vela" / "context.json"), "schema_version": context["schema_version"]})
    return 0


def cmd_privacy_scan(args: argparse.Namespace) -> int:
    result = vela_privacy.scan_project(Path(args.path))
    _print_json(result)
    return 0 if result["ok"] else 1


def cmd_export_public(args: argparse.Namespace) -> int:
    result = vela_public_export.build_public_export(Path(args.path), Path(args.out), force=args.force)
    _print_json(result)
    return 0 if result["ok"] else 1


def cmd_local_env_install(args: argparse.Namespace) -> int:
    result = vela_local_environment.install_local_environment(
        codex_home=Path(args.codex_home) if args.codex_home else None,
        vela_home=Path(args.vela_home) if args.vela_home else None,
        python_executable=args.python or sys.executable,
        force=args.force,
        dry_run=args.dry_run,
    )
    _print_json(result)
    return 0 if result.get("ok") else 1


def cmd_local_env_doctor(args: argparse.Namespace) -> int:
    result = vela_local_environment.doctor_local_environment(
        codex_home=Path(args.codex_home) if args.codex_home else None,
        vela_home=Path(args.vela_home) if args.vela_home else None,
    )
    _print_json(result)
    return 0 if result.get("ok") else 1


def cmd_local_env_plan_runtime(args: argparse.Namespace) -> int:
    result = vela_runtime.plan_runtime(
        codex_home=Path(args.codex_home) if args.codex_home else None,
        vela_home=Path(args.vela_home) if args.vela_home else None,
        include=args.include,
        profile=args.profile,
        strict=args.strict,
    )
    _print_json(result)
    return 0 if result.get("ok") else 1


def cmd_local_env_doctor_runtime(args: argparse.Namespace) -> int:
    result = vela_runtime.doctor_runtime(
        codex_home=Path(args.codex_home) if args.codex_home else None,
        vela_home=Path(args.vela_home) if args.vela_home else None,
        include=args.include,
        profile=args.profile,
        strict=args.strict,
    )
    _print_json(result)
    return 0 if result.get("ok") else 1


def cmd_local_env_install_runtime(args: argparse.Namespace) -> int:
    result = vela_runtime.install_runtime(
        codex_home=Path(args.codex_home) if args.codex_home else None,
        vela_home=Path(args.vela_home) if args.vela_home else None,
        include=args.include,
        profile=args.profile,
        python_executable=args.python or sys.executable,
        commit=args.commit,
        force_core=args.force_core,
        apply_profile=args.apply_profile,
    )
    _print_json(result)
    return 0 if result.get("ok") else 1


def cmd_local_env_bootstrap_tools(args: argparse.Namespace) -> int:
    result = vela_bootstrap.bootstrap_tools(include=args.include, install=args.install, yes=args.yes)
    _print_json(result)
    return 0 if result.get("ok") else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="VELA workflow wrapper CLI.")
    sub = parser.add_subparsers(dest="command", required=True)

    doctor = sub.add_parser("doctor", help="Check the local VELA/Codex environment.")
    doctor.set_defaults(func=cmd_doctor)

    init = sub.add_parser("init", help="Initialize a VELA wrapper project.")
    init.add_argument("path", help="Project root path.")
    init.add_argument("--profile", default="codex-research", help="Starter profile name.")
    init.add_argument("--route-hint", default=None, help="Optional route hint.")
    init.add_argument("--skip-codex-trust", action="store_true", help="Do not modify Codex trust config.")
    init.set_defaults(func=cmd_init)

    validate = sub.add_parser("validate", help="Validate a VELA project.")
    validate.add_argument("path", nargs="?", default=".", help="Project root path.")
    validate.add_argument("--repair-context", action="store_true", help="Regenerate .vela/context.json before validating.")
    validate.set_defaults(func=cmd_validate)

    export = sub.add_parser("export-helm-context", help="Regenerate .vela/context.json for HELM.")
    export.add_argument("path", nargs="?", default=".", help="Project root path.")
    export.set_defaults(func=cmd_export_helm_context)

    privacy = sub.add_parser("privacy", help="Run privacy checks before sharing project outputs.")
    privacy_sub = privacy.add_subparsers(dest="privacy_command", required=True)
    privacy_scan = privacy_sub.add_parser("scan", help="Scan a VELA project for private paths and secret-like content.")
    privacy_scan.add_argument("path", nargs="?", default=".", help="Project root path.")
    privacy_scan.set_defaults(func=cmd_privacy_scan)

    export_group = sub.add_parser("export", help="Create bounded project exports.")
    export_sub = export_group.add_subparsers(dest="export_command", required=True)
    export_public = export_sub.add_parser("public", help="Create a public-safe export package.")
    export_public.add_argument("path", nargs="?", default=".", help="Project root path.")
    export_public.add_argument("--out", required=True, help="Export output directory.")
    export_public.add_argument("--force", action="store_true", help="Write export even when privacy scan has errors.")
    export_public.set_defaults(func=cmd_export_public)

    local_env = sub.add_parser("local-env", help="Install or inspect the local research environment distribution.")
    local_env_sub = local_env.add_subparsers(dest="local_env_command", required=True)
    local_env_install = local_env_sub.add_parser(
        "install",
        help="Install the near 1:1 VELA local research environment into CODEX_HOME, excluding app and distillation chains.",
    )
    local_env_install.add_argument("--codex-home", default=None, help="Override CODEX_HOME for installation.")
    local_env_install.add_argument("--vela-home", default=None, help="Override VELA_HOME for managed state.")
    local_env_install.add_argument("--python", default=None, help="Python executable used by the envctl shim.")
    local_env_install.add_argument("--force", action="store_true", help="Back up and replace conflicting skill folders.")
    local_env_install.add_argument("--dry-run", action="store_true", help="Preview installation without writing files.")
    local_env_install.set_defaults(func=cmd_local_env_install)
    local_env_doctor = local_env_sub.add_parser("doctor", help="Check the installed VELA local research environment.")
    local_env_doctor.add_argument("--codex-home", default=None, help="Override CODEX_HOME for inspection.")
    local_env_doctor.add_argument("--vela-home", default=None, help="Override VELA_HOME for inspection.")
    local_env_doctor.set_defaults(func=cmd_local_env_doctor)
    local_env_plan_runtime = local_env_sub.add_parser(
        "plan-runtime",
        help="Plan the optional C-drive/user runtime bootstrap without mutating plugin caches, memory data, or MCP config.",
    )
    local_env_plan_runtime.add_argument("--codex-home", default=None, help="Override CODEX_HOME for inspection.")
    local_env_plan_runtime.add_argument("--vela-home", default=None, help="Override VELA_HOME for inspection.")
    local_env_plan_runtime.add_argument("--include", default="all", help="Comma list: core,mcp,plugins,memory,automation,external-repos,toolchain or all.")
    local_env_plan_runtime.add_argument("--profile", default="startup-safe", help="MCP profile to evaluate.")
    local_env_plan_runtime.add_argument("--strict", action="store_true", help="Treat optional runtime gaps as errors.")
    local_env_plan_runtime.set_defaults(func=cmd_local_env_plan_runtime)
    local_env_doctor_runtime = local_env_sub.add_parser("doctor-runtime", help="Check the optional runtime bootstrap status.")
    local_env_doctor_runtime.add_argument("--codex-home", default=None, help="Override CODEX_HOME for inspection.")
    local_env_doctor_runtime.add_argument("--vela-home", default=None, help="Override VELA_HOME for inspection.")
    local_env_doctor_runtime.add_argument("--include", default="all", help="Comma list: core,mcp,plugins,memory,automation,external-repos,toolchain or all.")
    local_env_doctor_runtime.add_argument("--profile", default="startup-safe", help="MCP profile to evaluate.")
    local_env_doctor_runtime.add_argument("--strict", action="store_true", help="Treat optional runtime gaps as errors.")
    local_env_doctor_runtime.set_defaults(func=cmd_local_env_doctor_runtime)
    local_env_install_runtime = local_env_sub.add_parser(
        "install-runtime",
        help="Install VELA-owned runtime pieces and write a runtime receipt. External plugins, MCP servers, and memory stores remain explicit/user-runtime only.",
    )
    local_env_install_runtime.add_argument("--codex-home", default=None, help="Override CODEX_HOME for installation.")
    local_env_install_runtime.add_argument("--vela-home", default=None, help="Override VELA_HOME for managed state.")
    local_env_install_runtime.add_argument("--include", default="core,automation,toolchain", help="Comma list: core,mcp,plugins,memory,automation,external-repos,toolchain or all.")
    local_env_install_runtime.add_argument("--profile", default="startup-safe", help="MCP profile to apply when --apply-profile is set.")
    local_env_install_runtime.add_argument("--python", default=None, help="Python executable used for runtime shims.")
    local_env_install_runtime.add_argument("--commit", action="store_true", help="Write receipts and install VELA-owned core runtime pieces.")
    local_env_install_runtime.add_argument("--force-core", action="store_true", help="Back up and replace conflicting skill folders during core install.")
    local_env_install_runtime.add_argument("--apply-profile", action="store_true", help="With --commit and --include mcp, mutate CODEX_HOME/config.toml through envctl apply-profile.")
    local_env_install_runtime.set_defaults(func=cmd_local_env_install_runtime)
    local_env_bootstrap_tools = local_env_sub.add_parser(
        "bootstrap-tools",
        help="Check and optionally install public system tools needed by the VELA runtime.",
    )
    local_env_bootstrap_tools.add_argument("--include", default="all", help="Comma list: system,optional,runtime or all.")
    local_env_bootstrap_tools.add_argument("--install", action="store_true", help="Attempt explicit public tool installation where VELA knows a safe installer.")
    local_env_bootstrap_tools.add_argument("--yes", action="store_true", help="Allow installation commands to run. Without this, --install only previews remediation.")
    local_env_bootstrap_tools.set_defaults(func=cmd_local_env_bootstrap_tools)

    handoff = sub.add_parser("handoff", help="Create, lint, or render Codex handoffs.")
    handoff_sub = handoff.add_subparsers(dest="handoff_command", required=True)
    handoff_new = handoff_sub.add_parser("new", help="Create a bounded handoff packet.")
    handoff_new.add_argument("--project", default=".", help="Project root path.")
    handoff_new.add_argument("--template", default="claim-check", choices=["claim-check", "read-project"], help="Handoff template.")
    handoff_new.set_defaults(func=cmd_handoff_new)
    handoff_lint = handoff_sub.add_parser("lint", help="Lint a handoff packet.")
    handoff_lint.add_argument("path", help="Handoff YAML path.")
    handoff_lint.set_defaults(func=cmd_handoff_lint)
    handoff_render = handoff_sub.add_parser("render", help="Render a handoff packet into a Codex prompt.")
    handoff_render.add_argument("path", help="Handoff YAML path.")
    handoff_render.add_argument("--out", default=None, help="Optional prompt output path.")
    handoff_render.set_defaults(func=cmd_handoff_render)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    raise SystemExit(args.func(args))


if __name__ == "__main__":
    main()
