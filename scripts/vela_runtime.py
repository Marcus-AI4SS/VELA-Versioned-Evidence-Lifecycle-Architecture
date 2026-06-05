from __future__ import annotations



import json

import os

import shutil

import subprocess

import sys

import tomllib

from datetime import datetime, timezone

from pathlib import Path

from typing import Any



if __package__ in {None, ""}:

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

    from scripts import public_release_env as pre

    from scripts import vela_runtime_install

else:

    from scripts import public_release_env as pre

    from scripts import vela_runtime_install





RUNTIME_MANIFEST_PATH = vela_runtime_install.RUNTIME_PACKAGE_ROOT / "runtime" / "manifest.json"

RUNTIME_RECEIPT_NAME = "local-runtime-install.json"

RUNTIME_SCHEMA_VERSION = "vela.local_runtime.plan.v1"

RUNTIME_DOCTOR_SCHEMA_VERSION = "vela.local_runtime.doctor.v1"

RUNTIME_RECEIPT_SCHEMA_VERSION = "vela.local_runtime.install.receipt.v1"

ALL_CATEGORIES = ("core", "mcp", "plugins", "memory", "automation", "external-repos", "toolchain")

PLUGIN_IDS = ("superpowers", "github", "browser", "vela-runtime-local")





def _utc_now() -> str:

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()





def _load_json(path: Path) -> dict[str, Any]:

    return json.loads(path.read_text(encoding="utf-8"))





def _write_json(path: Path, payload: dict[str, Any]) -> None:

    path.parent.mkdir(parents=True, exist_ok=True)

    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")





def _parse_include(include: str | list[str] | tuple[str, ...] | None) -> list[str]:

    if include is None:

        return list(ALL_CATEGORIES)

    values: list[str] = []

    if isinstance(include, str):

        parts = include.split(",")

    else:

        parts = []

        for item in include:

            parts.extend(str(item).split(","))

    for raw in parts:

        item = raw.strip().lower()

        if not item:

            continue

        if item == "all":

            return list(ALL_CATEGORIES)

        if item == "repos":

            item = "external-repos"

        if item not in ALL_CATEGORIES:

            raise ValueError(f"unsupported-runtime-category:{item}")

        if item not in values:

            values.append(item)

    return values or list(ALL_CATEGORIES)





def _runtime_root(vela_home: Path) -> Path:

    return vela_home / "runtime"





def _profiles_root(vela_home: Path) -> Path:

    installed = _runtime_root(vela_home) / "skills" / "profiles"

    if installed.exists():

        return installed

    return vela_runtime_install.RUNTIME_PACKAGE_ROOT / "skills" / "profiles"





def _scripts_root(vela_home: Path) -> Path:

    installed = _runtime_root(vela_home) / "skills" / "scripts"

    if installed.exists():

        return installed

    return vela_runtime_install.RUNTIME_PACKAGE_ROOT / "skills" / "scripts"





def _load_profile(profile: str, profiles_root: Path) -> tuple[dict[str, Any] | None, list[str]]:

    path = profiles_root / f"{profile}.toml"

    if not path.exists():

        return None, [f"profile-missing:{path}"]

    try:

        payload = tomllib.loads(path.read_text(encoding="utf-8"))

    except (tomllib.TOMLDecodeError, OSError) as exc:

        return None, [f"profile-load-error:{path}:{exc}"]

    return payload, []





def _mcp_sections(codex_home: Path) -> tuple[list[str], list[str]]:

    config = codex_home / "config.toml"

    if not config.exists():

        return [], [f"codex-config-missing:{config}"]

    try:

        payload = tomllib.loads(config.read_text(encoding="utf-8"))

    except (tomllib.TOMLDecodeError, OSError) as exc:

        return [], [f"codex-config-load-error:{config}:{exc}"]

    servers = payload.get("mcp_servers", {})

    if not isinstance(servers, dict):

        return [], [f"codex-config-mcp-servers-missing:{config}"]

    return sorted(name for name, value in servers.items() if isinstance(value, dict)), []





def _run(args: list[str], *, cwd: Path | None = None, env: dict[str, str] | None = None, timeout: int = 20) -> dict[str, Any]:

    try:

        result = subprocess.run(

            args,

            cwd=str(cwd) if cwd else None,

            env=env,

            capture_output=True,

            text=True,

            encoding="utf-8",

            errors="replace",

            timeout=timeout,

            check=False,

        )

    except FileNotFoundError as exc:

        return {"ok": False, "returncode": None, "stdout": "", "stderr": str(exc)}

    except subprocess.TimeoutExpired as exc:

        return {

            "ok": False,

            "returncode": None,

            "stdout": exc.stdout or "",

            "stderr": f"timeout:{timeout}s",

        }

    return {

        "ok": result.returncode == 0,

        "returncode": result.returncode,

        "stdout": result.stdout.strip(),

        "stderr": result.stderr.strip(),

    }





