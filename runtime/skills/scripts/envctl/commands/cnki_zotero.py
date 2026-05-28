from __future__ import annotations



import argparse

import json

from pathlib import Path



try:

    from ..cnki_zotero import (

        build_candidate_gate_report,

        build_inbox_audit,

        build_status,

        batch_download_search_candidates_with_direct_cdp,

        discover_candidates_with_direct_cdp,

        download_candidates_with_authorized_browser,

        probe_authorized_browser,

        validate_cnki_zotero_workflow,

        write_audit_report,

        write_cnki_report,

    )

    from ..validator_envelope import exit_code_for_result

except ImportError:  # pragma: no cover

    from envctl.cnki_zotero import (

        build_candidate_gate_report,

        build_inbox_audit,

        build_status,

        batch_download_search_candidates_with_direct_cdp,

        discover_candidates_with_direct_cdp,

        download_candidates_with_authorized_browser,

        probe_authorized_browser,

        validate_cnki_zotero_workflow,

        write_audit_report,

        write_cnki_report,

    )

    from envctl.validator_envelope import exit_code_for_result





def run(args: argparse.Namespace) -> int:

    if args.action == "status":

        report = build_status(

            inbox=args.inbox,

            project_root=args.project_root,

            ensure_inbox=args.ensure_inbox,

            cdp=args.cdp,

            check_cdp=args.check_cdp,

        )

        print(json.dumps(report, ensure_ascii=False, indent=2))

        return 0 if report["ok"] else 1

    if args.action in {"audit-inbox", "ingest-plan"}:

        report = build_inbox_audit(inbox=args.inbox, project_root=args.project_root, recursive=args.recursive)

        if args.output:

            output = None if args.output == "auto" else Path(args.output)

            written = write_audit_report(report, output, project_root=args.project_root)

            report = {**report, "report_written": str(written)}

        print(json.dumps(report, ensure_ascii=False, indent=2))

        return 0

    if args.action == "candidate-gate":

        payload = json.loads(Path(args.input).read_text(encoding="utf-8"))

        candidates = _extract_candidate_list(payload, action=args.action)

        report = build_candidate_gate_report(

            candidates,

            requested_author=args.author,

            requested_affiliation=args.affiliation,

        )

        if args.output:

            output = Path(args.output)

            if not output.is_absolute():

                output = Path.cwd() / output

            output.parent.mkdir(parents=True, exist_ok=True)

            output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

            report = {**report, "report_written": str(output)}

        print(json.dumps(report, ensure_ascii=False, indent=2))

        return 0 if report["download_allowed"] else 1

    if args.action == "browser-probe":

        report = probe_authorized_browser(

            inbox=args.inbox,

            project_root=args.project_root,

            auto_connect=not args.no_auto_connect,

            cdp=args.cdp,

            profile=args.profile,

            session_name=args.session_name,

            open_cnki=not args.no_open_cnki,

        )

        if args.output:

            written = write_cnki_report(

                report,

                None if args.output == "auto" else Path(args.output),

                project_root=args.project_root,

                prefix="cnki-zotero",

            )

            report = {**report, "report_written": str(written)}

        print(json.dumps(report, ensure_ascii=False, indent=2))

        return 0 if report["ok"] else 1

    if args.action == "browser-download":

        payload = json.loads(Path(args.input).read_text(encoding="utf-8"))

        candidates = _extract_candidate_list(payload, action=args.action)

        report = download_candidates_with_authorized_browser(

            candidates,

            inbox=args.inbox,

            project_root=args.project_root,

            requested_author=args.author,

            requested_affiliation=args.affiliation,

            format_name=args.format,

            auto_connect=not args.no_auto_connect,

            cdp=args.cdp,

            profile=args.profile,

            session_name=args.session_name,

            timeout_seconds=args.timeout_seconds,

            limit=args.limit,

            cleanup=args.cleanup,

            direct_cdp=args.direct_cdp,

            stop_on_captcha=not args.no_stop_on_captcha,

        )

        if args.output:

            written = write_cnki_report(

                report,

                None if args.output == "auto" else Path(args.output),

                project_root=args.project_root,

                prefix="cnki-zotero",

            )

            report = {**report, "report_written": str(written)}

        print(json.dumps(report, ensure_ascii=False, indent=2))

        return 0 if report["ok"] else 1

    if args.action in {"browser-discover", "find"}:

        try:

            report = discover_candidates_with_direct_cdp(

                query=args.query,

                search_type=args.search_type,

                sort=args.sort,

                author=args.author,

                requested_author=args.requested_author,

                affiliation=args.affiliation,

                cdp=args.cdp,

                pages=args.pages,

                limit=args.limit,

                timeout_seconds=args.timeout_seconds,

            )

        except Exception as exc:

            report = _cnki_runtime_error_report(args.action, exc, cdp=args.cdp)

        if args.output:

            written = write_cnki_report(

                report,

                None if args.output == "auto" else Path(args.output),

                project_root=getattr(args, "project_root", None),

                prefix="cnki-zotero-discovery",

            )

            report = {**report, "report_written": str(written)}

        print(json.dumps(report, ensure_ascii=False, indent=2))

        return 0 if report["ok"] else 1

    if args.action in {"browser-batch-download", "fetch"}:

        try:

            report = batch_download_search_candidates_with_direct_cdp(

                query=args.query,

                search_type=args.search_type,

                sort=args.sort,

                author=args.author,

                requested_author=args.requested_author,

                affiliation=args.affiliation,

                inbox=args.inbox,

                project_root=args.project_root,

                format_name=args.format,

                cdp=args.cdp,

                pages=args.pages,

                limit=args.limit,

                timeout_seconds=args.timeout_seconds,

                cleanup=args.cleanup,

            )

        except Exception as exc:

            report = _cnki_runtime_error_report(args.action, exc, cdp=args.cdp)

        if args.output:

            written = write_cnki_report(

                report,

                None if args.output == "auto" else Path(args.output),

                project_root=args.project_root,

                prefix="cnki-zotero",

            )

            report = {**report, "report_written": str(written)}

        print(json.dumps(report, ensure_ascii=False, indent=2))

        return 0 if report["ok"] else 1

    if args.action == "validate":

        report = validate_cnki_zotero_workflow()

        print(json.dumps(report, ensure_ascii=False, indent=2))

        return exit_code_for_result(report)

    raise ValueError(f"unsupported cnki-zotero action: {args.action}")





