from __future__ import annotations



import argparse

import json

import re

import sqlite3

import tomllib

import unicodedata

import urllib.error

import urllib.parse

import urllib.request

import uuid

from dataclasses import dataclass

from datetime import datetime

from pathlib import Path

from typing import Any



try:

    from .path_utils import CATALOG_ROOT, OUTPUTS_ROOT, SKILLS_ROOT

except ImportError:

    from path_utils import CATALOG_ROOT, OUTPUTS_ROOT, SKILLS_ROOT



ROOT = SKILLS_ROOT

SETTINGS_PATH = CATALOG_ROOT / "settings.toml"

OUTPUTS_DIR = OUTPUTS_ROOT / "writing-reference-capture"

DEFAULT_ZOTERO_DB = Path(r"<ZOTERO_HOME>\zotero.sqlite")

CONNECTOR_BASE = "http://127.0.0.1:23119/connector"

USER_AGENT = "CodexResearchEnv/1.0"





class CaptureError(RuntimeError):

    pass





@dataclass

class VerifiedPaper:

    doi: str

    title: str

    authors: list[dict[str, str]]

    year: str

    journal: str

    volume: str

    issue: str

    pages: str

    url: str

    source_url: str

    zotero_item_key: str | None = None

    zotero_item_id: int | None = None





def load_settings() -> dict[str, Any]:

    text = SETTINGS_PATH.read_text(encoding="utf-8")

    return tomllib.loads(text)





def normalize_doi(value: str) -> str:

    text = value.strip()

    text = re.sub(r"^https?://(dx\.)?doi\.org/", "", text, flags=re.I)

    text = re.sub(r"^doi:\s*", "", text, flags=re.I)

    return text.strip().lower()





def resolve_project_slug(project_name: str) -> str:

    normalized = unicodedata.normalize("NFKD", project_name)

    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")

    slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_text.lower()).strip("-")

    if slug:

        return slug

    fallback = re.sub(r"\s+", "-", project_name.strip())

    fallback = re.sub(r"[^\w\u4e00-\u9fff-]+", "", fallback, flags=re.U).strip("-")

    return fallback or "research-project"





def _normalize_name(value: str) -> str:

    text = unicodedata.normalize("NFKC", value).lower()

    return re.sub(r"[\s_\-]+", "", text)





def select_zotero_target(

    targets: list[dict[str, Any]],

    project_name: str,

    requested_target_id: str | None,

    current_target_id: str | None,

    allow_library_root_fallback: bool,

    prefer_current_target: bool,

) -> dict[str, Any]:

    target_map = {target["id"]: target for target in targets}

    if requested_target_id:

        if requested_target_id not in target_map:

            raise CaptureError(f"请求的 Zotero 目标 `{requested_target_id}` 不存在。")

        return target_map[requested_target_id]



    normalized_project = _normalize_name(project_name)

    for target in targets:

        if target["id"].startswith("C") and _normalize_name(str(target["name"])) == normalized_project:

            return target



    if prefer_current_target and current_target_id and current_target_id in target_map:

        return target_map[current_target_id]



    if allow_library_root_fallback:

        for target in targets:

            if str(target["id"]).startswith("L"):

                return target

        raise CaptureError("允许回退到根库，但没有找到可写的 Zotero library 目标。")



    raise CaptureError(

        f"没有找到与项目 `{project_name}` 匹配的现有 Zotero collection，且当前不允许回退到根库。"

    )





def http_json(

    url: str,

    *,

    method: str = "GET",

    payload: dict[str, Any] | None = None,

    headers: dict[str, str] | None = None,

) -> Any:

    body = None

    request_headers = {"User-Agent": USER_AGENT}

    if headers:

        request_headers.update(headers)

    if payload is not None:

        body = json.dumps(payload).encode("utf-8")

        request_headers.setdefault("Content-Type", "application/json")

    request = urllib.request.Request(url, data=body, headers=request_headers, method=method)

    with urllib.request.urlopen(request, timeout=30) as response:

        raw = response.read().decode("utf-8")

        return json.loads(raw) if raw else None