def _probe_command(command: str, args: list[str] | None = None, *, timeout: int = 10) -> dict[str, Any]:

    found = shutil.which(command)

    if not found:

        return {"ok": False, "command": command, "path": None, "stdout_head": "", "stderr": "command-not-found"}

    command_args = args or ["--version"]

    executable = Path(found)

    if os.name == "nt" and executable.suffix.lower() in {".cmd", ".bat"}:

        run_args = ["cmd", "/c", str(executable), *command_args]

    else:

        run_args = [str(executable), *command_args]

    result = _run(run_args, timeout=timeout)

    stdout_head = "\n".join(result.get("stdout", "").splitlines()[:6])

    return {

        "ok": bool(result.get("ok")),

        "command": command,

        "path": found,

        "returncode": result.get("returncode"),

        "stdout_head": stdout_head,

        "stderr": result.get("stderr", ""),

    }





def _plugin_cache_status(codex_home: Path) -> dict[str, Any]:

    cache_root = codex_home / "plugins" / "cache"

    plugins: dict[str, Any] = {}

    for plugin_id in PLUGIN_IDS:

        candidates = []

        if cache_root.exists():

            candidates = [str(path) for path in cache_root.glob(f"**/{plugin_id}*") if path.is_dir()]

        plugins[plugin_id] = {

            "ok": bool(candidates),

            "cache_roots": candidates[:5],

            "policy": "detected_only_not_redistributed",

        }

    return {

        "ok": all(item["ok"] for item in plugins.values()),

        "cache_root": str(cache_root),

        "plugins": plugins,

    }





def _public_skill_status(codex_home: Path) -> dict[str, Any]:

    expected = vela_runtime_install._skill_names()

    missing = [name for name in expected if not (codex_home / "skills" / name / "SKILL.md").exists()]

    return {

        "ok": not missing,

        "expected_count": len(expected),

        "missing": missing,

    }





def _toolchain_status() -> dict[str, Any]:

    requirements = vela_runtime_install.RUNTIME_PACKAGE_ROOT / "python" / "requirements" / "research-core.txt"

    ai_requirements = vela_runtime_install.RUNTIME_PACKAGE_ROOT / "python" / "requirements" / "research-ai-extra.txt"

    current_python = _run([sys.executable, "--version"], timeout=10)

    return {

        "ok": requirements.exists(),

        "requirements": str(requirements),

        "requirements_exists": requirements.exists(),

        "ai_extra_requirements": str(ai_requirements),

        "ai_extra_requirements_exists": ai_requirements.exists(),

        "python": {

            "ok": bool(current_python.get("ok")),

            "command": "current-python",

            "path": sys.executable,

            "returncode": current_python.get("returncode"),

            "stdout_head": "\n".join(str(current_python.get("stdout", "")).splitlines()[:6]),

            "stderr": current_python.get("stderr", ""),

        },

        "path_python": _probe_command("python", ["--version"]),

        "git": _probe_command("git", ["--version"]),

        "node": _probe_command("node", ["--version"]),

    }





def _mcp_status(codex_home: Path, vela_home: Path, profile: str) -> dict[str, Any]:

    profiles_root = _profiles_root(vela_home)

    profile_payload, profile_errors = _load_profile(profile, profiles_root)

    sections, config_errors = _mcp_sections(codex_home)

    managed = list(profile_payload.get("managed_mcp", [])) if isinstance(profile_payload, dict) else []

    enabled = list(profile_payload.get("enabled_mcp", [])) if isinstance(profile_payload, dict) else []

    missing_sections = sorted(set(managed) - set(sections))

    return {

        "ok": not profile_errors and not config_errors and not missing_sections,

        "profile": profile,

        "profiles_root": str(profiles_root),

        "managed_mcp": managed,

        "enabled_mcp": enabled,

        "config_sections": sections,

        "missing_config_sections": missing_sections,

        "errors": profile_errors + config_errors,

        "policy": "VELA can apply profiles only when MCP server sections already exist in CODEX_HOME/config.toml.",

    }





