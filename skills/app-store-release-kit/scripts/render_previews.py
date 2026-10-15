#!/usr/bin/env python3
"""Render App Store and Google Play artwork from real UI captures."""

from __future__ import annotations

import argparse
import json
import math
import tempfile
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps
except ImportError as error:  # pragma: no cover - environment-specific
    raise SystemExit("Pillow is required: python3 -m pip install Pillow") from error


DEFAULT_FONTS = (
    Path("/System/Library/Fonts/PingFang.ttc"),
    Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf"),
    Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
)
VALID_STORES = {"app_store", "google_play"}
VALID_KINDS = {"screenshot", "feature_graphic"}


def resolve_path(base: Path, value: str | None) -> Path | None:
    if not value:
        return None
    path = Path(value).expanduser()
    return path if path.is_absolute() else (base / path).resolve()


def parse_hex(value: str) -> tuple[int, int, int]:
    value = value.strip().lstrip("#")
    if len(value) != 6 or not all(character in "0123456789abcdefABCDEF" for character in value):
        raise ValueError(f"Expected #RRGGBB color, got {value!r}")
    return tuple(int(value[index : index + 2], 16) for index in (0, 2, 4))


def font_path(preferred: Path | None) -> Path:
    candidates = ((preferred,) if preferred else ()) + DEFAULT_FONTS
    for candidate in candidates:
        if candidate and candidate.is_file():
            return candidate
    raise FileNotFoundError("No usable font found; set font_path in preview-spec.json")


def load_font(path: Path, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(path), size=max(12, size))


def gradient(size: tuple[int, int], top: str, bottom: str) -> Image.Image:
    width, height = size
    start = parse_hex(top)
    end = parse_hex(bottom)
    image = Image.new("RGB", size, start)
    draw = ImageDraw.Draw(image)
    divisor = max(1, height - 1)
    for y in range(height):
        ratio = y / divisor
        color = tuple(round(start[channel] * (1 - ratio) + end[channel] * ratio) for channel in range(3))
        draw.line((0, y, width, y), fill=color)
    return image.convert("RGBA")


def rounded(image: Image.Image, radius: int) -> Image.Image:
    content = image.convert("RGBA")
    mask = Image.new("L", content.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, content.width - 1, content.height - 1), radius=radius, fill=255)
    content.putalpha(mask)
    return content


def paste_shadowed(canvas: Image.Image, image: Image.Image, position: tuple[int, int], radius: int, padding: int) -> None:
    framed = Image.new("RGBA", (image.width + padding * 2, image.height + padding * 2), "#FFFFFF")
    framed.alpha_composite(image.convert("RGBA"), (padding, padding))
    framed = rounded(framed, radius)
    x, y = position[0] - padding, position[1] - padding
    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    shadow_shape = rounded(Image.new("RGBA", framed.size, (0, 20, 18, 100)), radius)
    shadow.alpha_composite(shadow_shape, (x, y + max(14, padding * 2)))
    shadow = shadow.filter(ImageFilter.GaussianBlur(max(18, padding * 3)))
    canvas.alpha_composite(shadow)
    canvas.alpha_composite(framed, (x, y))