def get_selected_collection() -> dict[str, Any]:

    return http_json(

        f"{CONNECTOR_BASE}/getSelectedCollection",

        method="POST",

        payload={},

        headers={"X-Zotero-Connector-API-Version": "3"},

    )





def save_items(session_id: str, items: list[dict[str, Any]]) -> None:

    http_json(

        f"{CONNECTOR_BASE}/saveItems",

        method="POST",

        payload={"sessionID": session_id, "items": items},

        headers={"X-Zotero-Connector-API-Version": "3"},

    )





def update_session(session_id: str, target_id: str, tags: list[str]) -> None:

    http_json(

        f"{CONNECTOR_BASE}/updateSession",

        method="POST",

        payload={"sessionID": session_id, "target": target_id, "tags": tags, "note": ""},

        headers={"X-Zotero-Connector-API-Version": "3"},

    )





def fetch_doi_csl(doi: str) -> dict[str, Any]:

    encoded = urllib.parse.quote(doi, safe="/")

    try:

        return http_json(

            f"https://doi.org/{encoded}",

            headers={

                "Accept": "application/vnd.citationstyles.csl+json",

            },

        )

    except urllib.error.HTTPError as exc:

        raise CaptureError(f"DOI `{doi}` 无法通过 doi.org 内容协商核验：HTTP {exc.code}") from exc





def _extract_year(metadata: dict[str, Any]) -> str:

    for key in ("issued", "published-print", "published-online", "published"):

        section = metadata.get(key) or {}

        date_parts = section.get("date-parts") or []

        if date_parts and date_parts[0]:

            return str(date_parts[0][0])

    return ""





def verify_paper(doi: str) -> VerifiedPaper:

    metadata = fetch_doi_csl(doi)

    resolved_doi = normalize_doi(str(metadata.get("DOI", "")))

    if resolved_doi != normalize_doi(doi):

        raise CaptureError(f"DOI `{doi}` 的返回结果与请求不一致：`{resolved_doi}`。")



    title = metadata.get("title")

    if isinstance(title, list):

        title = title[0] if title else ""

    if not title:

        raise CaptureError(f"DOI `{doi}` 返回结果缺少标题，不能作为正式引用。")



    container = metadata.get("container-title") or metadata.get("container_title") or ""

    if isinstance(container, list):

        container = container[0] if container else ""



    authors: list[dict[str, str]] = []

    for author in metadata.get("author", []):

        authors.append(

            {

                "given": str(author.get("given", "")).strip(),

                "family": str(author.get("family", "")).strip(),

            }

        )



    source_url = ""

    resource = metadata.get("resource") or {}

    if isinstance(resource, dict):

        primary = resource.get("primary") or {}

        if isinstance(primary, dict):

            source_url = str(primary.get("URL", "")).strip()



    return VerifiedPaper(

        doi=resolved_doi,

        title=str(title).strip(),

        authors=authors,

        year=_extract_year(metadata),

        journal=str(container).strip(),

        volume=str(metadata.get("volume", "")).strip(),

        issue=str(metadata.get("issue", "")).strip(),

        pages=str(metadata.get("page", "")).strip(),

        url=str(metadata.get("URL", "")).strip(),

        source_url=source_url or f"https://doi.org/{resolved_doi}",

    )





def _paper_to_zotero_item(paper: VerifiedPaper) -> dict[str, Any]:

    creators = []

    for author in paper.authors:

        creators.append(

            {

                "creatorType": "author",

                "firstName": author["given"],

                "lastName": author["family"],

            }

        )



    item = {

        "id": paper.doi,

        "itemType": "journalArticle",

        "title": paper.title,

        "creators": creators,

        "publicationTitle": paper.journal,

        "date": paper.year,

        "DOI": paper.doi,

        "url": paper.source_url or paper.url,

        "volume": paper.volume,

        "issue": paper.issue,

        "pages": paper.pages,

    }

    return {key: value for key, value in item.items() if value not in ("", [], None)}





def _sqlite_connection(path: Path) -> sqlite3.Connection:

    uri = f"file:{path.as_posix()}?mode=ro&immutable=1"

    return sqlite3.connect(uri, uri=True)