def _memory_status() -> dict[str, Any]:
    policy_path = vela_runtime_install.RUNTIME_PACKAGE_ROOT / "skills" / "catalog" / "local_memory_system.json"
    if not policy_path.exists():
        return {
            "ok": False,
            "status": "policy-missing",
            "policy_path": str(policy_path),
            "errors": [f"local-memory-policy-missing:{policy_path}"],
            "policy": "VELA memory is governed by local contracts, not by an external memory service.",
        }

    policy = _load_json(policy_path)
    runtime_adapter = policy.get("runtime_adapter_policy", {}) if isinstance(policy, dict) else {}
    selected_adapter = runtime_adapter.get("selected_adapter")
    status = runtime_adapter.get("status")
    ok = selected_adapter == "local_contract_only" and status == "enabled"
    errors: list[str] = []
    if selected_adapter != "local_contract_only":
        errors.append(f"memory-adapter-not-local-contract:{selected_adapter}")
    if status != "enabled":
        errors.append(f"memory-adapter-not-enabled:{status}")

    return {
        "ok": ok,
        "status": "local-contract-ready" if ok else "contract-needs-review",
        "policy_path": str(policy_path),
        "selected_adapter": selected_adapter,
        "adapter_status": status,
        "errors": errors,
        "policy": "VELA uses schema/validator-governed local memory contracts. External memory services are watch-only patterns and are not installed, prestarted, or treated as memory authority.",
    }





def _codegraph_status(project_root: Path) -> dict[str, Any]:

    found = shutil.which("codegraph")

    if not found:

        return {"ok": False, "command": "codegraph", "stderr": "command-not-found"}

    executable = Path(found)

    if os.name == "nt" and executable.suffix.lower() in {".cmd", ".bat"}:

        args = ["cmd", "/c", str(executable), "status", "--json", str(project_root)]

    else:

        args = [str(executable), "status", "--json", str(project_root)]

    status = _run(args, timeout=15)

    parsed: dict[str, Any] = {}

    if status.get("ok"):

        try:

            parsed = json.loads(str(status.get("stdout") or "{}"))

        except json.JSONDecodeError:

            parsed = {}

    initialized = parsed.get("initialized") is True

    return {

        "ok": bool(status.get("ok")) and initialized,

        "command": "codegraph status --json <project>",

        "project_root": str(project_root),

        "initialized": initialized,

        "node_count": parsed.get("nodeCount"),

        "edge_count": parsed.get("edgeCount"),

        "stderr": status.get("stderr", ""),

        "policy": "CodeGraph is project-local; initialize each target project separately.",

    }





def _external_repos_status() -> dict[str, Any]:

    reviews = vela_runtime_install.RUNTIME_PACKAGE_ROOT / "skills" / "catalog" / "external_adoption_reviews.json"

    pattern_only = []

    if reviews.exists():

        payload = _load_json(reviews)

        for item in payload.get("reviews", []):

            if not isinstance(item, dict):

                continue

            status = str(item.get("current_status", "")).lower()

            rejected = " ".join(str(value) for value in item.get("rejected_patterns", [])).lower()

            if "not installed" in status or "not bulk" in rejected or "pattern-only" in status:

                pattern_only.append(item.get("upstream", "unknown"))

    return {

        "ok": True,

        "reviews": str(reviews),

        "pattern_only_count": len(pattern_only),

        "pattern_only_examples": pattern_only[:10],

        "policy": "Absorbed repositories are not cloned unless a future explicit installer marks them redistributable and required.",

    }





def _component(component_id: str, category: str, ok: bool, status: str, **extra: Any) -> dict[str, Any]:

    payload = {"id": component_id, "category": category, "ok": bool(ok), "status": status}

    payload.update(extra)

    return payload