def _cnki_runtime_error_report(action: str, exc: Exception, *, cdp: str | None) -> dict:

    return {

        "schema_version": "cnki_runtime_error.v1",

        "ok": False,

        "mode": "direct_cdp_preflight",

        "action": action,

        "cdp": cdp,

        "error_type": type(exc).__name__,

        "errors": [str(exc)],

        "next_steps": [

            "Run `python -m skills.scripts.envctl cnki-zotero status --check-cdp --cdp 9333` to inspect dependencies and the controlled Chrome endpoint.",

            "If CDP is unreachable, start the controlled CNKI Chrome window with `powershell -ExecutionPolicy Bypass -File skills\\scripts\\open-cnki-controlled-chrome.ps1`.",

            "If websocket-client is missing, install it in the active Python environment; do not downgrade to public visible search as a substitute for controlled CNKI/CSSCI evidence.",

        ],

    }





def _extract_candidate_list(payload: object, *, action: str) -> list[dict]:

    if isinstance(payload, list):

        candidates = payload

    elif isinstance(payload, dict):

        if isinstance(payload.get("candidates"), list):

            candidates = payload["candidates"]

        elif isinstance(payload.get("captcha_checkpoint"), dict) and isinstance(

            payload["captcha_checkpoint"].get("resume_candidates"), list

        ):

            candidates = payload["captcha_checkpoint"]["resume_candidates"]

        elif isinstance(payload.get("download"), dict) and isinstance(

            payload["download"].get("captcha_checkpoint"), dict

        ) and isinstance(payload["download"]["captcha_checkpoint"].get("resume_candidates"), list):

            candidates = payload["download"]["captcha_checkpoint"]["resume_candidates"]

        else:

            candidates = None

    else:

        candidates = None

    if not isinstance(candidates, list) or not all(isinstance(item, dict) for item in candidates):

        raise ValueError(

            f"{action} input must be a JSON list, an object with candidates, or a previous report with captcha_checkpoint.resume_candidates"

        )

    return candidates