def find_existing_items_by_doi(dois: list[str], sqlite_path: Path) -> dict[str, dict[str, Any]]:

    if not sqlite_path.exists():

        return {}



    sql = """

    SELECT i.itemID, i.key, LOWER(v.value) AS doi

    FROM items i

    JOIN itemData d ON d.itemID = i.itemID

    JOIN itemDataValues v ON v.valueID = d.valueID

    JOIN fieldsCombined f ON f.fieldID = d.fieldID

    WHERE f.fieldName = 'DOI' AND LOWER(v.value) = ?

    ORDER BY i.itemID DESC

    LIMIT 1

    """

    existing: dict[str, dict[str, Any]] = {}

    with _sqlite_connection(sqlite_path) as connection:

        cursor = connection.cursor()

        for doi in dois:

            row = cursor.execute(sql, (normalize_doi(doi),)).fetchone()

            if row:

                existing[normalize_doi(doi)] = {

                    "item_id": int(row[0]),

                    "item_key": str(row[1]),

                }

    return existing





def enrich_with_zotero_keys(papers: list[VerifiedPaper], sqlite_path: Path) -> None:

    existing = find_existing_items_by_doi([paper.doi for paper in papers], sqlite_path)

    for paper in papers:

        match = existing.get(paper.doi)

        if not match:

            continue

        paper.zotero_item_id = match["item_id"]

        paper.zotero_item_key = match["item_key"]





def _obsidian_root(settings: dict[str, Any]) -> Path:

    obsidian = settings.get("obsidian", {})

    root = Path(obsidian["vault_path"])

    subdir = obsidian.get("vault_subdir")

    return root / subdir if subdir else root





def _safe_ascii_slug(value: str, fallback: str) -> str:

    normalized = unicodedata.normalize("NFKD", value)

    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")

    slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_text.lower()).strip("-")

    return slug or fallback





def _first_author_label(paper: VerifiedPaper) -> str:

    if not paper.authors:

        return "unknown"

    family = paper.authors[0].get("family", "").strip()

    return family or "unknown"





def build_obsidian_note(paper: VerifiedPaper, project_name: str, project_slug: str) -> str:

    authors = [f"{author['family']}, {author['given']}".strip(", ") for author in paper.authors]

    zotero_ref = (

        f"zotero://select/library/items/{paper.zotero_item_key}"

        if paper.zotero_item_key

        else ""

    )

    lines = [

        "---",

        'type: "literature-note"',

        f'title: "{paper.title.replace("\"", "\\\"")}"',

        f"authors: {json.dumps(authors, ensure_ascii=False)}",

        f'year: "{paper.year}"',

        f'doi: "{paper.doi}"',

        f'citekey: "{paper.zotero_item_key or ""}"',

        f'zotero_ref: "{zotero_ref}"',

        f'project: "{project_name}"',

        'status: "captured"',

        'sync_origin: "codex-writing-reference-capture-local"',

        f'last_zotero_sync: "{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}"',

        "tags:",

        "  - literature",

        "  - source/codex-writing",

        f"  - project/{project_slug}",

        "---",

        "",

        "# 一句话判断",

        "",

        f"{paper.title} 是本次写作中已核验并实际纳入论证链的正式文献。",

        "",

        "# 核验信息",

        "",

        f"- 作者：{'; '.join(authors) if authors else '未提取到'}",

        f"- 年份：{paper.year or '未提取到'}",

        f"- 期刊：{paper.journal or '未提取到'}",

        f"- DOI：{paper.doi}",

        f"- 来源：{paper.source_url}",

        "",

        "# 与当前项目的连接",

        "",

        f"- 项目：{project_name}",

        "- 本条文献由 Codex 写作自动入库链路写入 Zotero，并同步到 Obsidian。",

        "",

        "# 后续动作",

        "",

        "- [ ] 补充你的人工摘要",

        "- [ ] 补充关键页码",

        "- [ ] 写入项目综合笔记",

        "",

    ]

    return "\n".join(lines)





