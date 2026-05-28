from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "manager" / "assets"
ASSET_DIR.mkdir(parents=True, exist_ok=True)


def build_icon(size: int) -> Image.Image:
    image = Image.new("RGBA", (size, size), (14, 36, 65, 255))
    draw = ImageDraw.Draw(image)

    margin = int(size * 0.14)
    shield_top = margin
    shield_bottom = size - margin
    center_x = size // 2
    points = [
        (center_x, shield_top),
        (size - margin, shield_top + int(size * 0.10)),
        (size - margin, shield_top + int(size * 0.46)),
        (center_x, shield_bottom),
        (margin, shield_top + int(size * 0.46)),
        (margin, shield_top + int(size * 0.10)),
    ]
    draw.polygon(points, outline=(226, 184, 97, 255), width=max(2, size // 32))

    col_w = max(2, size // 26)
    col_h = size // 3
    col_y = size // 2 - col_h // 2
    left = center_x - col_w * 2
    right = center_x + col_w * 2

    draw.line((left, col_y, right, col_y), fill=(226, 184, 97, 255), width=col_w)
    draw.line((left, col_y + col_h, right, col_y + col_h), fill=(226, 184, 97, 255), width=col_w)

    for offset in (-col_w * 2, 0, col_w * 2):
        x = center_x + offset
        draw.line((x, col_y + col_w, x, col_y + col_h - col_w), fill=(226, 184, 97, 255), width=col_w)

    return image


def main() -> None:
    png_path = ASSET_DIR / "codex-research-console.png"
    ico_path = ASSET_DIR / "codex-research-console.ico"

    base = build_icon(512)
    base.save(png_path)

    sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    base.save(ico_path, sizes=sizes)

    print(str(png_path))
    print(str(ico_path))


if __name__ == "__main__":
    main()