def split_long_token(draw: ImageDraw.ImageDraw, token: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    chunks: list[str] = []
    current = ""
    for character in token:
        candidate = current + character
        if current and draw.textlength(candidate, font=font) > max_width:
            chunks.append(current)
            current = character
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks


def wrap_text(draw: ImageDraw.ImageDraw, value: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    value = " ".join(value.split())
    if not value:
        return []
    tokens = value.split(" ")
    lines: list[str] = []
    current = ""
    for token in tokens:
        pieces = split_long_token(draw, token, font, max_width) if draw.textlength(token, font=font) > max_width else [token]
        for piece in pieces:
            candidate = piece if not current else f"{current} {piece}"
            if current and draw.textlength(candidate, font=font) > max_width:
                lines.append(current)
                current = piece
            else:
                current = candidate
    if current:
        lines.append(current)
    return lines


def draw_lines(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    lines: list[str],
    font: ImageFont.FreeTypeFont,
    fill: str,
    spacing: int,
    anchor: str | None = None,
) -> int:
    x, y = xy
    line_height = font.getbbox("Ag")[3] - font.getbbox("Ag")[1]
    for line in lines:
        draw.text((x, y), line, font=font, fill=fill, anchor=anchor)
        y += line_height + spacing
    return y


def merged(defaults: dict[str, object], item: dict[str, object], key: str, fallback: object) -> object:
    return item.get(key, defaults.get(key, fallback))


def render_app_store_screenshot(
    canvas: Image.Image,
    capture: Image.Image,
    draw: ImageDraw.ImageDraw,
    selected_font: Path,
    global_spec: dict[str, object],
    item: dict[str, object],
    defaults: dict[str, object],
) -> None:
    width, height = canvas.size
    portrait = height >= width
    margin_x = round(width * (0.075 if portrait else 0.065))
    content_width = width - margin_x * 2
    brand_y = round(height * 0.035)
    icon_value = item.get("icon") or global_spec.get("icon")
    icon_path = resolve_path(Path(str(item["_spec_base"])), str(icon_value)) if icon_value else None
    icon_size = round(min(width, height) * 0.055)
    brand_x = margin_x
    text_color = str(merged(defaults, item, "text_color", "#FFFFFF"))
    muted_color = str(merged(defaults, item, "muted_text_color", "#DCE9E6"))
    app_name = str(item.get("app_name") or global_spec.get("app_name") or "").strip()

    if icon_path:
        if not icon_path.is_file():
            raise FileNotFoundError(f"App icon not found: {icon_path}")
        icon = ImageOps.fit(Image.open(icon_path).convert("RGB"), (icon_size, icon_size), Image.Resampling.LANCZOS)
        canvas.alpha_composite(rounded(icon, max(10, icon_size // 5)), (brand_x, brand_y))
        brand_x += icon_size + round(icon_size * 0.3)
    if app_name:
        brand_font = load_font(selected_font, round(icon_size * 0.52))
        draw.text((brand_x, brand_y + icon_size // 2), app_name, font=brand_font, fill=text_color, anchor="lm")

    headline = str(item.get("headline") or "").strip()
    subheadline = str(item.get("subheadline") or "").strip()
    headline_font = load_font(selected_font, round(height * (0.043 if portrait else 0.052)))
    subheadline_font = load_font(selected_font, round(height * (0.017 if portrait else 0.021)))
    headline_y = round(height * 0.105)
    headline_lines = wrap_text(draw, headline, headline_font, content_width)
    if len(headline_lines) > 3:
        raise ValueError(f"Headline wraps to more than three lines: {headline!r}")
    text_bottom = draw_lines(draw, (margin_x, headline_y), headline_lines, headline_font, text_color, round(height * 0.008))
    if subheadline:
        sub_lines = wrap_text(draw, subheadline, subheadline_font, content_width)
        if len(sub_lines) > 3:
            raise ValueError(f"Subheadline wraps to more than three lines: {subheadline!r}")
        text_bottom = draw_lines(
            draw,
            (margin_x, text_bottom + round(height * 0.012)),
            sub_lines,
            subheadline_font,
            muted_color,
            round(height * 0.006),
        )

    screenshot_top = max(round(height * (0.285 if portrait else 0.30)), text_bottom + round(height * 0.035))
    max_screen_width = round(width * (0.84 if portrait else 0.72))
    max_screen_height = height - screenshot_top - round(height * 0.045)
    capture.thumbnail((max_screen_width, max_screen_height), Image.Resampling.LANCZOS)
    x = (width - capture.width) // 2
    y = screenshot_top + max(0, (max_screen_height - capture.height) // 2)
    radius = max(22, round(min(width, height) * 0.025))
    padding = max(6, round(min(width, height) * 0.006))
    paste_shadowed(canvas, capture, (x, y), radius, padding)


def render_google_play_screenshot(
    canvas: Image.Image,
    capture: Image.Image,
    draw: ImageDraw.ImageDraw,
    selected_font: Path,
    item: dict[str, object],
    defaults: dict[str, object],
) -> None:
    width, height = canvas.size
    portrait = height >= width
    margin_x = round(width * 0.07)
    text_color = str(merged(defaults, item, "text_color", "#FFFFFF"))
    headline = str(item.get("headline") or "").strip()
    subheadline = str(item.get("subheadline") or "").strip()
    headline_font = load_font(selected_font, round(height * (0.033 if portrait else 0.07)))
    headline_lines = wrap_text(draw, headline, headline_font, width - margin_x * 2)
    if len(headline_lines) > 2:
        raise ValueError(f"Google Play headline wraps to more than two lines: {headline!r}")
    text_top = round(height * 0.035)
    text_bottom = draw_lines(draw, (width // 2, text_top), headline_lines, headline_font, text_color, round(height * 0.006), "ma")
    if subheadline:
        sub_font = load_font(selected_font, round(height * (0.016 if portrait else 0.03)))
        sub_lines = wrap_text(draw, subheadline, sub_font, width - margin_x * 2)
        if len(sub_lines) > 1:
            raise ValueError("Google Play subheadline must fit on one line")
        text_bottom = draw_lines(
            draw,
            (width // 2, text_bottom + round(height * 0.008)),
            sub_lines,
            sub_font,
            str(merged(defaults, item, "muted_text_color", "#DCE9E6")),
            0,
            "ma",
        )
    text_limit = round(height * 0.20)
    if text_bottom > text_limit:
        raise ValueError("Google Play overlay text exceeds the top 20% safe region")

    capture_top = max(text_limit, text_bottom + round(height * 0.01))
    max_width = width
    max_height = height - capture_top
    capture.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
    x = (width - capture.width) // 2
    y = capture_top + max(0, (max_height - capture.height) // 2)
    canvas.alpha_composite(capture.convert("RGBA"), (x, y))


def render_feature_graphic(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    selected_font: Path,
    global_spec: dict[str, object],
    item: dict[str, object],
    defaults: dict[str, object],
) -> None:
    width, height = canvas.size
    if (width, height) != (1024, 500):
        raise ValueError("Google Play feature graphic must be exactly 1024x500")
    if item.get("source") or item.get("icon") or global_spec.get("icon"):
        raise ValueError("Feature graphic must not use a screenshot or app icon")

    accent = parse_hex(str(merged(defaults, item, "muted_text_color", "#DCE9E6")))
    decoration = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    decoration_draw = ImageDraw.Draw(decoration)
    decoration_draw.ellipse((-130, 235, 330, 695), outline=(*accent, 42), width=36)
    decoration_draw.ellipse((735, -210, 1195, 250), outline=(*accent, 34), width=30)
    canvas.alpha_composite(decoration)

    app_name = str(item.get("app_name") or global_spec.get("app_name") or "").strip()
    headline = str(item.get("headline") or "").strip()
    if not headline:
        raise ValueError("Feature graphic needs a headline")
    text_color = str(merged(defaults, item, "text_color", "#FFFFFF"))
    muted_color = str(merged(defaults, item, "muted_text_color", "#DCE9E6"))
    if app_name:
        brand_font = load_font(selected_font, 32)
        draw.text((width // 2, 145), app_name, font=brand_font, fill=muted_color, anchor="mm")
    headline_font = load_font(selected_font, 64)
    headline_lines = wrap_text(draw, headline, headline_font, 760)
    if len(headline_lines) > 2:
        raise ValueError("Feature graphic headline wraps to more than two lines")
    start_y = 215 if len(headline_lines) == 1 else 185
    draw_lines(draw, (width // 2, start_y), headline_lines, headline_font, text_color, 14, "ma")


def render_item(spec_base: Path, global_spec: dict[str, object], item: dict[str, object]) -> Path:
    defaults = dict(global_spec.get("defaults") or {})
    size_value = item.get("size")
    if not isinstance(size_value, list) or len(size_value) != 2:
        raise ValueError("Each preview item needs size: [width, height]")
    width, height = (int(size_value[0]), int(size_value[1]))
    if min(width, height) < 320:
        raise ValueError(f"Preview size is implausibly small: {width}x{height}")

    store = str(item.get("store") or global_spec.get("store") or "app_store")
    kind = str(item.get("kind") or "screenshot")
    if store not in VALID_STORES:
        raise ValueError(f"Unsupported store: {store}")
    if kind not in VALID_KINDS:
        raise ValueError(f"Unsupported preview kind: {kind}")
    if kind == "feature_graphic" and store != "google_play":
        raise ValueError("feature_graphic is supported only for google_play")

    output_path = resolve_path(spec_base, str(item.get("output") or ""))
    if output_path is None:
        raise ValueError("Each preview item needs an output path")
    source_path = resolve_path(spec_base, str(item.get("source") or ""))
    capture: Image.Image | None = None
    if kind == "screenshot":
        if source_path is None or not source_path.is_file():
            raise FileNotFoundError(f"Real source capture not found: {source_path}")
        if source_path == output_path:
            raise ValueError("Source and output paths must differ")
        capture = ImageOps.exif_transpose(Image.open(source_path)).convert("RGB")

    headline = str(item.get("headline") or "").strip()
    if not headline:
        raise ValueError(f"Missing headline for {output_path}")
    font_value = merged(defaults, item, "font_path", global_spec.get("font_path") or "")
    preferred_font = resolve_path(spec_base, str(font_value)) if font_value else None
    selected_font = font_path(preferred_font)
    canvas = gradient(
        (width, height),
        str(merged(defaults, item, "background_top", "#0B6B63")),
        str(merged(defaults, item, "background_bottom", "#17312E")),
    )
    draw = ImageDraw.Draw(canvas)
    render_item_data = dict(item)
    render_item_data["_spec_base"] = str(spec_base)
    if kind == "feature_graphic":
        render_feature_graphic(canvas, draw, selected_font, global_spec, render_item_data, defaults)
    elif store == "google_play":
        assert capture is not None
        render_google_play_screenshot(canvas, capture, draw, selected_font, render_item_data, defaults)
    else:
        assert capture is not None
        render_app_store_screenshot(canvas, capture, draw, selected_font, global_spec, render_item_data, defaults)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(output_path, optimize=True, quality=95)
    return output_path


def contact_sheets(paths: list[Path], qa_dir: Path) -> list[Path]:
    groups: dict[tuple[int, int], list[Path]] = {}
    for path in paths:
        with Image.open(path) as image:
            groups.setdefault(image.size, []).append(path)
    outputs: list[Path] = []
    qa_dir.mkdir(parents=True, exist_ok=True)
    for size, group in sorted(groups.items()):
        columns = min(4, len(group))
        rows = math.ceil(len(group) / columns)
        thumb_height = 560 if size[1] >= size[0] else 320
        thumb_width = round(thumb_height * size[0] / size[1])
        gap = 24
        label_height = 42
        sheet = Image.new(
            "RGB",
            (columns * thumb_width + (columns + 1) * gap, rows * (thumb_height + label_height) + (rows + 1) * gap),
            "#E8EFED",
        )
        draw = ImageDraw.Draw(sheet)
        label_font = load_font(font_path(None), 20)
        for index, path in enumerate(group):
            column, row = index % columns, index // columns
            x = gap + column * (thumb_width + gap)
            y = gap + row * (thumb_height + label_height + gap)
            image = Image.open(path).convert("RGB").resize((thumb_width, thumb_height), Image.Resampling.LANCZOS)
            sheet.paste(image, (x, y))
            draw.text((x + thumb_width // 2, y + thumb_height + 12), path.name, font=label_font, fill="#17312E", anchor="ma")
        destination = qa_dir / f"contact-sheet-{size[0]}x{size[1]}.jpg"
        sheet.save(destination, quality=90, optimize=True)
        outputs.append(destination)
    return outputs


def render_spec(path: Path) -> list[Path]:
    payload = json.loads(path.read_text())
    if payload.get("schema_version") not in {1, 2}:
        raise ValueError("preview-spec.json must use schema_version 1 or 2")
    if payload.get("schema_version") == 1 and "store" not in payload:
        payload["store"] = "app_store"
    items = payload.get("items")
    if not isinstance(items, list) or not items:
        raise ValueError("preview-spec.json needs at least one item")
    outputs = [render_item(path.parent, payload, item) for item in items]
    qa_dir = resolve_path(path.parent, str(payload.get("qa_dir", "qa")))
    if qa_dir:
        outputs.extend(contact_sheets(outputs, qa_dir))
    return outputs


def self_test() -> None:
    with tempfile.TemporaryDirectory(prefix="release-kit-render-") as temporary:
        root = Path(temporary)
        source = Image.new("RGB", (600, 1200), "#F4F7F6")
        source_draw = ImageDraw.Draw(source)
        source_draw.rounded_rectangle((60, 90, 540, 250), radius=24, fill="#0B6B63")
        source_draw.rectangle((60, 310, 540, 1050), fill="#FFFFFF")
        source.save(root / "source.png")
        spec = {
            "schema_version": 2,
            "app_name": "Fixture",
            "qa_dir": "qa",
            "items": [
                {
                    "store": "app_store",
                    "kind": "screenshot",
                    "source": "source.png",
                    "output": "ios.png",
                    "size": [1206, 2622],
                    "headline": "A Real Capture, Clearly Presented",
                },
                {
                    "store": "google_play",
                    "kind": "screenshot",
                    "source": "source.png",
                    "output": "play.png",
                    "size": [1080, 1920],
                    "headline": "Plan With Clarity",
                },
                {
                    "store": "google_play",
                    "kind": "feature_graphic",
                    "output": "feature.png",
                    "size": [1024, 500],
                    "headline": "Plan With Clarity",
                },
            ],
        }
        spec_path = root / "preview-spec.json"
        spec_path.write_text(json.dumps(spec))
        outputs = render_spec(spec_path)
        for name, size in (("ios.png", (1206, 2622)), ("play.png", (1080, 1920)), ("feature.png", (1024, 500))):
            with Image.open(root / name) as rendered:
                assert rendered.size == size
                assert rendered.mode == "RGB"
        assert len(outputs) == 6
    print("render_previews self-test passed")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", type=Path, help="Path to preview-spec.json")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    if not args.spec:
        parser.error("--spec is required unless --self-test is used")
    for output in render_spec(args.spec.resolve()):
        print(output)


if __name__ == "__main__":
    main()