def build_project_map(

    project_name: str,

    project_slug: str,

    target: dict[str, Any],

    papers: list[VerifiedPaper],

    degraded_mode: bool,

) -> str:

    now = datetime.now().strftime("%Y-%m-%d")

    lines = [

        "---",

        'type: "project-map"',

        f'project: "{project_name}"',

        f'project_slug: "{project_slug}"',

        f'zotero_collection: "{target["id"]} | {target["name"]}"',

        'status: "active"',

        f'created: "{now}"',

        f'updated: "{now}"',

        "tags:",

        "  - project",

        "  - source/codex-writing",

        "---",

        "",

        "# 项目说明",

        "",

        f"- 项目名：{project_name}",

        f"- Zotero 目标：{target['id']} | {target['name']}",

        f"- 运行模式：{'降级到根库' if degraded_mode else '直接写入现有项目目标'}",

        "",

        "# 已捕获写作来源",

        "",

    ]

    for paper in papers:

        note_name = build_note_filename(paper)

        lines.append(

            f"- [[20-文献/_zotero-sync/{project_slug}/{note_name}|{paper.title}]]"

        )

    lines.extend(

        [

            "",

            "# 当前说明",

            "",

            "- 这是一张由 `writing-reference-capture` 本地链路生成的项目地图。",

            "- 如果你之后在 Zotero 中为该项目预建 collection，再运行一次脚本，就能把条目归到正式项目 collection。",

            "",

        ]

    )

    return "\n".join(lines)





def build_note_filename(paper: VerifiedPaper) -> str:

    year = paper.year or "n.d."

    author = _safe_ascii_slug(_first_author_label(paper), "unknown")

    title = _safe_ascii_slug(paper.title, paper.doi.replace("/", "-"))

    return f"{year} - {author} - {title}.md"





def write_obsidian_outputs(

    settings: dict[str, Any],

    project_name: str,

    project_slug: str,

    target: dict[str, Any],

    papers: list[VerifiedPaper],

    degraded_mode: bool,

) -> dict[str, str]:

    vault_root = _obsidian_root(settings)

    project_map_path = vault_root / "10-项目" / f"{project_slug}.md"

    sync_dir = vault_root / "20-文献" / "_zotero-sync" / project_slug

    sync_dir.mkdir(parents=True, exist_ok=True)

    project_map_path.parent.mkdir(parents=True, exist_ok=True)



    for paper in papers:

        note_path = sync_dir / build_note_filename(paper)

        note_path.write_text(

            build_obsidian_note(paper, project_name=project_name, project_slug=project_slug),

            encoding="utf-8",

        )



    project_map_path.write_text(

        build_project_map(

            project_name=project_name,

            project_slug=project_slug,

            target=target,

            papers=papers,

            degraded_mode=degraded_mode,

        ),

        encoding="utf-8",

    )

    return {

        "project_map": str(project_map_path),

        "sync_dir": str(sync_dir),

    }





def write_summary_files(

    project_name: str,

    project_slug: str,

    target: dict[str, Any],

    verified_papers: list[VerifiedPaper],

    skipped_existing: list[str],

    degraded_mode: bool,

) -> dict[str, str]:

    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")

    base_name = f"{stamp}-{project_slug}"

    json_path = OUTPUTS_DIR / f"{base_name}.json"

    md_path = OUTPUTS_DIR / f"{base_name}.md"



    payload = {

        "project_name": project_name,

        "project_slug": project_slug,

        "target": target,

        "degraded_mode": degraded_mode,

        "verified_papers": [

            {

                "doi": paper.doi,

                "title": paper.title,

                "journal": paper.journal,

                "year": paper.year,

                "item_key": paper.zotero_item_key,

                "item_id": paper.zotero_item_id,

                "source_url": paper.source_url,

            }

            for paper in verified_papers

        ],

        "skipped_existing_dois": skipped_existing,

        "generated_at": datetime.now().isoformat(timespec="seconds"),

    }

    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")



    lines = [

        "# Writing Reference Capture Local",

        "",

        f"- 项目：{project_name}",

        f"- 项目 slug：`{project_slug}`",

        f"- Zotero 目标：`{target['id']}` | {target['name']}",

        f"- 运行模式：{'降级到根库' if degraded_mode else '直接写入既有目标'}",

        "",

        "## 已核验并处理的论文",

        "",

    ]

    for paper in verified_papers:

        lines.extend(

            [

                f"- {paper.title}",

                f"  DOI: {paper.doi}",

                f"  期刊: {paper.journal}",

                f"  年份: {paper.year}",

                f"  Zotero: {paper.zotero_item_key or '未写回 key'}",

            ]

        )

    if skipped_existing:

        lines.extend(["", "## 已存在而跳过重复写入的 DOI", ""])

        for doi in skipped_existing:

            lines.append(f"- {doi}")



    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    return {"json": str(json_path), "markdown": str(md_path)}





