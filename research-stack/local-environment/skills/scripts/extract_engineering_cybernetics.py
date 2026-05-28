from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pypdfium2 as pdfium
import pytesseract
from pypdf import PdfReader

try:
    from .path_utils import OUTPUTS_ROOT
except ImportError:  # pragma: no cover
    from path_utils import OUTPUTS_ROOT


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


ENGLISH_PDF = Path(
    r"<USER_DOWNLOADS>\Engineering cybernetics (Hsue Shen Tsien) (z-library.sk, 1lib.sk, z-lib.sk).pdf"
)
ZH_VOL1_PDF = Path(
    r"<USER_DOWNLOADS>\工程控制论 (上册) (第三版) (钱学森, 宋健) (z-library.sk, 1lib.sk, z-lib.sk).pdf"
)
ZH_VOL2_PDF = Path(
    r"<USER_DOWNLOADS>\工程控制论 (下册) (第三版) (钱学森, 宋健) (z-library.sk, 1lib.sk, z-lib.sk).pdf"
)
DEFAULT_OUTPUT_DIR = OUTPUTS_ROOT / "reading" / "engineering-cybernetics"
DEFAULT_TESSERACT = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _count_outline_items(items: list[Any]) -> int:
    total = 0
    for item in items:
        if isinstance(item, list):
            total += _count_outline_items(item)
        else:
            total += 1
    return total


def _outline_items(reader: PdfReader) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    def walk(items: list[Any], depth: int) -> None:
        for item in items:
            if isinstance(item, list):
                walk(item, depth + 1)
                continue
            title = getattr(item, "title", str(item))
            try:
                page = reader.get_destination_page_number(item) + 1
            except Exception:
                page = None
            rows.append({"title": title, "page": page, "depth": depth})

    try:
        walk(reader.outline, 0)
    except Exception:
        return []
    return rows


def extract_text_layer(pdf_path: Path, output_path: Path, outline_path: Path) -> dict[str, Any]:
    reader = PdfReader(str(pdf_path))
    pages: list[str] = []
    char_counts: list[int] = []
    for index, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        char_counts.append(len(text.strip()))
        pages.append(f"\n\n===== PAGE {index} =====\n{text.strip()}\n")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("".join(pages), encoding="utf-8")
    outlines = _outline_items(reader)
    outline_path.write_text(json.dumps(outlines, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "pdf": str(pdf_path),
        "output": str(output_path),
        "outline": str(outline_path),
        "pages": len(reader.pages),
        "outline_items": len(outlines),
        "total_chars": sum(char_counts),
        "nonempty_pages": sum(1 for count in char_counts if count > 0),
        "min_page_chars": min(char_counts) if char_counts else 0,
        "max_page_chars": max(char_counts) if char_counts else 0,
    }


def ocr_english(
    pdf_path: Path,
    output_dir: Path,
    *,
    tesseract_cmd: Path = DEFAULT_TESSERACT,
    scale: float = 2.0,
    force: bool = False,
    limit: int | None = None,
) -> dict[str, Any]:
    if not tesseract_cmd.exists():
        raise FileNotFoundError(f"missing tesseract executable: {tesseract_cmd}")
    pytesseract.pytesseract.tesseract_cmd = str(tesseract_cmd)

    pages_dir = output_dir / "english-ocr-pages"
    pages_dir.mkdir(parents=True, exist_ok=True)
    combined_path = output_dir / "engineering-cybernetics-en.ocr.txt"
    metadata_path = output_dir / "engineering-cybernetics-en.ocr.metadata.json"

    document = pdfium.PdfDocument(str(pdf_path))
    page_total = len(document)
    selected_total = min(page_total, limit) if limit else page_total
    page_stats: list[dict[str, Any]] = []
    combined_chunks: list[str] = []

    for page_index in range(selected_total):
        page_number = page_index + 1
        page_output = pages_dir / f"page-{page_number:03d}.txt"
        if page_output.exists() and not force:
            text = page_output.read_text(encoding="utf-8", errors="replace")
        else:
            page = document[page_index]
            image = page.render(scale=scale).to_pil()
            text = pytesseract.image_to_string(image, lang="eng", config="--psm 6")
            page_output.write_text(text, encoding="utf-8")
            image.close()
        stripped = text.strip()
        page_stats.append(
            {
                "page": page_number,
                "chars": len(stripped),
                "words_estimate": len(stripped.split()),
                "output": str(page_output),
            }
        )
        combined_chunks.append(f"\n\n===== PAGE {page_number} =====\n{stripped}\n")
        if page_number % 25 == 0 or page_number == selected_total:
            print(f"ocr-progress page={page_number}/{selected_total}", flush=True)

    combined_path.write_text("".join(combined_chunks), encoding="utf-8")
    metadata = {
        "generated_at": _utc_now(),
        "pdf": str(pdf_path),
        "output": str(combined_path),
        "pages_total": page_total,
        "pages_processed": selected_total,
        "scale": scale,
        "tesseract_cmd": str(tesseract_cmd),
        "total_chars": sum(item["chars"] for item in page_stats),
        "nonempty_pages": sum(1 for item in page_stats if item["chars"] > 0),
        "page_stats": page_stats,
    }
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return metadata


def run(args: argparse.Namespace) -> int:
    output_dir = Path(args.output_dir) if args.output_dir else DEFAULT_OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    report: dict[str, Any] = {"generated_at": _utc_now(), "output_dir": str(output_dir), "items": {}}

    if args.english_ocr:
        report["items"]["english_ocr"] = ocr_english(
            ENGLISH_PDF,
            output_dir,
            tesseract_cmd=Path(args.tesseract),
            scale=args.scale,
            force=args.force,
            limit=args.limit,
        )
    if args.chinese_text:
        report["items"]["zh_vol1"] = extract_text_layer(
            ZH_VOL1_PDF,
            output_dir / "engineering-cybernetics-zh-vol1.txt",
            output_dir / "engineering-cybernetics-zh-vol1.outline.json",
        )
        report["items"]["zh_vol2"] = extract_text_layer(
            ZH_VOL2_PDF,
            output_dir / "engineering-cybernetics-zh-vol2.txt",
            output_dir / "engineering-cybernetics-zh-vol2.outline.json",
        )
    report_path = output_dir / "extraction-report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Extract local Engineering Cybernetics reading sources.")
    parser.add_argument("--english-ocr", action="store_true", help="OCR the scanned English PDF.")
    parser.add_argument("--chinese-text", action="store_true", help="Extract Chinese PDF text layers and outlines.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--tesseract", default=str(DEFAULT_TESSERACT))
    parser.add_argument("--scale", type=float, default=2.0)
    parser.add_argument("--limit", type=int, default=None, help="Process only the first N English pages.")
    parser.add_argument("--force", action="store_true", help="Re-run OCR even if page text files already exist.")
    return parser


if __name__ == "__main__":
    raise SystemExit(run(build_parser().parse_args()))