def plan_runtime(

    *,

    codex_home: Path | None = None,

    vela_home: Path | None = None,

    include: str | list[str] | None = None,

    profile: str = "startup-safe",

    strict: bool = False,

) -> dict[str, Any]:

    codex_home = (codex_home or pre.CODEX_HOME).expanduser()

    vela_home = (vela_home or pre.APP_STATE_HOME).expanduser()

    categories = _parse_include(include)

    errors: list[str] = []

    warnings: list[str] = []

    manifest: dict[str, Any] | None = None

    if not RUNTIME_MANIFEST_PATH.exists():

        errors.append(f"runtime-manifest-missing:{RUNTIME_MANIFEST_PATH}")

    else:

        manifest = _load_json(RUNTIME_MANIFEST_PATH)



    components: list[dict[str, Any]] = []

    if "core" in categories:

        core = vela_runtime_install.doctor_runtime_core(codex_home=codex_home, vela_home=vela_home)

        public_skills = _public_skill_status(codex_home)

        components.append(

            _component(

                "core.vela-runtime",

                "core",

                bool(core.get("ok")) and public_skills["ok"],

                "installed" if core.get("ok") and public_skills["ok"] else "missing-or-incomplete",

                required=True,

                doctor=core,

                public_skills=public_skills,

                remediation="vela runtime enable --include core,automation,toolchain --commit",

            )

        )

    if "mcp" in categories:

        mcp = _mcp_status(codex_home, vela_home, profile)

        components.append(

            _component(

                "mcp.profile-readiness",

                "mcp",

                mcp["ok"],

                "profile-apply-ready" if mcp["ok"] else "config-sections-missing-or-unreadable",

                required=False,

                details=mcp,

                remediation="Define MCP server sections in CODEX_HOME/config.toml, then run envctl apply-profile.",

            )

        )

    if "plugins" in categories:

        plugin_status = _plugin_cache_status(codex_home)

        components.append(

            _component(

                "plugins.codex-cache",

                "plugins",

                plugin_status["ok"],

                "detected" if plugin_status["ok"] else "not-fully-detected",

                required=False,

                details=plugin_status,

                remediation="Install or enable required Codex plugins in the user's runtime; VELA does not vendor plugin caches.",

            )

        )

    if "memory" in categories:

        memory = _memory_status()

        components.append(

            _component(

                "memory.local-contracts",

                "memory",

                memory["ok"],

                "ready" if memory["ok"] else "needs-review",

                required=False,

                details=memory,

                remediation="Run `python -m skills.scripts.envctl validate memory --summary`; do not install or prestart external memory services by default.",

            )

        )

    if "automation" in categories:

        shim_cmd = vela_home / "bin" / "envctl.cmd"

        shim_sh = vela_home / "bin" / "envctl"

        components.append(

            _component(

                "automation.envctl",

                "automation",

                shim_cmd.exists() or shim_sh.exists(),

                "shim-installed" if shim_cmd.exists() or shim_sh.exists() else "shim-missing",

                required=True,

                shims={"windows": str(shim_cmd), "posix": str(shim_sh)},

                remediation="vela runtime enable --include core,automation,toolchain --commit",

                policy="No background automation or service is auto-started.",

            )

        )

    if "external-repos" in categories:

        external = _external_repos_status()

        codegraph = _codegraph_status(pre.REPO_ROOT)

        components.append(

            _component(

                "external-repos.adoption-readiness",

                "external-repos",

                external["ok"],

                "classified",

                required=False,

                details={**external, "codegraph": codegraph},

                remediation="Use envctl validate adoption-readiness for the local runtime; pattern-only repos are not install claims.",

            )

        )

    if "toolchain" in categories:

        toolchain = _toolchain_status()

        components.append(

            _component(

                "toolchain.python-requirements",

                "toolchain",

                toolchain["ok"],

                "requirements-present" if toolchain["ok"] else "requirements-missing",

                required=True,

                details=toolchain,

                remediation="Reinstall or refresh the VELA runtime package.",

            )

        )



    for item in components:

        if item["ok"]:

            continue

        message = f"runtime-component-not-ready:{item['id']}:{item['status']}"

        if strict:

            errors.append(message)

        else:

            warnings.append(message)



    required_ready = all(item["ok"] for item in components if item.get("required"))

    ready = required_ready and (all(item["ok"] for item in components) if strict else True)

    if not required_ready:

        next_action = "Run `vela runtime enable --commit --include core` first, then enable optional runtime categories explicitly."

    elif strict and any(not item["ok"] for item in components):

        next_action = "Core VELA runtime is ready. Enable or document optional runtime categories before requiring --strict all."

    else:

        next_action = "Core VELA runtime is ready. Use `vela runtime check --include all` to inspect optional runtime categories."

    return {

        "schema_version": RUNTIME_SCHEMA_VERSION,

        "generated_at": _utc_now(),

        "ok": not errors,

        "ready": ready,

        "mode": "plan",

        "strict": strict,

        "profile": profile,

        "include": categories,

        "paths": {

            "runtime_package": str(vela_runtime_install.RUNTIME_PACKAGE_ROOT),

            "source_role": "VELA runtime package in this repository",

            "codex_home": str(codex_home),

            "runtime_role": "user runtime target and health probe",

            "vela_home": str(vela_home),

            "runtime_manifest": str(RUNTIME_MANIFEST_PATH),

        },

        "manifest": manifest,

        "components": components,

        "errors": errors,

        "warnings": warnings,

        "next_action": next_action,

    }





