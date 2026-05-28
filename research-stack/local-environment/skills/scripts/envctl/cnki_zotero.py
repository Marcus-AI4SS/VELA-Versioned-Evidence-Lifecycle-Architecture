from __future__ import annotations

import base64
import hashlib
import importlib.util
import json
import shutil
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from ..path_utils import CATALOG_ROOT, OUTPUTS_ROOT, REPO_ROOT, SCHEMAS_ROOT
    from .schema_validation import collect_schema_document_errors, collect_schema_errors, load_json
    from .validator_envelope import build_validator_result
except ImportError:  # pragma: no cover
    from path_utils import CATALOG_ROOT, OUTPUTS_ROOT, REPO_ROOT, SCHEMAS_ROOT
    from envctl.schema_validation import collect_schema_document_errors, collect_schema_errors, load_json
    from envctl.validator_envelope import build_validator_result


WORKFLOW_PATH = CATALOG_ROOT / "cnki_zotero_workflow.json"
SCHEMA_PATH = SCHEMAS_ROOT / "cnki_zotero_workflow.v1.schema.json"
REPORT_SCHEMA_PATHS = [
    SCHEMAS_ROOT / "cnki_candidate_discovery.v1.schema.json",
    SCHEMAS_ROOT / "cnki_search_batch_download.v1.schema.json",
]


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_workflow_contract() -> dict[str, Any]:
    return load_json(WORKFLOW_PATH)


def validate_cnki_zotero_workflow() -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    schema = load_json(SCHEMA_PATH)
    contract = load_workflow_contract()
    errors.extend(collect_schema_document_errors(schema, "cnki_zotero_workflow.schema"))
    for report_schema_path in REPORT_SCHEMA_PATHS:
        errors.extend(
            collect_schema_document_errors(
                load_json(report_schema_path),
                f"{report_schema_path.stem}.schema",
            )
        )
    errors.extend(collect_schema_errors(contract, schema, "cnki_zotero_workflow"))
    errors.extend(_collect_workflow_semantic_errors(contract))
    return build_validator_result(
        validator="validate_cnki_zotero_workflow",
        scope="cnki_zotero_workflow",
        errors=errors,
        warnings=warnings,
        details={
            "contract": str(WORKFLOW_PATH.relative_to(REPO_ROOT)),
            "schema": str(SCHEMA_PATH.relative_to(REPO_ROOT)),
            "report_schemas": [str(path.relative_to(REPO_ROOT)) for path in REPORT_SCHEMA_PATHS],
            "workflow_id": contract.get("workflow_id"),
            "default_inbox": contract.get("inbox", {}).get("default_path"),
        },
    )