def add_parser(subparsers: argparse._SubParsersAction) -> None:

    parser = subparsers.add_parser("cnki-zotero")

    action = parser.add_subparsers(dest="action", required=True)



    validate = action.add_parser("validate")

    validate.set_defaults(func=run)



    status = action.add_parser("status")

    status.add_argument("--project-root", help="Project root. Defaults the inbox to <project>/outputs/inbox/cnki-downloads.")

    status.add_argument("--inbox", help="CNKI download inbox. With --project-root, relative paths resolve under the project.")

    status.add_argument(

        "--ensure-inbox",

        action="store_true",

        help="Create the selected inbox when it is missing. Project mode refuses paths outside project outputs.",

    )

    status.add_argument("--cdp", default="9333", help="Chrome DevTools Protocol port, HTTP endpoint, or WebSocket URL.")

    status.add_argument("--check-cdp", action="store_true", help="Probe the controlled Chrome DevTools endpoint.")

    status.set_defaults(func=run)



    audit = action.add_parser("audit-inbox")

    audit.add_argument("--project-root", help="Project root. Defaults the inbox to <project>/outputs/inbox/cnki-downloads.")

    audit.add_argument("--inbox", help="CNKI download inbox. With --project-root, relative paths resolve under the project.")

    audit.add_argument("--recursive", action="store_true", help="Scan nested folders inside the inbox.")

    audit.add_argument(

        "--output",

        help="Write JSON report to a path, or use 'auto' for project outputs/reports/cnki-zotero/YYYY-MM-DD.json in project mode.",

    )

    audit.set_defaults(func=run)



    ingest = action.add_parser("ingest-plan", help="Scan the CNKI inbox and write a Zotero import plan.")

    ingest.add_argument("--project-root", help="Project root. Defaults the inbox to <project>/outputs/inbox/cnki-downloads.")

    ingest.add_argument("--inbox", help="CNKI download inbox. With --project-root, relative paths resolve under the project.")

    ingest.add_argument("--recursive", action="store_true", help="Scan nested folders inside the inbox.")

    ingest.add_argument("--output", default="auto", help="Write JSON report to a path, or use 'auto'.")

    ingest.set_defaults(func=run)



    gate = action.add_parser("candidate-gate")

    gate.add_argument("--input", required=True, help="JSON list of CNKI candidates, or an object with a candidates list.")

    gate.add_argument("--author", help="Requested author name, for example 陈云松.")

    gate.add_argument("--affiliation", help="Requested author affiliation, for example 南京大学.")

    gate.add_argument("--output", help="Optional JSON report path.")

    gate.set_defaults(func=run)



    browser_probe = action.add_parser("browser-probe")

    browser_probe.add_argument("--project-root", help="Project root. Defaults the inbox to <project>/outputs/inbox/cnki-downloads.")

    browser_probe.add_argument("--inbox", help="CNKI download inbox. With --project-root, relative paths resolve under the project.")

    browser_probe.add_argument("--output", help="Write JSON report to a path, or use 'auto'.")

    browser_probe.add_argument("--no-auto-connect", action="store_true", help="Do not ask agent-browser to attach to the running user Chrome session.")

    browser_probe.add_argument("--cdp", help="Connect to a specific Chrome DevTools Protocol port or URL.")

    browser_probe.add_argument("--profile", help="Use a named or path-based Chrome profile instead of the running browser.")

    browser_probe.add_argument("--session-name", help="Use an agent-browser persistent session name.")

    browser_probe.add_argument("--no-open-cnki", action="store_true", help="Do not navigate the attached browser to cnki.net during the probe.")

    browser_probe.set_defaults(func=run)



    browser_download = action.add_parser("browser-download")

    browser_download.add_argument("--input", required=True, help="JSON list of gated CNKI candidates, or an object with a candidates list.")

    browser_download.add_argument("--project-root", help="Project root. Defaults the inbox to <project>/outputs/inbox/cnki-downloads.")

    browser_download.add_argument("--inbox", help="CNKI download inbox. With --project-root, relative paths resolve under the project.")

    browser_download.add_argument("--author", help="Requested author name, for example 陈云松.")

    browser_download.add_argument("--affiliation", help="Requested author affiliation, for example 南京大学.")

    browser_download.add_argument("--format", choices=["pdf", "caj", "auto"], default="pdf", help="Preferred CNKI full-text format.")

    browser_download.add_argument("--limit", type=int, help="Maximum number of verified candidates to attempt.")

    browser_download.add_argument("--timeout-seconds", type=int, default=90, help="Seconds to wait for each downloaded file.")

    browser_download.add_argument("--cleanup", action="store_true", help="Delete files downloaded during this command after recording the report.")

    browser_download.add_argument("--output", help="Write JSON report to a path, or use 'auto'.")

    browser_download.add_argument("--no-auto-connect", action="store_true", help="Do not ask agent-browser to attach to the running user Chrome session.")

    browser_download.add_argument("--direct-cdp", action="store_true", help="Use direct Chrome DevTools Protocol control instead of agent-browser for download-path control.")

    browser_download.add_argument(

        "--no-stop-on-captcha",

        action="store_true",

        help="Continue to later items after a captcha instead of writing a resumable checkpoint. Not recommended for batch work.",

    )

    browser_download.add_argument("--cdp", help="Connect to a specific Chrome DevTools Protocol port, HTTP endpoint, or WebSocket URL.")

    browser_download.add_argument("--profile", help="Use a named or path-based Chrome profile instead of the running browser.")

    browser_download.add_argument("--session-name", help="Use an agent-browser persistent session name.")

    browser_download.set_defaults(func=run)



    browser_discover = action.add_parser("browser-discover")

    browser_discover.add_argument("--query", help="CNKI search text. If omitted, --author is used as the query.")

    browser_discover.add_argument(

        "--search-type",

        "--field",

        dest="search_type",

        default="author",

        help="Search field: author, subject, keyword, title, affiliation, fulltext, doi, or CNKI korder code.",

    )

    browser_discover.add_argument(

        "--sort",

        default="cited",

        help="Sort order: cited, date/latest, relevance, download, or composite.",

    )

    browser_discover.add_argument("--author", help="Convenience query and gate author, for example 陈云松.")

    browser_discover.add_argument("--requested-author", help="Optional author gate when the query is not an author search.")

    browser_discover.add_argument("--affiliation", help="Optional affiliation gate, for example 南京大学.")

    browser_discover.add_argument("--pages", type=int, default=1, help="Search result pages to scan.")

    browser_discover.add_argument("--limit", type=int, help="Maximum verified candidates to return.")

    browser_discover.add_argument("--timeout-seconds", type=int, default=90, help="Seconds to wait for each browser page.")

    browser_discover.add_argument("--cdp", default="9333", help="Chrome DevTools Protocol port, HTTP endpoint, or WebSocket URL.")

    browser_discover.add_argument("--output", help="Write discovery JSON to this path.")

    browser_discover.set_defaults(func=run)



    find = action.add_parser("find", help="Simple alias for browser-discover. Finds verified CNKI candidates without downloading.")

    find.add_argument("--query", help="CNKI search text. If omitted, --author is used as the query.")

    find.add_argument(

        "--field",

        "--search-type",

        dest="search_type",

        default="subject",

        help="Search field: author, subject, keyword, title, affiliation, fulltext, doi, or CNKI korder code.",

    )

    find.add_argument("--sort", default="relevance", help="Sort order: cited, date/latest, relevance, download, or composite.")

    find.add_argument("--author", help="Convenience query and gate author, for example 陈云松.")

    find.add_argument("--requested-author", help="Optional author gate when the query is not an author search.")

    find.add_argument("--affiliation", help="Optional affiliation gate, for example 南京大学.")

    find.add_argument("--pages", type=int, default=1, help="Search result pages to scan.")

    find.add_argument("--limit", type=int, help="Maximum verified candidates to return.")

    find.add_argument("--timeout-seconds", type=int, default=90, help="Seconds to wait for each browser page.")

    find.add_argument("--cdp", default="9333", help="Chrome DevTools Protocol port, HTTP endpoint, or WebSocket URL.")

    find.add_argument("--output", help="Write discovery JSON to this path.")

    find.set_defaults(func=run)



    browser_batch = action.add_parser("browser-batch-download")

    browser_batch.add_argument("--query", help="CNKI search text. If omitted, --author is used as the query.")

    browser_batch.add_argument(

        "--search-type",

        "--field",

        dest="search_type",

        default="author",

        help="Search field: author, subject, keyword, title, affiliation, fulltext, doi, or CNKI korder code.",

    )

    browser_batch.add_argument(

        "--sort",

        default="cited",

        help="Sort order: cited, date/latest, relevance, download, or composite.",

    )

    browser_batch.add_argument("--author", help="Convenience query and gate author, for example 陈云松.")

    browser_batch.add_argument("--requested-author", help="Optional author gate when the query is not an author search.")

    browser_batch.add_argument("--affiliation", help="Optional affiliation gate, for example 南京大学.")

    browser_batch.add_argument("--project-root", help="Project root. Defaults the inbox to <project>/outputs/inbox/cnki-downloads.")

    browser_batch.add_argument("--inbox", help="CNKI download inbox. With --project-root, relative paths resolve under the project.")

    browser_batch.add_argument("--format", choices=["pdf", "caj", "auto"], default="pdf", help="Preferred CNKI full-text format.")

    browser_batch.add_argument("--pages", type=int, default=1, help="Search result pages to scan.")

    browser_batch.add_argument("--limit", type=int, default=10, help="Maximum verified candidates to download.")

    browser_batch.add_argument("--timeout-seconds", type=int, default=90, help="Seconds to wait for each browser page or download.")

    browser_batch.add_argument("--cleanup", action="store_true", help="Delete files downloaded during this command after recording the report.")

    browser_batch.add_argument("--cdp", default="9333", help="Chrome DevTools Protocol port, HTTP endpoint, or WebSocket URL.")

    browser_batch.add_argument("--output", help="Write JSON report to a path, or use 'auto'.")

    browser_batch.set_defaults(func=run)



    fetch = action.add_parser("fetch", help="Simple CNKI search -> gate -> batch download entry point.")

    fetch.add_argument("--query", help="CNKI search text. If omitted, --author is used as the query.")

    fetch.add_argument(

        "--field",

        "--search-type",

        dest="search_type",

        default="subject",

        help="Search field: author, subject, keyword, title, affiliation, fulltext, doi, or CNKI korder code.",

    )

    fetch.add_argument("--sort", default="relevance", help="Sort order: cited, date/latest, relevance, download, or composite.")

    fetch.add_argument("--author", help="Convenience query and gate author, for example 陈云松.")

    fetch.add_argument("--requested-author", help="Optional author gate when the query is not an author search.")

    fetch.add_argument("--affiliation", help="Optional affiliation gate, for example 南京大学.")

    fetch.add_argument("--project-root", help="Project root. Defaults the inbox to <project>/outputs/inbox/cnki-downloads.")

    fetch.add_argument("--inbox", help="CNKI download inbox. With --project-root, relative paths resolve under the project.")

    fetch.add_argument("--format", choices=["pdf", "caj", "auto"], default="pdf", help="Preferred CNKI full-text format.")

    fetch.add_argument("--pages", type=int, default=1, help="Search result pages to scan.")

    fetch.add_argument("--limit", type=int, default=10, help="Maximum verified candidates to download.")

    fetch.add_argument("--timeout-seconds", type=int, default=90, help="Seconds to wait for each browser page or download.")

    fetch.add_argument("--cleanup", action="store_true", help="Delete files downloaded during this command after recording the report.")

    fetch.add_argument("--cdp", default="9333", help="Chrome DevTools Protocol port, HTTP endpoint, or WebSocket URL.")

    fetch.add_argument("--output", default="auto", help="Write JSON report to a path, or use 'auto'.")

    fetch.set_defaults(func=run)