def doctor_runtime(

    *,

    codex_home: Path | None = None,

    vela_home: Path | None = None,

    include: str | list[str] | None = None,

    profile: str = "startup-safe",

    strict: bool = False,

) -> dict[str, Any]:

    report = plan_runtime(codex_home=codex_home, vela_home=vela_home, include=include, profile=profile, strict=strict)

    report["schema_version"] = RUNTIME_DOCTOR_SCHEMA_VERSION

    report["mode"] = "doctor"

    report["ok"] = bool(report["ready"]) and not report["errors"]

    return report





def _run_apply_profile(*, codex_home: Path, vela_home: Path, profile: str, python_executable: str) -> dict[str, Any]:

    scripts_root = _scripts_root(vela_home)

    profiles_root = _profiles_root(vela_home)

    env = os.environ.copy()

    env["CODEX_HOME"] = str(codex_home)

    env["PYTHONPATH"] = str(scripts_root) + os.pathsep + env.get("PYTHONPATH", "")

    return _run(

        [

            python_executable,

            "-m",

            "envctl",

            "apply-profile",

            profile,

            "--commit",

            "--config",

            str(codex_home / "config.toml"),

            "--profiles-root",

            str(profiles_root),

        ],

        cwd=scripts_root,

        env=env,

        timeout=30,

    )





def install_runtime(

    *,

    codex_home: Path | None = None,

    vela_home: Path | None = None,

    include: str | list[str] | None = None,

    profile: str = "startup-safe",

    python_executable: str | None = None,

    commit: bool = False,

    force_core: bool = False,

    apply_profile: bool = False,

) -> dict[str, Any]:

    codex_home = (codex_home or pre.CODEX_HOME).expanduser()

    vela_home = (vela_home or pre.APP_STATE_HOME).expanduser()

    python_executable = python_executable or sys.executable

    categories = _parse_include(include)

    before = plan_runtime(codex_home=codex_home, vela_home=vela_home, include=categories, profile=profile)

    actions: list[dict[str, Any]] = []



    if not commit:

        before["mode"] = "install-dry-run"

        before["actions"] = [{"id": "write-runtime-receipt", "status": "dry-run"}]

        before["next_action"] = "Rerun with --commit to write receipts or install the VELA-owned core layer."

        return before



    errors: list[str] = []

    warnings: list[str] = []

    if "core" in categories:

        core = vela_runtime_install.install_runtime_core(

            codex_home=codex_home,

            vela_home=vela_home,

            python_executable=python_executable,

            force=force_core,

        )

        actions.append({"id": "core.vela-runtime", "status": "installed" if core.get("ok") else "failed", "result": core})

        if not core.get("ok"):

            errors.extend(str(item) for item in core.get("errors", []))



    if "mcp" in categories and apply_profile:

        applied = _run_apply_profile(

            codex_home=codex_home,

            vela_home=vela_home,

            profile=profile,

            python_executable=python_executable,

        )

        actions.append({"id": "mcp.apply-profile", "status": "applied" if applied.get("ok") else "failed", "result": applied})

        if not applied.get("ok"):

            errors.append("mcp-apply-profile-failed")

    elif "mcp" in categories:

        warnings.append("mcp-profile-not-applied:pass --apply-profile to mutate CODEX_HOME/config.toml")

        actions.append({"id": "mcp.apply-profile", "status": "skipped"})



    for category in ("plugins", "memory", "external-repos"):

        if category in categories:

            actions.append(

                {

                    "id": f"{category}.runtime-install",

                    "status": "doctor-only",

                    "policy": "VELA does not vendor or silently install this runtime category.",

                }

            )

    if "automation" in categories:

        actions.append({"id": "automation.envctl", "status": "installed-by-core" if "core" in categories else "checked-only"})

    if "toolchain" in categories:

        actions.append({"id": "toolchain.requirements", "status": "published-requirements-only"})



    after = plan_runtime(codex_home=codex_home, vela_home=vela_home, include=categories, profile=profile)

    receipt = {

        "schema_version": RUNTIME_RECEIPT_SCHEMA_VERSION,

        "generated_at": _utc_now(),

        "ok": not errors,

        "ready": bool(after.get("ready")) and not errors,

        "mode": "install-commit",

        "profile": profile,

        "include": categories,

        "paths": after["paths"],

        "components": after["components"],

        "actions": actions,

        "errors": errors,

        "warnings": warnings + after.get("warnings", []),

        "before": before,

        "next_action": "Run `vela runtime check --strict` after enabling optional runtime dependencies.",

    }

    _write_json(vela_home / "state" / RUNTIME_RECEIPT_NAME, receipt)

    return receipt