def parse_args() -> argparse.Namespace:

    parser = argparse.ArgumentParser()

    parser.add_argument("--project-name", required=True)

    parser.add_argument("--doi", action="append", default=[])

    parser.add_argument("--target-id")

    parser.add_argument("--prefer-current-target", action="store_true")

    parser.add_argument("--allow-library-root-fallback", action="store_true")

    parser.add_argument("--zotero-db", default=str(DEFAULT_ZOTERO_DB))

    return parser.parse_args()





def main() -> None:

    args = parse_args()

    settings = load_settings()

    project_name = args.project_name.strip()

    project_slug = resolve_project_slug(project_name)

    dois = [normalize_doi(value) for value in args.doi if value.strip()]

    if not dois:

        raise CaptureError("至少需要提供一个 DOI。")



    connector_state = get_selected_collection()

    target = select_zotero_target(

        targets=connector_state["targets"],

        project_name=project_name,

        requested_target_id=args.target_id,

        current_target_id=connector_state.get("id"),

        allow_library_root_fallback=args.allow_library_root_fallback,

        prefer_current_target=args.prefer_current_target,

    )

    degraded_mode = str(target["id"]).startswith("L")



    sqlite_path = Path(args.zotero_db)

    existing = find_existing_items_by_doi(dois, sqlite_path)



    verified_papers: list[VerifiedPaper] = []

    items_to_write: list[dict[str, Any]] = []

    skipped_existing: list[str] = []



    for doi in dois:

        paper = verify_paper(doi)

        match = existing.get(paper.doi)

        if match:

            paper.zotero_item_id = match["item_id"]

            paper.zotero_item_key = match["item_key"]

            skipped_existing.append(paper.doi)

        else:

            items_to_write.append(_paper_to_zotero_item(paper))

        verified_papers.append(paper)



    if items_to_write:

        session_id = str(uuid.uuid4())

        save_items(session_id, items_to_write)

        update_session(

            session_id,

            target_id=str(target["id"]),

            tags=[

                "source/codex-writing",

                f"project/{project_slug}",

                "status/captured",

            ],

        )



    enrich_with_zotero_keys(verified_papers, sqlite_path)

    obsidian_paths = write_obsidian_outputs(

        settings=settings,

        project_name=project_name,

        project_slug=project_slug,

        target=target,

        papers=verified_papers,

        degraded_mode=degraded_mode,

    )

    summary_paths = write_summary_files(

        project_name=project_name,

        project_slug=project_slug,

        target=target,

        verified_papers=verified_papers,

        skipped_existing=skipped_existing,

        degraded_mode=degraded_mode,

    )



    result = {

        "project_name": project_name,

        "project_slug": project_slug,

        "target": target,

        "degraded_mode": degraded_mode,

        "obsidian": obsidian_paths,

        "summaries": summary_paths,

        "verified_papers": [

            {

                "doi": paper.doi,

                "title": paper.title,

                "year": paper.year,

                "journal": paper.journal,

                "item_key": paper.zotero_item_key,

                "item_id": paper.zotero_item_id,

                "source_url": paper.source_url,

            }

            for paper in verified_papers

        ],

        "skipped_existing_dois": skipped_existing,

    }

    print(json.dumps(result, ensure_ascii=False, indent=2))





if __name__ == "__main__":

    main()
