from __future__ import annotations



import json

import subprocess

from pathlib import Path

from typing import Any



from .validator_envelope import build_validator_result

try:

    from ..path_utils import CATALOG_ROOT, CODEX_HOME, REPO_ROOT, VELA_REPO_ROOT, VENV_PYTHON

except ImportError:  # Portable VELA installs expose envctl as a top-level package.

    from path_utils import CATALOG_ROOT, CODEX_HOME, REPO_ROOT, VELA_REPO_ROOT, VENV_PYTHON





REVIEWS_PATH = CATALOG_ROOT / "external_adoption_reviews.json"

CODEGRAPH_CACHE = REPO_ROOT / ".codegraph"

GUIZANG_ROOT = CODEX_HOME / "skills" / "guizang-ppt-skill"

OPENDATALOADER_WRAPPER = REPO_ROOT / "skills" / "scripts" / "run-opendataloader-pdf.ps1"

JAVA_RUNTIME_ROOT = REPO_ROOT / "python" / "runtime" / "jdk-21-adoptium"





def _run(args: list[str], *, cwd: Path = REPO_ROOT, timeout: int = 30) -> dict[str, Any]:

    try:

        result = subprocess.run(

            args,

            cwd=str(cwd),

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





def _load_reviews() -> dict[str, Any]:

    return json.loads(REVIEWS_PATH.read_text(encoding="utf-8"))





def _review_index(reviews: dict[str, Any]) -> dict[str, dict[str, Any]]:

    return {

        item.get("upstream", ""): item

        for item in reviews.get("reviews", [])

        if isinstance(item, dict) and item.get("upstream")

    }





def _pattern_only_entries(reviews: dict[str, Any]) -> list[dict[str, Any]]:

    entries: list[dict[str, Any]] = []

    markers = (

        "not installed",

        "not bulk-installed",

        "not installed as",

        "upstream runtime skill is not installed",

        "upstream skill is not installed",

        "runtime were not installed",

        "pattern-only",

    )

    for item in reviews.get("reviews", []):

        if not isinstance(item, dict):

            continue

        status = item.get("current_status", "").lower()

        rejected = " ".join(item.get("rejected_patterns", [])).lower()

        if any(marker in status or marker in rejected for marker in markers):

            entries.append(

                {

                    "upstream": item.get("upstream"),

                    "decision": item.get("decision"),

                    "runtime_claim": "pattern_only",

                }

            )

    return entries





def _probe_agentmemory() -> dict[str, Any]:

    status = _run(["cmd", "/c", "agentmemory", "status"], timeout=30)

    healthy = status["ok"] and "healthy" in status["stdout"].lower()

    return {

        "ok": healthy,

        "kind": "installed_runtime",

        "command": "agentmemory status",

        "healthy": healthy,

        "summary": "healthy" if healthy else "not healthy",

        "stdout_head": "\n".join(status["stdout"].splitlines()[:8]),

        "stderr": status["stderr"],

    }





def _probe_codegraph() -> dict[str, Any]:

    status = _run(["cmd", "/c", "codegraph", "status", "--json", str(REPO_ROOT)], timeout=30)

    parsed: dict[str, Any] = {}

    if status["ok"]:

        try:

            parsed = json.loads(status["stdout"])

        except json.JSONDecodeError:

            parsed = {}

    initialized = parsed.get("initialized") is True

    node_count = int(parsed.get("nodeCount") or 0)

    gitignore = REPO_ROOT / ".gitignore"
    if not gitignore.exists():
        gitignore = REPO_ROOT.parent / ".gitignore"
    cache_ignored = gitignore.exists() and ".codegraph" in gitignore.read_text(encoding="utf-8", errors="ignore")
    query = _run(["cmd", "/c", "codegraph", "query", "validate", "--limit", "1"], timeout=30) if initialized else {"ok": False}

    ok = status["ok"] and initialized and node_count > 0 and cache_ignored and query.get("ok") is True

    return {

        "ok": ok,

        "kind": "installed_runtime",

        "command": "codegraph status --json <VELA_RUNTIME_ROOT>",

        "initialized": initialized,

        "node_count": node_count,

        "edge_count": parsed.get("edgeCount"),

        "pending_changes": parsed.get("pendingChanges"),

        "cache_exists": CODEGRAPH_CACHE.exists(),

        "cache_ignored": cache_ignored,

        "query_ok": query.get("ok") is True,

        "project_scope_rule": "CodeGraph is project-local. If another project reports Not initialized, run skills/scripts/ensure-codegraph-index.ps1 -ProjectRoot <project> before relying on CodeGraph.",

        "stderr": status["stderr"],

    }





def _probe_guizang() -> dict[str, Any]:

    required = [

        GUIZANG_ROOT / "SKILL.md",

        GUIZANG_ROOT / "references" / "themes-swiss.md",

        GUIZANG_ROOT / "references" / "layouts-swiss.md",

        GUIZANG_ROOT / "scripts" / "validate-swiss-deck.mjs",

    ]

    missing = [str(path) for path in required if not path.exists()]

    return {

        "ok": not missing,

        "kind": "installed_runtime_skill",

        "root": str(GUIZANG_ROOT),

        "missing": missing,

    }





def _probe_opendataloader() -> dict[str, Any]:

    java_found = any(JAVA_RUNTIME_ROOT.rglob("java.exe")) if JAVA_RUNTIME_ROOT.exists() else False

    cli = REPO_ROOT / ".venv" / "Scripts" / "opendataloader-pdf.exe"

    help_probe = _run(

        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(OPENDATALOADER_WRAPPER), "--help"],

        timeout=30,

    )

    ok = VENV_PYTHON.exists() and cli.exists() and java_found and help_probe["ok"]

    return {

        "ok": ok,

        "kind": "optional_backend",

        "wrapper": str(OPENDATALOADER_WRAPPER),

        "venv_python_exists": VENV_PYTHON.exists(),

        "cli_exists": cli.exists(),

        "java_found": java_found,

        "help_ok": help_probe["ok"],

        "stderr": help_probe["stderr"],

    }