def _collect_workflow_semantic_errors(contract: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    channels = {item.get("id") for item in contract.get("acquisition_channels", []) if isinstance(item, dict)}
    required_channels = {
        "cnki-mcp-discovery",
        "authorized-browser-download",
        "cnki-export-metadata",
        "zotero-mcp-write",
    }
    errors.extend(f"cnki_zotero_workflow:missing-channel:{item}" for item in sorted(required_channels - channels))
    inbox = contract.get("inbox", {})
    inbox_path = inbox.get("default_path", "")
    if "outputs" not in Path(inbox_path).parts:
        errors.append("cnki_zotero_workflow:default-inbox-must-be-under-outputs")
    project_inbox = inbox.get("project_default_relative_path", "")
    if Path(project_inbox).is_absolute() or "outputs" not in Path(project_inbox).parts:
        errors.append("cnki_zotero_workflow:project-inbox-must-be-relative-under-outputs")
    fallback = inbox.get("environment_fallback_path")
    if fallback and fallback != inbox_path:
        errors.append("cnki_zotero_workflow:default-path-must-equal-environment-fallback-path")
    modes = set(contract.get("zotero_import", {}).get("supported_import_modes", []))
    if "local_pdf_add_from_file" not in modes:
        errors.append("cnki_zotero_workflow:missing-local-pdf-import-mode")
    policy = contract.get("candidate_selection", {}).get("author_affiliation_policy", {})
    if policy.get("required_when_affiliation_requested") is not True:
        errors.append("cnki_zotero_workflow:author-affiliation-gate-must-be-required")
    forbidden = set(policy.get("forbidden_shortcuts", []))
    if "author_only_search_as_affiliation_match" not in forbidden:
        errors.append("cnki_zotero_workflow:missing-author-only-shortcut-ban")
    if "fulltext_query_as_affiliation_filter" not in forbidden:
        errors.append("cnki_zotero_workflow:missing-fulltext-shortcut-ban")
    return errors


def resolve_inbox(path: str | Path | None = None, *, project_root: str | Path | None = None) -> Path:
    contract = load_workflow_contract()
    if project_root is not None:
        project = Path(project_root).expanduser().resolve()
        if not project.exists():
            raise ValueError(f"project root does not exist: {project}")
        if path is None:
            path = contract["inbox"]["project_default_relative_path"]
        candidate = Path(path)
        if not candidate.is_absolute():
            candidate = project / candidate
        resolved = candidate.resolve()
        _assert_project_inbox(resolved, project)
        return resolved
    if path is None:
        path = contract["inbox"]["environment_fallback_path"]
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = REPO_ROOT / candidate
    return candidate.resolve()


def build_status(
    *,
    inbox: str | Path | None = None,
    project_root: str | Path | None = None,
    ensure_inbox: bool = False,
    cdp: str | None = None,
    check_cdp: bool = False,
) -> dict[str, Any]:
    validation = validate_cnki_zotero_workflow()
    inbox_path = resolve_inbox(inbox, project_root=project_root)
    runtime = inspect_controlled_cnki_runtime(cdp=cdp, check_cdp=check_cdp)
    source_files_written = False
    if ensure_inbox and not inbox_path.exists():
        if project_root is None:
            _assert_safe_environment_inbox(inbox_path)
        else:
            _assert_project_inbox(inbox_path, Path(project_root).expanduser().resolve())
        inbox_path.mkdir(parents=True, exist_ok=True)
        source_files_written = False
    files = scan_inbox(inbox_path) if inbox_path.exists() else []
    scope = "project" if project_root is not None else "environment_fallback"
    errors = list(validation["errors"]) + list(runtime["errors"])
    return {
        "schema_version": "cnki_zotero_status.v1",
        "generated_at": _utc_now(),
        "workflow_id": load_workflow_contract()["workflow_id"],
        "ok": validation["ok"] and runtime["ok"],
        "validation_errors": validation["errors"],
        "runtime": runtime,
        "errors": errors,
        "mode": "report_only",
        "scope": scope,
        "project_root": str(Path(project_root).expanduser().resolve()) if project_root is not None else None,
        "source_files_written": source_files_written,
        "inbox": str(inbox_path),
        "inbox_exists": inbox_path.exists(),
        "file_count": len(files),
        "by_action": dict(sorted(Counter(item["action"] for item in files).items())),
        "next_steps": [
            "If direct CDP is not ready, run skills\\scripts\\open-cnki-controlled-chrome.ps1 and log in to CNKI in that window.",
            "Set the browser batch-download script target to the project inbox when a project root is available.",
            "Run envctl cnki-zotero audit-inbox after downloads finish.",
            "Use Zotero MCP to add verified local PDFs or DOI records after reviewing the import plan.",
        ],
    }


def inspect_controlled_cnki_runtime(*, cdp: str | None = None, check_cdp: bool = False) -> dict[str, Any]:
    errors: list[str] = []
    websocket_available = _websocket_client_available()
    agent_browser_path = shutil.which("agent-browser")
    cdp_report: dict[str, Any] = {
        "checked": check_cdp,
        "endpoint": cdp,
        "reachable": None,
        "websocket_url": None,
        "error": None,
    }
    if not websocket_available:
        errors.append("missing-python-dependency:websocket-client")
    if check_cdp:
        try:
            cdp_report["websocket_url"] = _resolve_cdp_websocket_url(cdp or "9333")
            cdp_report["reachable"] = True
        except Exception as exc:
            cdp_report["reachable"] = False
            cdp_report["error"] = f"{type(exc).__name__}:{exc}"
            errors.append("cdp-endpoint-unreachable")
    return {
        "ok": not errors,
        "websocket_client_available": websocket_available,
        "agent_browser_available": bool(agent_browser_path),
        "agent_browser_path": agent_browser_path,
        "direct_cdp_supported": websocket_available,
        "direct_cdp": cdp_report,
        "errors": errors,
    }


def _websocket_client_available() -> bool:
    if importlib.util.find_spec("websocket") is None:
        return False
    try:
        import websocket  # type: ignore[import-not-found]
    except Exception:
        return False
    return hasattr(websocket, "create_connection")


def _ensure_direct_cdp_runtime() -> None:
    if not _websocket_client_available():
        raise RuntimeError(
            "missing-python-dependency:websocket-client; install it in the active Python environment before CNKI direct CDP search"
        )


def build_agent_browser_args(
    *,
    inbox: str | Path,
    auto_connect: bool = True,
    cdp: str | None = None,
    profile: str | None = None,
    session_name: str | None = None,
) -> list[str]:
    """Build an agent-browser command that keeps downloads inside the selected inbox."""
    agent_browser = shutil.which("agent-browser")
    if not agent_browser:
        raise ValueError("agent-browser executable was not found on PATH")
    args = [agent_browser]
    if auto_connect:
        args.append("--auto-connect")
    if cdp:
        args.extend(["--cdp", cdp])
    if profile:
        args.extend(["--profile", profile])
    if session_name:
        args.extend(["--session-name", session_name])
    args.extend(["--download-path", str(Path(inbox).resolve())])
    return args


def build_cnki_download_script(format_name: str = "pdf") -> str:
    """JavaScript used inside the user's logged-in browser to click CNKI download links."""
    normalized_format = (format_name or "pdf").lower()
    if normalized_format not in {"pdf", "caj", "auto"}:
        raise ValueError(f"unsupported CNKI download format: {format_name}")
    return f"""
(async () => {{
  await new Promise((resolve, reject) => {{
    let attempts = 0;
    const wait = () => {{
      if (
        document.querySelector('.brief h1') ||
        document.querySelector('.wx-tit h1') ||
        document.querySelector('#pdfDown') ||
        document.querySelector('#cajDown')
      ) {{
        resolve();
      }} else if (++attempts > 60) {{
        reject(new Error('detail-page-timeout'));
      }} else {{
        setTimeout(wait, 500);
      }}
    }};
    wait();
  }});

  const captcha = document.querySelector('#tcaptcha_transform_dy');
  if (captcha && captcha.getBoundingClientRect().top >= 0) {{
    return {{ error: 'captcha', message: 'CNKI is showing a slider captcha that must be solved manually.' }};
  }}

  const notLogged = document.querySelector('.downloadlink.icon-notlogged')
    || document.querySelector('[class*="notlogged"]');
  if (notLogged) {{
    return {{ error: 'not_logged_in', message: 'CNKI download requires the user browser session to be logged in.' }};
  }}

  const title = (
    document.querySelector('.brief h1')?.innerText
    || document.querySelector('.wx-tit h1')?.innerText
    || document.title
    || ''
  ).trim().replace(/\\s*网络首发\\s*$/, '');
  const pdfLink = document.querySelector('#pdfDown') || document.querySelector('.btn-dlpdf a');
  const cajLink = document.querySelector('#cajDown') || document.querySelector('.btn-dlcaj a');
  const format = {json.dumps(normalized_format)};

  if ((format === 'pdf' || format === 'auto') && pdfLink) {{
    pdfLink.click();
    return {{ status: 'downloading', format: 'PDF', title, href: pdfLink.href || null }};
  }}
  if ((format === 'caj' || format === 'auto') && cajLink) {{
    cajLink.click();
    return {{ status: 'downloading', format: 'CAJ', title, href: cajLink.href || null }};
  }}
  return {{
    error: 'no_download_link',
    message: 'No CNKI PDF/CAJ download link was found on the current detail page.',
    title,
    hasPDF: Boolean(pdfLink),
    hasCAJ: Boolean(cajLink)
  }};
}})()
""".strip()


def probe_authorized_browser(
    *,
    inbox: str | Path | None = None,
    project_root: str | Path | None = None,
    auto_connect: bool = True,
    cdp: str | None = None,
    profile: str | None = None,
    session_name: str | None = None,
    open_cnki: bool = True,
) -> dict[str, Any]:
    inbox_path = resolve_inbox(inbox, project_root=project_root)
    _ensure_download_inbox(inbox_path, project_root=project_root)
    base_args = build_agent_browser_args(
        inbox=inbox_path,
        auto_connect=auto_connect,
        cdp=cdp,
        profile=profile,
        session_name=session_name,
    )
    checks: dict[str, Any] = {
        "schema_version": "cnki_authorized_browser_probe.v1",
        "generated_at": _utc_now(),
        "mode": "report_only",
        "source_files_written": False,
        "inbox": str(inbox_path),
        "agent_browser": base_args[0],
        "auto_connect": auto_connect,
        "cdp": cdp,
        "profile": profile,
        "session_name": session_name,
    }
    cdp_result = _run_agent_browser(base_args, ["get", "cdp-url"], timeout_seconds=45)
    checks["cdp_url_ok"] = cdp_result["ok"]
    checks["cdp_url"] = cdp_result["stdout"].strip().strip('"') if cdp_result["ok"] else None
    checks["cdp_error"] = cdp_result["stderr"] if not cdp_result["ok"] else None

    if open_cnki:
        _run_agent_browser(base_args, ["open", "https://www.cnki.net/"], timeout_seconds=60)
        _run_agent_browser(base_args, ["wait", "--load", "networkidle"], timeout_seconds=60)
    title = _run_agent_browser(base_args, ["get", "title"], timeout_seconds=45)
    url = _run_agent_browser(base_args, ["get", "url"], timeout_seconds=45)
    body = _run_agent_browser(base_args, ["get", "text", "body"], timeout_seconds=60)
    body_text = body["stdout"] if body["ok"] else ""
    checks.update(
        {
            "page_title": title["stdout"].strip().strip('"') if title["ok"] else None,
            "page_url": url["stdout"].strip().strip('"') if url["ok"] else None,
            "cnki_visible": "cnki" in (url["stdout"].lower() if url["ok"] else ""),
            "login_marker_present": any(marker in body_text for marker in ["个人登录", "我的CNKI", "充值", "会员"]),
            "institution_marker_present": "陕西师范大学" in body_text,
            "captcha_marker_present": "拖动下方拼图完成验证" in body_text,
        }
    )
    checks["ok"] = checks["cdp_url_ok"] and bool(checks["page_url"])
    return checks


def download_candidates_with_authorized_browser(
    candidates: list[dict[str, Any]],
    *,
    inbox: str | Path | None = None,
    project_root: str | Path | None = None,
    requested_author: str | None = None,
    requested_affiliation: str | None = None,
    format_name: str = "pdf",
    auto_connect: bool = True,
    cdp: str | None = None,
    profile: str | None = None,
    session_name: str | None = None,
    timeout_seconds: int = 90,
    limit: int | None = None,
    cleanup: bool = False,
    direct_cdp: bool = False,
    stop_on_captcha: bool = True,
) -> dict[str, Any]:
    if direct_cdp:
        return download_candidates_with_direct_cdp(
            candidates,
            inbox=inbox,
            project_root=project_root,
            requested_author=requested_author,
            requested_affiliation=requested_affiliation,
            format_name=format_name,
            cdp=cdp or "http://127.0.0.1:9333",
            timeout_seconds=timeout_seconds,
            limit=limit,
            cleanup=cleanup,
            stop_on_captcha=stop_on_captcha,
        )

    inbox_path = resolve_inbox(inbox, project_root=project_root)
    _ensure_download_inbox(inbox_path, project_root=project_root)
    gate_report = build_candidate_gate_report(
        candidates,
        requested_author=requested_author,
        requested_affiliation=requested_affiliation,
    )
    if not gate_report["download_allowed"]:
        return {
            "schema_version": "cnki_authorized_browser_download.v1",
            "generated_at": _utc_now(),
            "workflow_id": load_workflow_contract()["workflow_id"],
            "ok": False,
            "mode": "authorized_browser_download",
            "source_files_written": False,
            "inbox": str(inbox_path),
            "candidate_gate": gate_report,
            "attempted_count": 0,
            "downloaded_count": 0,
            "items": [],
            "errors": ["candidate-gate-blocked"],
        }

    selected = candidates[:limit] if limit else candidates
    base_args = build_agent_browser_args(
        inbox=inbox_path,
        auto_connect=auto_connect,
        cdp=cdp,
        profile=profile,
        session_name=session_name,
    )
    items: list[dict[str, Any]] = []
    created_paths: list[Path] = []
    captcha_checkpoint: dict[str, Any] | None = None
    for index, candidate in enumerate(selected, start=1):
        detail_url = _candidate_detail_url(candidate)
        item: dict[str, Any] = {
            "index": index,
            "title": candidate.get("title"),
            "detail_url": detail_url,
            "status": "pending",
            "downloaded_file": None,
            "browser_result": None,
            "errors": [],
        }
        if not detail_url:
            item["status"] = "blocked"
            item["errors"].append("missing-detail-url")
            items.append(item)
            continue

        before = _inbox_file_snapshot(inbox_path)
        open_result = _run_agent_browser(base_args, ["open", detail_url], timeout_seconds=60)
        if not open_result["ok"]:
            item["status"] = "browser-open-failed"
            item["errors"].append(open_result["stderr"] or open_result["stdout"])
            items.append(item)
            continue
        _run_agent_browser(base_args, ["wait", "--load", "networkidle"], timeout_seconds=60)
        script = build_cnki_download_script(format_name)
        encoded = base64.b64encode(script.encode("utf-8")).decode("ascii")
        trigger = _run_agent_browser(base_args, ["eval", "-b", encoded], timeout_seconds=60)
        item["browser_result"] = _parse_agent_browser_json(trigger["stdout"])
        if not trigger["ok"]:
            item["status"] = "browser-trigger-failed"
            item["errors"].append(trigger["stderr"] or trigger["stdout"])
            items.append(item)
            continue
        if isinstance(item["browser_result"], dict) and item["browser_result"].get("error"):
            if item["browser_result"].get("error") == "captcha" and stop_on_captcha:
                item["status"] = "captcha-required"
                item["errors"].append("captcha-required")
                items.append(item)
                captcha_checkpoint = _build_captcha_checkpoint(
                    selected=selected,
                    current_index=index,
                    items=items,
                    inbox_path=inbox_path,
                    project_root=project_root,
                    cdp=cdp,
                    format_name=format_name,
                    mode="authorized_browser_download",
                    direct_cdp=False,
                )
                break
            item["status"] = "browser-rejected"
            item["errors"].append(str(item["browser_result"].get("error")))
            items.append(item)
            continue
        downloaded = _wait_for_new_download(inbox_path, before, timeout_seconds=timeout_seconds)
        if downloaded is None:
            item["status"] = "no-file-created"
            item["errors"].append("download-timeout")
        else:
            created_paths.append(downloaded)
            item["status"] = "downloaded"
            item["downloaded_file"] = _download_file_record(downloaded)
        items.append(item)

    if cleanup:
        for path in created_paths:
            _delete_downloaded_test_file(path, inbox_path)
        for item in items:
            if item.get("downloaded_file"):
                item["downloaded_file"]["deleted_after_test"] = True

    downloaded_count = sum(1 for item in items if item["status"] == "downloaded")
    errors = [f"{item['index']}:{err}" for item in items for err in item["errors"]]
    return {
        "schema_version": "cnki_authorized_browser_download.v1",
        "generated_at": _utc_now(),
        "workflow_id": load_workflow_contract()["workflow_id"],
        "ok": downloaded_count == len(selected) and bool(selected),
        "mode": "authorized_browser_download",
        "source_files_written": False,
        "inbox": str(inbox_path),
        "candidate_gate": gate_report,
        "queued_count": len(selected),
        "attempted_count": len(items),
        "downloaded_count": downloaded_count,
        "remaining_count": len(captcha_checkpoint.get("resume_candidates", [])) if captcha_checkpoint else 0,
        "cleanup": cleanup,
        "captcha_checkpoint": captcha_checkpoint,
        "next_steps": _captcha_next_steps() if captcha_checkpoint else [],
        "items": items,
        "errors": errors,
    }


def download_candidates_with_direct_cdp(
    candidates: list[dict[str, Any]],
    *,
    inbox: str | Path | None = None,
    project_root: str | Path | None = None,
    requested_author: str | None = None,
    requested_affiliation: str | None = None,
    format_name: str = "pdf",
    cdp: str = "http://127.0.0.1:9333",
    timeout_seconds: int = 90,
    limit: int | None = None,
    cleanup: bool = False,
    stop_on_captcha: bool = True,
) -> dict[str, Any]:
    inbox_path = resolve_inbox(inbox, project_root=project_root)
    _ensure_download_inbox(inbox_path, project_root=project_root)
    gate_report = build_candidate_gate_report(
        candidates,
        requested_author=requested_author,
        requested_affiliation=requested_affiliation,
    )
    if not gate_report["download_allowed"]:
        return _browser_download_report(
            ok=False,
            inbox_path=inbox_path,
            gate_report=gate_report,
            queued_count=0,
            attempted_count=0,
            downloaded_count=0,
            cleanup=cleanup,
            items=[],
            errors=["candidate-gate-blocked"],
            mode="direct_cdp_download",
        )

    client = _CdpClient.from_endpoint(cdp)
    created_paths: list[Path] = []
    items: list[dict[str, Any]] = []
    selected = candidates[:limit] if limit else candidates
    captcha_checkpoint: dict[str, Any] | None = None
    try:
        client.call(
            "Browser.setDownloadBehavior",
            {"behavior": "allow", "downloadPath": str(inbox_path), "eventsEnabled": True},
        )
        for index, candidate in enumerate(selected, start=1):
            detail_url = _candidate_detail_url(candidate)
            item: dict[str, Any] = {
                "index": index,
                "title": candidate.get("title"),
                "detail_url": detail_url,
                "status": "pending",
                "downloaded_file": None,
                "browser_result": None,
                "errors": [],
            }
            if not detail_url:
                item["status"] = "blocked"
                item["errors"].append("missing-detail-url")
                items.append(item)
                continue
            target_id = None
            try:
                target_id = client.call("Target.createTarget", {"url": detail_url})["targetId"]
                session_id = client.call("Target.attachToTarget", {"targetId": target_id, "flatten": True})["sessionId"]
                state = _wait_for_cdp_detail_or_gate(client, session_id, timeout_seconds=min(timeout_seconds, 90))
                item["browser_state"] = state
                if state.get("captcha_required"):
                    item["status"] = "captcha-required"
                    item["errors"].append("captcha-required")
                    items.append(item)
                    if stop_on_captcha:
                        captcha_checkpoint = _build_captcha_checkpoint(
                            selected=selected,
                            current_index=index,
                            items=items,
                            inbox_path=inbox_path,
                            project_root=project_root,
                            cdp=cdp,
                            format_name=format_name,
                            mode="direct_cdp_download",
                            direct_cdp=True,
                        )
                        break
                    continue
                if not state.get("download_link_present"):
                    item["status"] = "no-download-link"
                    item["errors"].append("no-download-link")
                    items.append(item)
                    continue
                before = _inbox_file_snapshot(inbox_path)
                item["browser_result"] = _cdp_resolve_download_link(client, session_id, format_name)
                if isinstance(item["browser_result"], dict) and item["browser_result"].get("error"):
                    item["status"] = "browser-rejected"
                    item["errors"].append(str(item["browser_result"].get("error")))
                    items.append(item)
                    continue
                client.call(
                    "Page.navigate",
                    {
                        "url": item["browser_result"]["href"],
                        "referrer": detail_url,
                        "transitionType": "link",
                    },
                    session_id=session_id,
                    timeout_seconds=30,
                )
                downloaded = _wait_for_new_download(inbox_path, before, timeout_seconds=timeout_seconds)
                if downloaded is None:
                    item["status"] = "no-file-created"
                    item["errors"].append("download-timeout")
                else:
                    created_paths.append(downloaded)
                    item["status"] = "downloaded"
                    item["downloaded_file"] = _download_file_record(downloaded)
                items.append(item)
            finally:
                if target_id:
                    try:
                        client.call("Target.closeTarget", {"targetId": target_id}, timeout_seconds=10)
                    except Exception:
                        pass
    finally:
        client.close()

    if cleanup:
        for path in created_paths:
            _delete_downloaded_test_file(path, inbox_path)
        for item in items:
            if item.get("downloaded_file"):
                item["downloaded_file"]["deleted_after_test"] = True

    downloaded_count = sum(1 for item in items if item["status"] == "downloaded")
    errors = [f"{item['index']}:{err}" for item in items for err in item["errors"]]
    return _browser_download_report(
        ok=downloaded_count == len(selected) and bool(selected),
        inbox_path=inbox_path,
        gate_report=gate_report,
        queued_count=len(selected),
        attempted_count=len(items),
        downloaded_count=downloaded_count,
        cleanup=cleanup,
        items=items,
        errors=errors,
        mode="direct_cdp_download",
        captcha_checkpoint=captcha_checkpoint,
    )


def discover_candidates_with_direct_cdp(
    *,
    query: str | None = None,
    search_type: str = "author",
    sort: str = "cited",
    author: str | None = None,
    requested_author: str | None = None,
    affiliation: str | None = None,
    cdp: str = "http://127.0.0.1:9333",
    pages: int = 1,
    limit: int | None = None,
    timeout_seconds: int = 90,
) -> dict[str, Any]:
    _ensure_direct_cdp_runtime()
    query_value = query or author
    if not query_value:
        raise ValueError("query is required for CNKI candidate discovery")
    if pages < 1:
        raise ValueError("pages must be >= 1")
    normalized_search_type = _normalize_cnki_search_type(search_type)
    normalized_sort = _normalize_cnki_sort(sort)
    gate_author = requested_author
    if gate_author is None and author:
        gate_author = author
    if gate_author is None and normalized_search_type == "author":
        gate_author = query_value
    client = _CdpClient.from_endpoint(cdp)
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    errors: list[str] = []
    target_id = None
    try:
        search_url = _cnki_search_url(query_value, normalized_search_type)
        target_id = client.call("Target.createTarget", {"url": search_url})["targetId"]
        session_id = client.call("Target.attachToTarget", {"targetId": target_id, "flatten": True})["sessionId"]
        _wait_for_cdp_search_results(client, session_id, timeout_seconds=min(timeout_seconds, 90))
        _cdp_apply_sort(client, session_id, normalized_sort)

        seen: set[str] = set()
        for page_number in range(1, pages + 1):
            rows = _cdp_extract_result_rows(client, session_id)
            for row in rows:
                key = normalize_cnki_text(row.get("title")) or str(row.get("detail_url"))
                if not key or key in seen:
                    continue
                seen.add(key)
                candidate = _candidate_from_result_row(row)
                detail = _cdp_extract_detail_evidence(
                    client,
                    detail_url=candidate.get("detail_url") or "",
                    affiliation=affiliation,
                    timeout_seconds=min(timeout_seconds, 90),
                )
                candidate.update(detail.get("candidate_patch", {}))
                candidate["discovery"] = {
                    "source": "cnki-browser-search",
                    "search_type": normalized_search_type,
                    "sort": normalized_sort,
                    "result_page": page_number,
                    "result_rank": row.get("rank"),
                }
                gate = evaluate_candidate_gate(
                    candidate,
                    requested_author=gate_author,
                    requested_affiliation=affiliation,
                )
                if gate["download_allowed"]:
                    accepted.append(candidate)
                else:
                    rejected.append(
                        {
                            **candidate,
                            "gate": gate,
                            "detail_status": detail.get("status"),
                        }
                    )
                if limit is not None and len(accepted) >= limit:
                    break
            if limit is not None and len(accepted) >= limit:
                break
            if page_number < pages and not _cdp_go_to_next_results_page(client, session_id):
                errors.append(f"page-{page_number}:next-page-unavailable")
                break
        if limit is not None:
            accepted = accepted[:limit]
        gate_report = build_candidate_gate_report(
            accepted,
            requested_author=gate_author,
            requested_affiliation=affiliation,
        )
        return {
            "schema_version": "cnki_candidate_discovery.v1",
            "generated_at": _utc_now(),
            "workflow_id": load_workflow_contract()["workflow_id"],
            "ok": bool(accepted) and (limit is None or len(accepted) >= min(limit, len(accepted))),
            "mode": "direct_cdp_discovery",
            "source_files_written": False,
            "search_url": search_url,
            "query": query_value,
            "search_type": normalized_search_type,
            "requested_author": gate_author,
            "requested_affiliation": affiliation,
            "sort": normalized_sort,
            "pages_requested": pages,
            "accepted_count": len(accepted),
            "rejected_count": len(rejected),
            "candidates": accepted,
            "rejected_candidates": rejected,
            "candidate_gate": gate_report,
            "errors": errors,
        }
    finally:
        if target_id:
            try:
                client.call("Target.closeTarget", {"targetId": target_id}, timeout_seconds=10)
            except Exception:
                pass
        client.close()


def batch_download_search_candidates_with_direct_cdp(
    *,
    query: str | None = None,
    search_type: str = "author",
    sort: str = "cited",
    author: str | None = None,
    requested_author: str | None = None,
    affiliation: str | None = None,
    inbox: str | Path | None = None,
    project_root: str | Path | None = None,
    format_name: str = "pdf",
    cdp: str = "http://127.0.0.1:9333",
    pages: int = 1,
    limit: int = 10,
    timeout_seconds: int = 90,
    cleanup: bool = False,
) -> dict[str, Any]:
    _ensure_direct_cdp_runtime()
    query_value = query or author
    normalized_search_type = _normalize_cnki_search_type(search_type)
    gate_author = requested_author
    if gate_author is None and author:
        gate_author = author
    if gate_author is None and normalized_search_type == "author":
        gate_author = query_value
    discovery = discover_candidates_with_direct_cdp(
        query=query_value,
        search_type=normalized_search_type,
        sort=sort,
        requested_author=gate_author,
        affiliation=affiliation,
        cdp=cdp,
        pages=pages,
        limit=limit,
        timeout_seconds=timeout_seconds,
    )
    candidates = discovery.get("candidates", [])
    if not candidates:
        return {
            "schema_version": "cnki_search_batch_download.v1",
            "generated_at": _utc_now(),
            "workflow_id": load_workflow_contract()["workflow_id"],
            "ok": False,
            "mode": "direct_cdp_discover_then_download",
            "source_files_written": False,
            "discovery": discovery,
            "download": None,
            "errors": ["no-verified-candidates"],
        }
    download = download_candidates_with_direct_cdp(
        candidates,
        inbox=inbox,
        project_root=project_root,
        requested_author=gate_author,
        requested_affiliation=affiliation,
        format_name=format_name,
        cdp=cdp,
        timeout_seconds=timeout_seconds,
        limit=limit,
        cleanup=cleanup,
    )
    errors = list(discovery.get("errors") or []) + list(download.get("errors") or [])
    captcha_checkpoint = download.get("captcha_checkpoint") if isinstance(download, dict) else None
    return {
        "schema_version": "cnki_search_batch_download.v1",
        "generated_at": _utc_now(),
        "workflow_id": load_workflow_contract()["workflow_id"],
        "ok": bool(download.get("ok")),
        "mode": "direct_cdp_discover_then_download",
        "source_files_written": False,
        "query": query_value,
        "search_type": normalized_search_type,
        "sort": _normalize_cnki_sort(sort),
        "requested_author": gate_author,
        "requested_affiliation": affiliation,
        "limit": limit,
        "pages": pages,
        "cleanup": cleanup,
        "discovery": discovery,
        "download": download,
        "captcha_checkpoint": captcha_checkpoint,
        "errors": errors,
    }


def scan_inbox(inbox: str | Path, *, recursive: bool = False) -> list[dict[str, Any]]:
    root = Path(inbox).resolve()
    if not root.exists():
        return []
    pattern = "**/*" if recursive else "*"
    contract = load_workflow_contract()
    allowed = {item.lower() for item in contract["inbox"]["allowed_extensions"]}
    sidecars = {item.lower() for item in contract["inbox"]["metadata_sidecar_extensions"]}
    max_bytes = int(contract["inbox"]["max_auto_import_mb"]) * 1024 * 1024
    items: list[dict[str, Any]] = []
    for path in sorted(root.glob(pattern)):
        if not path.is_file():
            continue
        ext = path.suffix.lower()
        size = path.stat().st_size
        action, eligible = classify_file(ext, size, allowed, sidecars, max_bytes)
        item = {
            "path": str(path),
            "name": path.name,
            "extension": ext,
            "size_bytes": size,
            "sha256": sha256_file(path),
            "action": action,
            "zotero_auto_candidate": eligible,
            "title_guess": path.stem,
        }
        items.append(item)
    return items


def classify_file(
    extension: str,
    size_bytes: int,
    allowed_extensions: set[str],
    metadata_sidecars: set[str],
    max_auto_import_bytes: int,
) -> tuple[str, bool]:
    if extension == ".pdf" and extension in allowed_extensions:
        if size_bytes <= max_auto_import_bytes:
            return "local_pdf_add_from_file", True
        return "manual_pdf_too_large", False
    if extension == ".caj" and extension in allowed_extensions:
        return "manual_caj_attachment", False
    if extension in metadata_sidecars:
        return "metadata_review", False
    return "ignored", False


def build_inbox_audit(
    *,
    inbox: str | Path | None = None,
    project_root: str | Path | None = None,
    recursive: bool = False,
) -> dict[str, Any]:
    inbox_path = resolve_inbox(inbox, project_root=project_root)
    files = scan_inbox(inbox_path, recursive=recursive)
    scope = "project" if project_root is not None else "environment_fallback"
    return {
        "schema_version": "cnki_zotero_inbox_audit.v1",
        "generated_at": _utc_now(),
        "workflow_id": load_workflow_contract()["workflow_id"],
        "mode": "report_only",
        "scope": scope,
        "project_root": str(Path(project_root).expanduser().resolve()) if project_root is not None else None,
        "source_files_written": False,
        "inbox": str(inbox_path),
        "inbox_exists": inbox_path.exists(),
        "recursive": recursive,
        "file_count": len(files),
        "by_action": dict(sorted(Counter(item["action"] for item in files).items())),
        "files": files,
        "zotero_mcp_import_plan": build_zotero_import_plan(files),
    }


def normalize_cnki_text(value: Any) -> str:
    return "".join(str(value or "").split()).lower()


def evaluate_candidate_gate(
    candidate: dict[str, Any],
    *,
    requested_author: str | None = None,
    requested_affiliation: str | None = None,
) -> dict[str, Any]:
    """Block downloads when an author+affiliation request lacks affiliation evidence."""
    contract = load_workflow_contract()
    policy = contract["candidate_selection"]["author_affiliation_policy"]
    accepted_sources = set(policy["accepted_evidence_sources"])
    errors: list[str] = []
    warnings: list[str] = []

    author_norm = normalize_cnki_text(requested_author)
    affiliation_norm = normalize_cnki_text(requested_affiliation)
    authors = candidate.get("authors") or []
    author_pool = [normalize_cnki_text(item) for item in authors]
    if author_norm and not any(author_norm in item or item in author_norm for item in author_pool):
        errors.append("author-not-matched")

    evidence_sources = set(candidate.get("evidence_sources") or [])
    accepted_evidence_sources = sorted(evidence_sources & accepted_sources)
    affiliations = candidate.get("institutions") or candidate.get("affiliations") or []
    evidence_texts = (
        list(affiliations)
        + list(candidate.get("evidence_texts") or [])
        + list(candidate.get("snippets") or [])
    )
    if affiliation_norm:
        if not accepted_evidence_sources:
            errors.append("missing-accepted-affiliation-evidence-source")
        evidence_pool = [normalize_cnki_text(item) for item in evidence_texts]
        if not any(affiliation_norm in item for item in evidence_pool):
            errors.append("affiliation-not-found-in-evidence")
    elif policy.get("required_when_affiliation_requested") is True:
        warnings.append("no-affiliation-requested")

    status = "verified" if not errors else "blocked"
    return {
        "title": candidate.get("title"),
        "authors": authors,
        "requested_author": requested_author,
        "requested_affiliation": requested_affiliation,
        "status": status,
        "download_allowed": status == "verified",
        "accepted_evidence_sources": accepted_evidence_sources,
        "errors": errors,
        "warnings": warnings,
    }


def build_candidate_gate_report(
    candidates: list[dict[str, Any]],
    *,
    requested_author: str | None = None,
    requested_affiliation: str | None = None,
) -> dict[str, Any]:
    items = [
        evaluate_candidate_gate(
            candidate,
            requested_author=requested_author,
            requested_affiliation=requested_affiliation,
        )
        for candidate in candidates
    ]
    return {
        "schema_version": "cnki_zotero_candidate_gate.v1",
        "generated_at": _utc_now(),
        "workflow_id": load_workflow_contract()["workflow_id"],
        "mode": "report_only",
        "requested_author": requested_author,
        "requested_affiliation": requested_affiliation,
        "candidate_count": len(items),
        "verified_count": sum(1 for item in items if item["status"] == "verified"),
        "blocked_count": sum(1 for item in items if item["status"] == "blocked"),
        "download_allowed": bool(items) and all(item["download_allowed"] for item in items),
        "items": items,
        "gate_rule": "When affiliation is requested, author-only search results and full-text keyword matches are not sufficient for download. Use advanced author+affiliation search, detail-page author affiliation, or metadata sidecar evidence.",
    }


def build_zotero_import_plan(files: list[dict[str, Any]]) -> list[dict[str, Any]]:
    plan: list[dict[str, Any]] = []
    tags = load_workflow_contract()["zotero_import"]["default_tags"]
    for item in files:
        if item["action"] == "local_pdf_add_from_file":
            plan.append(
                {
                    "file": item["path"],
                    "tool": "zotero_add_from_file",
                    "requires_review": True,
                    "suggested_arguments": {
                        "file_path": item["path"],
                        "title": item["title_guess"],
                        "tags": tags,
                    },
                }
            )
        elif item["action"] == "manual_caj_attachment":
            plan.append(
                {
                    "file": item["path"],
                    "tool": "manual_review",
                    "requires_review": True,
                    "reason": "CAJ is not a default automatic Zotero MCP import target. Attach manually or convert through a trusted user-approved path.",
                }
            )
    return plan


def write_audit_report(
    report: dict[str, Any],
    output: str | Path | None = None,
    *,
    project_root: str | Path | None = None,
) -> Path:
    if output is None or str(output) == "auto":
        date = datetime.now().strftime("%Y-%m-%d")
        if project_root is None:
            output_path = OUTPUTS_ROOT / "reports" / "cnki-zotero" / f"{date}.json"
        else:
            output_path = Path(project_root).expanduser().resolve() / "outputs" / "reports" / "cnki-zotero" / f"{date}.json"
    else:
        output_path = Path(output)
        if not output_path.is_absolute():
            output_path = (Path(project_root).expanduser().resolve() if project_root is not None else REPO_ROOT) / output_path
    if project_root is not None:
        _assert_project_inbox(output_path, Path(project_root).expanduser().resolve(), require_inbox_leaf=False)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return output_path


def write_cnki_report(
    report: dict[str, Any],
    output: str | Path | None = None,
    *,
    project_root: str | Path | None = None,
    prefix: str = "cnki-zotero",
) -> Path:
    if output is None or str(output) == "auto":
        date = datetime.now().strftime("%Y-%m-%d")
        base = (
            Path(project_root).expanduser().resolve() / "outputs" / "reports" / prefix
            if project_root is not None
            else OUTPUTS_ROOT / "reports" / prefix
        )
        output_path = base / f"{date}.json"
    else:
        output_path = Path(output)
        if not output_path.is_absolute():
            output_path = (Path(project_root).expanduser().resolve() if project_root is not None else REPO_ROOT) / output_path
    if project_root is not None:
        _assert_project_inbox(output_path, Path(project_root).expanduser().resolve(), require_inbox_leaf=False)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return output_path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _run_agent_browser(base_args: list[str], command: list[str], *, timeout_seconds: int) -> dict[str, Any]:
    completed = subprocess.run(
        base_args + command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout_seconds,
    )
    return {
        "ok": completed.returncode == 0,
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def _parse_agent_browser_json(text: str) -> Any:
    stripped = (text or "").strip()
    if not stripped:
        return None
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        return stripped


def _browser_download_report(
    *,
    ok: bool,
    inbox_path: Path,
    gate_report: dict[str, Any],
    queued_count: int,
    attempted_count: int,
    downloaded_count: int,
    cleanup: bool,
    items: list[dict[str, Any]],
    errors: list[str],
    mode: str,
    captcha_checkpoint: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": "cnki_authorized_browser_download.v1",
        "generated_at": _utc_now(),
        "workflow_id": load_workflow_contract()["workflow_id"],
        "ok": ok,
        "mode": mode,
        "source_files_written": False,
        "inbox": str(inbox_path),
        "candidate_gate": gate_report,
        "queued_count": queued_count,
        "attempted_count": attempted_count,
        "downloaded_count": downloaded_count,
        "remaining_count": len(captcha_checkpoint.get("resume_candidates", [])) if captcha_checkpoint else 0,
        "cleanup": cleanup,
        "captcha_checkpoint": captcha_checkpoint,
        "next_steps": _captcha_next_steps() if captcha_checkpoint else [],
        "items": items,
        "errors": errors,
    }


def _build_captcha_checkpoint(
    *,
    selected: list[dict[str, Any]],
    current_index: int,
    items: list[dict[str, Any]],
    inbox_path: Path,
    project_root: str | Path | None,
    cdp: str | None,
    format_name: str,
    mode: str,
    direct_cdp: bool,
) -> dict[str, Any]:
    remaining = selected[max(current_index - 1, 0) :]
    project = str(Path(project_root).expanduser().resolve()) if project_root is not None else None
    downloaded_count = sum(1 for item in items if item.get("status") == "downloaded")
    command = [
        "python",
        "-m",
        "skills.scripts.envctl",
        "cnki-zotero",
        "browser-download",
        "--input",
        "<previous-report-or-captcha-queue.json>",
        "--format",
        format_name,
        "--output",
        "auto",
    ]
    if project is not None:
        command.extend(["--project-root", project])
    else:
        command.extend(["--inbox", str(inbox_path)])
    if direct_cdp:
        command.append("--direct-cdp")
    if cdp:
        command.extend(["--cdp", str(cdp)])
    return {
        "schema_version": "cnki_captcha_checkpoint.v1",
        "status": "manual_verification_required",
        "reason": "CNKI showed a visible slider or security verification page. The workflow stopped instead of trying to bypass it.",
        "current_index": current_index,
        "queued_count": len(selected),
        "attempted_count": len(items),
        "downloaded_count": downloaded_count,
        "remaining_count": len(remaining),
        "resume_candidates": remaining,
        "inbox": str(inbox_path),
        "project_root": project,
        "mode": mode,
        "direct_cdp": direct_cdp,
        "cdp": cdp,
        "resume_command_hint": " ".join(command),
        "manual_action": "Use the visible logged-in CNKI browser window to complete the slider verification, then rerun browser-download with this report or the resume_candidates list as --input.",
    }


def _captcha_next_steps() -> list[str]:
    return [
        "Do not automate or bypass the slider verification.",
        "Complete the CNKI slider verification manually in the visible logged-in browser window.",
        "Rerun browser-download with the previous report path as --input; envctl will read captcha_checkpoint.resume_candidates and continue from the interrupted item.",
        "Keep batches small and leave a short pause between runs if CNKI repeatedly asks for verification.",
    ]


class _CdpClient:
    def __init__(self, websocket_url: str):
        import websocket  # type: ignore[import-not-found]

        self._websocket = websocket.create_connection(websocket_url, timeout=30, suppress_origin=True)
        self._next_id = 1

    @classmethod
    def from_endpoint(cls, endpoint: str) -> "_CdpClient":
        return cls(_resolve_cdp_websocket_url(endpoint))

    def call(
        self,
        method: str,
        params: dict[str, Any] | None = None,
        *,
        session_id: str | None = None,
        timeout_seconds: int = 30,
    ) -> dict[str, Any]:
        message: dict[str, Any] = {"id": self._next_id, "method": method}
        if params is not None:
            message["params"] = params
        if session_id:
            message["sessionId"] = session_id
        request_id = self._next_id
        self._next_id += 1
        self._websocket.send(json.dumps(message))
        deadline = time.time() + timeout_seconds
        while time.time() < deadline:
            payload = json.loads(self._websocket.recv())
            if payload.get("id") == request_id:
                if "error" in payload:
                    raise RuntimeError(payload["error"])
                return payload.get("result", {})
        raise TimeoutError(method)

    def close(self) -> None:
        self._websocket.close()


def _resolve_cdp_websocket_url(endpoint: str) -> str:
    value = (endpoint or "").strip()
    if value.startswith(("ws://", "wss://")):
        return value
    if value.isdigit():
        value = f"http://127.0.0.1:{value}"
    if not value.startswith(("http://", "https://")):
        value = f"http://{value}"
    version_url = value.rstrip("/") + "/json/version"
    with urllib.request.urlopen(version_url, timeout=10) as response:
        data = json.loads(response.read().decode("utf-8"))
    websocket_url = data.get("webSocketDebuggerUrl")
    if not websocket_url:
        raise ValueError(f"CDP endpoint did not expose webSocketDebuggerUrl: {version_url}")
    return websocket_url


def _normalize_cnki_search_type(value: str | None) -> str:
    aliases = {
        "author": "author",
        "作者": "author",
        "au": "author",
        "subject": "subject",
        "主题": "subject",
        "su": "subject",
        "keyword": "keyword",
        "keywords": "keyword",
        "关键词": "keyword",
        "ky": "keyword",
        "title": "title",
        "篇名": "title",
        "题名": "title",
        "ti": "title",
        "affiliation": "affiliation",
        "作者单位": "affiliation",
        "机构": "affiliation",
        "af": "affiliation",
        "fulltext": "fulltext",
        "全文": "fulltext",
        "ft": "fulltext",
        "doi": "doi",
    }
    normalized = str(value or "subject").strip().lower()
    return aliases.get(normalized, normalized)


def _normalize_cnki_sort(value: str | None) -> str:
    aliases = {
        "relevance": "relevance",
        "相关度": "relevance",
        "ffd": "relevance",
        "date": "date",
        "latest": "date",
        "发表时间": "date",
        "最新": "date",
        "pt": "date",
        "cited": "cited",
        "citation": "cited",
        "citations": "cited",
        "被引": "cited",
        "cf": "cited",
        "download": "download",
        "downloads": "download",
        "下载": "download",
        "dfr": "download",
        "composite": "composite",
        "综合": "composite",
        "zh": "composite",
    }
    normalized = str(value or "relevance").strip().lower()
    return aliases.get(normalized, normalized)


def _cnki_search_url(query: str, search_type: str) -> str:
    korder_by_type = {
        "subject": "SU",
        "keyword": "KY",
        "title": "TI",
        "author": "AU",
        "affiliation": "AF",
        "fulltext": "FT",
        "doi": "DOI",
    }
    korder = korder_by_type.get(_normalize_cnki_search_type(search_type), search_type).upper()
    encoded_query = urllib.parse.quote(query)
    encoded_korder = urllib.parse.quote(korder)
    return f"https://kns.cnki.net/kns8s/defaultresult/index?kw={encoded_query}&korder={encoded_korder}"


def _wait_for_cdp_search_results(
    client: _CdpClient,
    session_id: str,
    *,
    timeout_seconds: int,
) -> dict[str, Any]:
    expression = """
(() => {
  const rows = Array.from(document.querySelectorAll('tr'))
    .filter((tr) => tr.querySelector('a.fz14')).length;
  const title = document.title || '';
  const text = document.body?.innerText || '';
  const securityGate = title.includes('安全验证') || location.href.includes('/verify/');
  return {readyState: document.readyState, title, url: location.href, rows, securityGate, text: text.slice(0, 200)};
})()
""".strip()
    deadline = time.time() + timeout_seconds
    last: dict[str, Any] = {}
    while time.time() < deadline:
        result = client.call(
            "Runtime.evaluate",
            {"expression": expression, "returnByValue": True},
            session_id=session_id,
            timeout_seconds=10,
        )
        value = result.get("result", {}).get("value") or {}
        last = value if isinstance(value, dict) else {"raw": value}
        if last.get("securityGate"):
            raise RuntimeError("CNKI search is showing a security verification page")
        if int(last.get("rows") or 0) > 0:
            return last
        time.sleep(0.5)
    raise TimeoutError(f"CNKI search results did not load: {last}")


def _cdp_apply_sort(client: _CdpClient, session_id: str, sort: str) -> None:
    selectors = {
        "relevance": "#FFD",
        "date": "#PT",
        "cited": "#CF",
        "download": "#DFR",
        "composite": "#ZH",
    }
    target = selectors.get(_normalize_cnki_sort(sort))
    if not target:
        raise ValueError(f"unsupported CNKI sort: {sort}")
    # CNKI sometimes keeps a stale visual sort state while the grid uses another
    # order. Click a different stable sort first, then the requested sort.
    intermediate = "#PT" if target != "#PT" else "#FFD"
    for selector in (intermediate, target):
        client.call(
            "Runtime.evaluate",
            {
                "expression": (
                    f"document.querySelector({json.dumps(selector)})?.dispatchEvent("
                    "new MouseEvent('click', {bubbles: true, cancelable: true, view: window})); true"
                ),
                "returnByValue": True,
            },
            session_id=session_id,
            timeout_seconds=10,
        )
        time.sleep(4)
        _wait_for_cdp_search_results(client, session_id, timeout_seconds=30)


def _cdp_extract_result_rows(client: _CdpClient, session_id: str) -> list[dict[str, Any]]:
    expression = """
(() => Array.from(document.querySelectorAll('tr')).map((tr) => {
  const titleLink = tr.querySelector('a.fz14')
    || Array.from(tr.querySelectorAll('a')).find((a) => a.href.includes('/kcms2/article/abstract'));
  if (!titleLink) return null;
  const cells = Array.from(tr.children).map((td) => td.innerText.trim().replace(/\\s+/g, ' '));
  const downloadLink = Array.from(tr.querySelectorAll('a'))
    .find((a) => (a.innerText || '').trim() === '下载' && a.href.includes('/bar/download/order'));
  return {
    rank: cells[0] || null,
    title: titleLink.innerText.trim(),
    detail_url: titleLink.href,
    authors_text: cells[2] || '',
    source: cells[3] || '',
    date: cells[4] || '',
    document_type: cells[5] || '',
    cited_count: cells[6] || '',
    download_count: cells[7] || '',
    row_text: tr.innerText.trim().replace(/\\s+/g, ' '),
    search_download_url: downloadLink?.href || null
  };
}).filter(Boolean))()
""".strip()
    result = client.call(
        "Runtime.evaluate",
        {"expression": expression, "returnByValue": True},
        session_id=session_id,
        timeout_seconds=20,
    )
    value = result.get("result", {}).get("value") or []
    return value if isinstance(value, list) else []


def _candidate_from_result_row(row: dict[str, Any]) -> dict[str, Any]:
    authors = [item for item in str(row.get("authors_text") or "").replace("；", ";").split(";") if item]
    return {
        "title": row.get("title"),
        "authors": authors,
        "source": row.get("source"),
        "published_at": row.get("date"),
        "document_type": row.get("document_type"),
        "cited_count": _parse_int(row.get("cited_count")),
        "download_count": _parse_int(row.get("download_count")),
        "detail_url": row.get("detail_url"),
        "cnki_url": row.get("detail_url"),
        "search_download_url": row.get("search_download_url"),
        "evidence_sources": ["cnki-browser-search"],
        "evidence_texts": [row.get("row_text") or ""],
    }


def _cdp_extract_detail_evidence(
    client: _CdpClient,
    *,
    detail_url: str,
    affiliation: str | None,
    timeout_seconds: int,
) -> dict[str, Any]:
    if not detail_url:
        return {"status": "missing-detail-url", "candidate_patch": {}}
    target_id = None
    try:
        target_id = client.call("Target.createTarget", {"url": detail_url})["targetId"]
        session_id = client.call("Target.attachToTarget", {"targetId": target_id, "flatten": True})["sessionId"]
        state = _wait_for_cdp_detail_text(client, session_id, timeout_seconds=timeout_seconds)
        text = state.get("text", "")
        snippets = _extract_keyword_snippets(text, [affiliation or "", "作者单位", "社会学院", "社会学系"])
        institutions = []
        if affiliation and normalize_cnki_text(affiliation) in normalize_cnki_text(text):
            institutions.append(affiliation)
        expression = """
(() => {
  const title = (
    document.querySelector('.brief h1')?.innerText
    || document.querySelector('.wx-tit h1')?.innerText
    || document.title
    || ''
  ).trim();
  const doiMatch = (document.body.innerText || '').match(/DOI[:：]\\s*([^\\s;；]+)/i);
  const links = Array.from(document.querySelectorAll('a')).map((a) => ({
    text: (a.innerText || '').trim(),
    href: a.href,
    id: a.id
  })).filter((a) => a.id === 'pdfDown' || a.id === 'cajDown' || a.text.includes('下载'));
  return {title, doi: doiMatch ? doiMatch[1] : null, download_links: links};
})()
""".strip()
        detail = client.call(
            "Runtime.evaluate",
            {"expression": expression, "returnByValue": True},
            session_id=session_id,
            timeout_seconds=20,
        ).get("result", {}).get("value") or {}
        candidate_patch = {
            "doi": detail.get("doi"),
            "detail_title": detail.get("title"),
            "institutions": institutions,
            "snippets": snippets,
            "evidence_texts": snippets,
            "detail_download_links": detail.get("download_links") or [],
        }
        if institutions or snippets:
            candidate_patch["evidence_sources"] = [
                "cnki-browser-search",
                "detail_page_author_affiliation",
            ]
        return {
            "status": "ok",
            "security_gate_seen": bool(state.get("securityGate")),
            "candidate_patch": candidate_patch,
        }
    except Exception as exc:
        return {"status": "detail-read-failed", "error": str(exc), "candidate_patch": {}}
    finally:
        if target_id:
            try:
                client.call("Target.closeTarget", {"targetId": target_id}, timeout_seconds=10)
            except Exception:
                pass


def _wait_for_cdp_detail_text(
    client: _CdpClient,
    session_id: str,
    *,
    timeout_seconds: int,
) -> dict[str, Any]:
    expression = """
(() => {
  const text = document.body?.innerText || '';
  const title = document.title || '';
  const hasDetail = Boolean(document.querySelector('.brief h1') || document.querySelector('.wx-tit h1'))
    || text.includes('摘要') || text.includes('关键词');
  const securityGate = title.includes('安全验证') || location.href.includes('/verify/');
  return {readyState: document.readyState, title, url: location.href, hasDetail, securityGate, text};
})()
""".strip()
    deadline = time.time() + timeout_seconds
    last: dict[str, Any] = {}
    while time.time() < deadline:
        result = client.call(
            "Runtime.evaluate",
            {"expression": expression, "returnByValue": True},
            session_id=session_id,
            timeout_seconds=10,
        )
        value = result.get("result", {}).get("value") or {}
        last = value if isinstance(value, dict) else {"raw": value}
        if last.get("hasDetail") or last.get("securityGate"):
            return last
        time.sleep(0.5)
    return last


def _cdp_go_to_next_results_page(client: _CdpClient, session_id: str) -> bool:
    before = client.call(
        "Runtime.evaluate",
        {"expression": "document.querySelector('.countPageMark')?.innerText || ''", "returnByValue": True},
        session_id=session_id,
        timeout_seconds=10,
    ).get("result", {}).get("value")
    clicked = client.call(
        "Runtime.evaluate",
        {
            "expression": """
(() => {
  const next = document.querySelector('#Page_next_top')
    || Array.from(document.querySelectorAll('a')).find((a) => (a.innerText || '').trim() === '>>');
  if (!next) return false;
  next.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true, view: window}));
  return true;
})()
""".strip(),
            "returnByValue": True,
        },
        session_id=session_id,
        timeout_seconds=10,
    ).get("result", {}).get("value")
    if not clicked:
        return False
    deadline = time.time() + 30
    while time.time() < deadline:
        time.sleep(1)
        current = client.call(
            "Runtime.evaluate",
            {"expression": "document.querySelector('.countPageMark')?.innerText || ''", "returnByValue": True},
            session_id=session_id,
            timeout_seconds=10,
        ).get("result", {}).get("value")
        if current and current != before:
            _wait_for_cdp_search_results(client, session_id, timeout_seconds=30)
            return True
    return False


def _extract_keyword_snippets(text: str, keywords: list[str], *, radius: int = 140) -> list[str]:
    snippets: list[str] = []
    normalized = str(text or "").replace("\xa0", " ")
    for keyword in [item for item in keywords if item]:
        start = 0
        while True:
            index = normalized.find(keyword, start)
            if index < 0:
                break
            snippet = normalized[max(0, index - radius) : index + len(keyword) + radius]
            compact = " ".join(snippet.split())
            if compact and compact not in snippets:
                snippets.append(compact)
            start = index + len(keyword)
            if len(snippets) >= 5:
                return snippets
    return snippets


def _parse_int(value: Any) -> int | None:
    text = "".join(ch for ch in str(value or "") if ch.isdigit())
    return int(text) if text else None


def _wait_for_cdp_detail_or_gate(
    client: _CdpClient,
    session_id: str,
    *,
    timeout_seconds: int,
) -> dict[str, Any]:
    expression = """
(() => {
  const title = document.title || '';
  const url = location.href;
  const captcha = document.querySelector('#tcaptcha_transform_dy');
  const captchaVisible = captcha ? captcha.getBoundingClientRect().top >= 0 : false;
  const securityGate = title.includes('安全验证') || url.includes('/verify/') || captchaVisible;
  const links = Array.from(document.querySelectorAll('a'));
  const pdf = Boolean(document.querySelector('#pdfDown') || links.find(a => (a.innerText || '').includes('PDF下载')));
  const caj = Boolean(document.querySelector('#cajDown') || links.find(a => (a.innerText || '').includes('CAJ下载')));
  return {readyState: document.readyState, title, url, securityGate, captchaVisible, pdf, caj};
})()
""".strip()
    deadline = time.time() + timeout_seconds
    last: dict[str, Any] = {}
    while time.time() < deadline:
        result = client.call(
            "Runtime.evaluate",
            {"expression": expression, "returnByValue": True},
            session_id=session_id,
            timeout_seconds=10,
        )
        value = result.get("result", {}).get("value") or {}
        last = value if isinstance(value, dict) else {"raw": value}
        if last.get("securityGate"):
            return {"captcha_required": True, "download_link_present": False, **last}
        if last.get("pdf") or last.get("caj"):
            return {"captcha_required": False, "download_link_present": True, **last}
        time.sleep(0.5)
    return {"captcha_required": False, "download_link_present": False, "timeout": True, **last}


def _cdp_resolve_download_link(client: _CdpClient, session_id: str, format_name: str) -> dict[str, Any]:
    normalized_format = (format_name or "pdf").lower()
    if normalized_format not in {"pdf", "caj", "auto"}:
        raise ValueError(f"unsupported CNKI download format: {format_name}")
    expression = f"""
(() => {{
  const format = {json.dumps(normalized_format)};
  const links = Array.from(document.querySelectorAll('a'));
  const title = (
    document.querySelector('.brief h1')?.innerText
    || document.querySelector('.wx-tit h1')?.innerText
    || document.title
    || ''
  ).trim().replace(/\\s*网络首发\\s*$/, '');
  const pdfLink = document.querySelector('#pdfDown') || links.find(a => (a.innerText || '').includes('PDF下载'));
  const cajLink = document.querySelector('#cajDown') || links.find(a => (a.innerText || '').includes('CAJ下载'));
  if ((format === 'pdf' || format === 'auto') && pdfLink?.href) {{
    return {{status: 'download-url-resolved', format: 'PDF', href: pdfLink.href, title}};
  }}
  if ((format === 'caj' || format === 'auto') && cajLink?.href) {{
    return {{status: 'download-url-resolved', format: 'CAJ', href: cajLink.href, title}};
  }}
  return {{error: 'no_download_link', title, hasPDF: Boolean(pdfLink), hasCAJ: Boolean(cajLink)}};
}})()
""".strip()
    result = client.call(
        "Runtime.evaluate",
        {"expression": expression, "returnByValue": True},
        session_id=session_id,
        timeout_seconds=30,
    )
    value = result.get("result", {}).get("value")
    return value if isinstance(value, dict) else {"error": "invalid-download-link-result", "raw": value}


def _candidate_detail_url(candidate: dict[str, Any]) -> str | None:
    for key in ("url", "detail_url", "cnki_url", "paper_url"):
        value = candidate.get(key)
        if isinstance(value, str) and value.startswith(("http://", "https://")):
            return value
    return None


def _ensure_download_inbox(path: Path, *, project_root: str | Path | None = None) -> None:
    if project_root is None:
        _assert_safe_environment_inbox(path)
    else:
        _assert_project_inbox(path, Path(project_root).expanduser().resolve())
    path.mkdir(parents=True, exist_ok=True)


def _inbox_file_snapshot(inbox: Path) -> dict[str, tuple[int, int]]:
    if not inbox.exists():
        return {}
    return {
        str(path.resolve()): (path.stat().st_size, int(path.stat().st_mtime_ns))
        for path in inbox.iterdir()
        if path.is_file()
    }


def _wait_for_new_download(inbox: Path, before: dict[str, tuple[int, int]], *, timeout_seconds: int) -> Path | None:
    deadline = time.time() + timeout_seconds
    stable_seen: dict[str, tuple[int, int]] = {}
    while time.time() < deadline:
        files = [path for path in inbox.iterdir() if path.is_file()]
        pending = [path for path in files if path.suffix.lower() in {".crdownload", ".tmp"}]
        candidates = [
            path
            for path in files
            if str(path.resolve()) not in before
            and path.suffix.lower() not in {".crdownload", ".tmp"}
        ]
        if candidates and not pending:
            newest = max(candidates, key=lambda item: item.stat().st_mtime_ns)
            current = (newest.stat().st_size, int(newest.stat().st_mtime_ns))
            previous = stable_seen.get(str(newest.resolve()))
            if previous == current and current[0] > 0:
                return newest
            stable_seen[str(newest.resolve())] = current
        time.sleep(0.8)
    return None


def _download_file_record(path: Path) -> dict[str, Any]:
    return {
        "path": str(path),
        "name": path.name,
        "extension": path.suffix.lower(),
        "size_bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def _delete_downloaded_test_file(path: Path, inbox: Path) -> None:
    resolved = path.resolve()
    root = inbox.resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"refusing to delete file outside CNKI inbox: {resolved}") from exc
    if resolved.is_file():
        resolved.unlink()


def _assert_safe_environment_inbox(path: Path) -> None:
    resolved = path.resolve()
    repo = REPO_ROOT.resolve()
    try:
        resolved.relative_to(repo)
    except ValueError as exc:
        raise ValueError(f"refusing to create inbox outside repo: {resolved}") from exc
    if "outputs" not in resolved.parts:
        raise ValueError(f"refusing to create CNKI inbox outside ignored outputs tree: {resolved}")


def _assert_project_inbox(path: Path, project_root: Path, *, require_inbox_leaf: bool = True) -> None:
    resolved = path.resolve()
    project = project_root.resolve()
    try:
        relative = resolved.relative_to(project)
    except ValueError as exc:
        raise ValueError(f"refusing CNKI project path outside project root: {resolved}") from exc
    parts = relative.parts
    if not parts or parts[0] != "outputs":
        raise ValueError(f"refusing CNKI project path outside project outputs tree: {resolved}")
    if require_inbox_leaf and "inbox" not in parts:
        raise ValueError(f"refusing CNKI project inbox outside outputs/inbox tree: {resolved}")
