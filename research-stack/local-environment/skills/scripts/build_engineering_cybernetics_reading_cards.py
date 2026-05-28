from __future__ import annotations

import json
import re
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

try:
    from .path_utils import OUTPUTS_ROOT
except ImportError:  # pragma: no cover
    from path_utils import OUTPUTS_ROOT


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


BASE = OUTPUTS_ROOT / "reading" / "engineering-cybernetics"
OUTPUT = BASE / "engineering-cybernetics-reading-cards.json"

SOURCES = {
    "engineering-cybernetics-en": BASE / "engineering-cybernetics-en.ocr.txt",
    "engineering-cybernetics-zh-vol1": BASE / "engineering-cybernetics-zh-vol1.txt",
    "engineering-cybernetics-zh-vol2": BASE / "engineering-cybernetics-zh-vol2.txt",
}
OUTLINES = {
    "engineering-cybernetics-zh-vol1": BASE / "engineering-cybernetics-zh-vol1.outline.json",
    "engineering-cybernetics-zh-vol2": BASE / "engineering-cybernetics-zh-vol2.outline.json",
}

CONCEPTS = {
    "feedback": ["feedback", "反馈"],
    "stability": ["stability", "stable", "stabil", "稳定", "李雅普诺夫"],
    "controllability": ["controllable", "controllability", "能控"],
    "observability": ["observable", "observability", "能观测"],
    "transfer_function": ["transfer function", "传递函数"],
    "random_disturbance": ["random", "stochastic", "随机", "扰动"],
    "filtering": ["filter", "filtering", "过滤", "滤波"],
    "optimal_control": ["optimal", "optimum", "最优", "最速"],
    "adaptive": ["adaptive", "ultrastability", "multistability", "自适应", "自镇定"],
    "redundancy_fault_tolerance": ["reliability", "redundancy", "error", "可靠", "冗余", "容错", "误差"],
    "information_large_system": ["information", "large system", "信息", "大系统"],
    "finite_automata_logic": ["finite automata", "logic", "逻辑", "自动机"],
}

ENGLISH_CHAPTER_PATTERN = re.compile(r"^CHAPTER\s+(\d+)\s*$", re.IGNORECASE | re.MULTILINE)
PAGE_PATTERN = re.compile(r"===== PAGE\s+(\d+)\s+=====")


@dataclass
class Chapter:
    source_id: str
    index: int
    title: str
    start_offset: int
    end_offset: int
    text: str


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _page_for_offset(text: str, offset: int) -> int | None:
    current = None
    for match in PAGE_PATTERN.finditer(text):
        if match.start() > offset:
            break
        current = int(match.group(1))
    return current


def _next_nonempty_lines(text: str, offset: int, limit: int = 3) -> list[str]:
    lines = text[offset:].splitlines()[1:]
    out: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("====="):
            out.append(stripped)
        if len(out) >= limit:
            break
    return out


def split_english(text: str) -> list[Chapter]:
    matches = list(ENGLISH_CHAPTER_PATTERN.finditer(text))
    chapters: list[Chapter] = []
    for pos, match in enumerate(matches):
        index = int(match.group(1))
        start = match.start()
        end = matches[pos + 1].start() if pos + 1 < len(matches) else len(text)
        title_lines = _next_nonempty_lines(text, match.end(), 2)
        title = " ".join(title_lines[:2]) if title_lines else f"Chapter {index}"
        chapters.append(Chapter("engineering-cybernetics-en", index, _normalize_space(title), start, end, text[start:end]))
    return chapters


def _page_offsets(text: str) -> dict[int, int]:
    return {int(match.group(1)): match.start() for match in PAGE_PATTERN.finditer(text)}


def split_chinese(source_id: str, text: str) -> list[Chapter]:
    outline = json.loads(OUTLINES[source_id].read_text(encoding="utf-8"))
    top_chapters = []
    for item in outline:
        title = str(item.get("title", "")).replace("\u3000", " ").strip()
        page = item.get("page")
        if item.get("depth") == 1 and title.startswith("第") and "章" in title and "." not in title and isinstance(page, int):
            top_chapters.append({"title": title, "page": page})
    offsets = _page_offsets(text)
    chapters: list[Chapter] = []
    for pos, item in enumerate(top_chapters):
        start = offsets.get(item["page"], 0)
        if pos + 1 < len(top_chapters):
            end = offsets.get(top_chapters[pos + 1]["page"], len(text))
        else:
            end = len(text)
        chapters.append(Chapter(source_id, pos + 1, _normalize_space(item["title"]), start, end, text[start:end]))
    return chapters


def _concept_counts(text: str) -> dict[str, int]:
    low = text.lower()
    result: dict[str, int] = {}
    for concept, terms in CONCEPTS.items():
        count = 0
        for term in terms:
            flags = 0 if re.search(r"[\u4e00-\u9fff]", term) else re.IGNORECASE
            count += len(re.findall(re.escape(term), text if flags == 0 else low, flags))
        if count:
            result[concept] = count
    return result


def _contexts(text: str, terms: Iterable[str], limit: int = 5, window: int = 130) -> list[str]:
    snippets: list[str] = []
    seen: set[str] = set()
    for term in terms:
        pattern = re.compile(re.escape(term), 0 if re.search(r"[\u4e00-\u9fff]", term) else re.IGNORECASE)
        for match in pattern.finditer(text):
            start = max(0, match.start() - window)
            end = min(len(text), match.end() + window)
            snippet = _normalize_space(text[start:end])
            key = snippet[:80]
            if key not in seen:
                seen.add(key)
                snippets.append(snippet)
            if len(snippets) >= limit:
                return snippets
    return snippets


def build_cards() -> dict:
    all_cards: list[dict] = []
    concept_index: dict[str, list[dict]] = {concept: [] for concept in CONCEPTS}

    for source_id, path in SOURCES.items():
        text = path.read_text(encoding="utf-8", errors="replace")
        chapters = split_english(text) if source_id.endswith("-en") else split_chinese(source_id, text)
        for chapter in chapters:
            counts = _concept_counts(chapter.text)
            card = {
                "source_id": source_id,
                "chapter_index": chapter.index,
                "title": chapter.title,
                "start_page": _page_for_offset(text, chapter.start_offset),
                "end_page": _page_for_offset(text, max(chapter.start_offset, chapter.end_offset - 1)),
                "chars": len(chapter.text),
                "concept_counts": counts,
            }
            all_cards.append(card)
            for concept, count in counts.items():
                concept_index[concept].append(
                    {
                        "source_id": source_id,
                        "chapter_index": chapter.index,
                        "title": chapter.title,
                        "count": count,
                    }
                )

    concept_contexts = {}
    combined_text = "\n".join(path.read_text(encoding="utf-8", errors="replace") for path in SOURCES.values())
    for concept, terms in CONCEPTS.items():
        concept_contexts[concept] = _contexts(combined_text, terms)

    return {
        "generated_at": _utc_now(),
        "source_files": {key: str(path) for key, path in SOURCES.items()},
        "chapter_cards": all_cards,
        "concept_index": {
            concept: sorted(rows, key=lambda item: item["count"], reverse=True)[:12]
            for concept, rows in concept_index.items()
        },
        "concept_contexts": concept_contexts,
    }


def main() -> int:
    payload = build_cards()
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(OUTPUT), "chapters": len(payload["chapter_cards"])}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