def _probe_superpowers() -> dict[str, Any]:

    candidates = list((CODEX_HOME / "plugins" / "cache" / "openai-curated").glob("superpowers/**/skills"))

    return {

        "ok": bool(candidates),

        "kind": "active_plugin",

        "cache_skill_roots": [str(path) for path in candidates[:5]],

    }





def _probe_vela() -> dict[str, Any]:

    vela_root = VELA_REPO_ROOT

    exists = vela_root.exists()

    manifest = vela_root / "runtime" / "manifest.json"
    return {

        "ok": exists and manifest.exists(),

        "kind": "vela_runtime_package",
        "repo_root": str(vela_root),

        "repo_exists": exists,

        "runtime_manifest_exists": manifest.exists(),
    }





def validate_external_adoption_readiness() -> dict[str, Any]:

    errors: list[str] = []

    warnings: list[str] = []

    reviews = _load_reviews()

    index = _review_index(reviews)

    probes = {

        "obra/superpowers": _probe_superpowers(),

        "op7418/guizang-ppt-skill": _probe_guizang(),

        "rohitg00/agentmemory": _probe_agentmemory(),

        "colbymchenry/codegraph": _probe_codegraph(),

        "opendataloader-project/opendataloader-pdf": _probe_opendataloader(),

        "Marcus-AI4SS/VELA": _probe_vela(),

    }



    for upstream in probes:

        if upstream not in index:

            errors.append(f"adoption-readiness:probe-upstream-missing-review:{upstream}")

    for upstream, probe in probes.items():
        if probe.get("ok") is True:
            continue
        if probe.get("kind") in {"optional_backend", "installed_runtime"}:
            warnings.append(f"adoption-readiness:runtime-probe-not-ready:{upstream}")
            continue
        errors.append(f"adoption-readiness:runtime-probe-failed:{upstream}")


    gs = index.get("cookjohn/gs-skills", {})

    if "blocked" not in gs.get("current_status", "").lower():

        warnings.append("adoption-readiness:google-scholar-status-does-not-declare-verification-block")



    pattern_only = _pattern_only_entries(reviews)

    details = {

        "review_count": len(reviews.get("reviews", [])),

        "pattern_only_count": len(pattern_only),

        "pattern_only_examples": pattern_only[:12],

        "runtime_probe_count": len(probes),

        "runtime_probes": probes,

        "codegraph_project_rule": "CodeGraph is not global per repository. Initialize each target project with ensure-codegraph-index.ps1 or codegraph init -i <project> before using CodeGraph context.",

        "classification_policy": {

            "pattern_only": "Upstream ideas were absorbed into local schemas, catalogs, skills, or validators; upstream runtime is intentionally absent.",

            "installed_runtime": "Documentation claims an installed component; this validator runs a local smoke probe.",

            "watch": "No local runtime availability is claimed.",

        },

    }

    return build_validator_result(

        validator="validate_external_adoption_readiness",

        scope="external_adoption_readiness",

        errors=errors,

        warnings=warnings,

        details=details,

    )
