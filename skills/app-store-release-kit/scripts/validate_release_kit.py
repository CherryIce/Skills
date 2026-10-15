#!/usr/bin/env python3
"""Validate one app's App Store, Google Play, and bilingual web package."""

from __future__ import annotations

import argparse
import html
import re
import tempfile
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

try:
    from PIL import Image
except ImportError as error:  # pragma: no cover - environment-specific
    raise SystemExit("Pillow is required: python3 -m pip install Pillow") from error


IPHONE_REQUIRED = {(1179, 2556), (2556, 1179), (1206, 2622), (2622, 1206)}
IPAD_REQUIRED = {(2064, 2752), (2752, 2064), (2048, 2732), (2732, 2048)}
IPHONE_ACCEPTED = IPHONE_REQUIRED | {
    (1260, 2736), (2736, 1260), (1290, 2796), (2796, 1290),
    (1320, 2868), (2868, 1320), (1284, 2778), (2778, 1284),
    (1242, 2688), (2688, 1242), (1170, 2532), (2532, 1170),
    (1125, 2436), (2436, 1125), (1080, 2340), (2340, 1080),
    (1242, 2208), (2208, 1242), (750, 1334), (1334, 750),
    (640, 1096), (1096, 640), (640, 1136), (1136, 640),
    (640, 920), (920, 640), (640, 960), (960, 640),
}
IPAD_ACCEPTED = IPAD_REQUIRED | {
    (1488, 2266), (2266, 1488), (1668, 2420), (2420, 1668),
    (1668, 2388), (2388, 1668), (1640, 2360), (2360, 1640),
    (1668, 2224), (2224, 1668), (1536, 2008), (2008, 1536),
    (1536, 2048), (2048, 1536), (768, 1004), (1004, 768),
    (768, 1024), (1024, 768),
}
PLACEHOLDER_PATTERN = re.compile(r"\[\[[A-Z0-9_]+\]\]|\{\{[^}]+\}\}|\bTODO\b|example\.com", re.IGNORECASE)
EMAIL_PATTERN = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE)
CHINESE_PATTERN = re.compile(r"[\u3400-\u9fff]")
DESCRIPTION_CANDIDATES = (
    "artifacts/app-store-listing/description-en.txt",
    "docs/release/APP_STORE_DESCRIPTION_EN.txt",
    "app-store/description-en.txt",
)
KEYWORD_CANDIDATES = (
    "artifacts/app-store-listing/keywords-en.txt",
    "docs/release/APP_STORE_KEYWORDS_EN.txt",
    "app-store/keywords-en.txt",
)
PLAY_SHORT_DESCRIPTION_CANDIDATES = (
    "artifacts/google-play-listing/short-description-en.txt",
    "docs/release/GOOGLE_PLAY_SHORT_DESCRIPTION_EN.txt",
)
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg"}


@dataclass(frozen=True)
class Finding:
    level: str
    code: str
    message: str
    path: str | None = None


def add(findings: list[Finding], level: str, code: str, message: str, path: Path | None = None) -> None:
    findings.append(Finding(level, code, message, str(path) if path else None))


def first_existing(root: Path, candidates: tuple[str, ...]) -> Path | None:
    return next((root / candidate for candidate in candidates if (root / candidate).is_file()), None)


def read(path: Path) -> str:
    return path.read_text(errors="replace")


def validate_manifest(root: Path, findings: list[Finding]) -> tuple[bool | None, str | None]:
    path = root / "release-kit.yml"
    if not path.is_file():
        add(findings, "ERROR", "manifest.missing", "release-kit.yml is missing", path)
        return None, None
    text = read(path)
    schema_match = re.search(r"(?m)^schema_version:\s*(\d+)", text)
    if not schema_match or int(schema_match.group(1)) < 2:
        add(findings, "ERROR", "manifest.schema", "Manifest must use schema_version 2 for iOS, Android, and bilingual web output", path)
    for key in ("app_name", "operator", "support_email", "production_domain", "effective_date"):
        match = re.search(rf"(?m)^\s*{key}:\s*(.*)$", text)
        value = match.group(1).strip().strip("'\"") if match else ""
        if not value:
            add(findings, "ERROR", f"manifest.{key}", f"Manifest value {key} is missing", path)

    ipad_match = re.search(r"(?m)^\s*ipad:\s*([^#\n]+)", text)
    ipad_value = ipad_match.group(1).strip().strip("'\"").lower() if ipad_match else None
    ipad = True if ipad_value == "true" else False if ipad_value == "false" else None
    if ipad is None:
        add(findings, "WARN", "manifest.ipad_auto", "Resolve platforms.ios.ipad from the Xcode target before completion", path)
    android_block = re.search(r"(?ms)^\s{2}android:\s*\n(?P<body>(?:\s{4}[^\n]+\n?)*)", text)
    phone_match = re.search(r"(?m)^\s*phone:\s*true\s*$", android_block.group("body")) if android_block else None
    if not phone_match:
        add(findings, "ERROR", "manifest.android_phone", "platforms.android.phone must be true", path)
    for locale in ("en", "zh-Hans"):
        if not re.search(rf"(?m)^\s*-\s*{re.escape(locale)}\s*$", text):
            add(findings, "ERROR", "manifest.website_locale", f"website.locales must include {locale}", path)
    app_match = re.search(r"(?m)^\s*app_name:\s*([^#\n]+)", text)
    app_name = app_match.group(1).strip().strip("'\"") if app_match else None
    return ipad, app_name


def validate_description(root: Path, findings: list[Finding], explicit: Path | None) -> None:
    path = explicit or first_existing(root, DESCRIPTION_CANDIDATES)
    if not path or not path.is_file():
        add(findings, "ERROR", "description.missing", "Shared English full description is missing", path)
        return
    value = read(path).rstrip("\n")
    count = len(value)
    if not value.strip():
        add(findings, "ERROR", "description.empty", "Shared English full description is empty", path)
    if count > 4000:
        add(findings, "ERROR", "description.limit", f"Description is {count} characters; maximum is 4000", path)
    else:
        add(findings, "PASS", "description.limit", f"Shared description is {count}/4000 characters", path)
    if "<" in value and re.search(r"<\/?[A-Za-z][^>]*>", value):
        add(findings, "ERROR", "description.html", "Description must be plain text, not HTML", path)


def validate_keywords(root: Path, findings: list[Finding], explicit: Path | None, app_name: str | None) -> None:
    path = explicit or first_existing(root, KEYWORD_CANDIDATES)
    if not path or not path.is_file():
        add(findings, "ERROR", "keywords.missing", "Apple English keywords file is missing", path)
        return
    value = read(path).strip()
    byte_count = len(value.encode("utf-8"))
    if not value:
        add(findings, "ERROR", "keywords.empty", "Apple English keywords are empty", path)
        return
    if byte_count > 100:
        add(findings, "ERROR", "keywords.limit", f"Keywords use {byte_count} UTF-8 bytes; maximum is 100", path)
    else:
        add(findings, "PASS", "keywords.limit", f"Apple keywords use {byte_count}/100 UTF-8 bytes", path)
    keywords = [item.strip() for item in value.replace("\n", ",").split(",") if item.strip()]
    normalized = [item.casefold() for item in keywords]
    duplicates = sorted(item for item, count in Counter(normalized).items() if count > 1)
    if duplicates:
        add(findings, "ERROR", "keywords.duplicates", f"Duplicate keywords: {', '.join(duplicates)}", path)
    too_short = [item for item in keywords if len(item) <= 2]
    if too_short:
        add(findings, "ERROR", "keywords.too_short", f"Keywords must be longer than two characters: {', '.join(too_short)}", path)
    if app_name:
        app_tokens = {token.casefold() for token in re.findall(r"[A-Za-z0-9]+", app_name) if len(token) > 2}
        repeated = sorted(set(normalized) & app_tokens)
        if repeated:
            add(findings, "WARN", "keywords.app_name", f"Keywords repeat app-name terms: {', '.join(repeated)}", path)


def validate_play_short_description(root: Path, findings: list[Finding], explicit: Path | None) -> None:
    path = explicit or first_existing(root, PLAY_SHORT_DESCRIPTION_CANDIDATES)
    if not path or not path.is_file():
        add(findings, "ERROR", "play_short_description.missing", "Google Play English short description is missing", path)
        return
    value = read(path).strip()
    if not value:
        add(findings, "ERROR", "play_short_description.empty", "Google Play short description is empty", path)
        return
    if "\n" in value or "\r" in value:
        add(findings, "ERROR", "play_short_description.lines", "Google Play short description must be one line", path)
    count = len(value)
    if count > 80:
        add(findings, "ERROR", "play_short_description.limit", f"Short description is {count} characters; maximum is 80", path)
    else:
        add(findings, "PASS", "play_short_description.limit", f"Google Play short description is {count}/80 characters", path)


def strip_markup(value: str) -> str:
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", value)).split())


def localized_text(document: str, locale: str) -> str:
    pattern = re.compile(
        rf"(?is)<(?P<tag>[a-z][a-z0-9]*)\b[^>]*\bdata-lang\s*=\s*['\"]{re.escape(locale)}['\"][^>]*>(?P<body>.*?)</(?P=tag)>",
    )
    return " ".join(strip_markup(match.group("body")) for match in pattern.finditer(document))


def validate_html(root: Path, findings: list[Finding], website: Path | None) -> None:
    website_root = website or root / "website"
    index = website_root / "index.html"
    privacy = website_root / "privacy.html"
    styles = website_root / "styles.css"
    script = website_root / "site.js"
    for path in (index, privacy, styles, script):
        if not path.is_file():
            add(findings, "ERROR", "website.missing", f"Website file is missing: {path.name}", path)
    if not index.is_file() or not privacy.is_file():
        return

    index_text = read(index)
    privacy_text = read(privacy)
    for path, document, minimum in ((index, index_text, 80), (privacy, privacy_text, 220)):
        marker = PLACEHOLDER_PATTERN.search(document)
        if marker:
            add(findings, "ERROR", "website.placeholder", f"Unresolved template marker: {marker.group(0)}", path)
        checks = (
            (re.compile(r"<title\b", re.IGNORECASE), "title"),
            (re.compile(r"<meta\b[^>]*\bname\s*=\s*['\"]viewport['\"]", re.IGNORECASE), "viewport meta"),
            (re.compile(r"<html\b[^>]*\blang\s*=", re.IGNORECASE), "html root with language"),
            (re.compile(r"<script\b[^>]*\bsrc\s*=\s*['\"]site\.js['\"][^>]*\bdefer\b", re.IGNORECASE), "deferred site.js"),
            (re.compile(r"data-title-en\s*=", re.IGNORECASE), "English page title data"),
            (re.compile(r"data-title-zh\s*=", re.IGNORECASE), "Chinese page title data"),
            (re.compile(r"data-description-en\s*=", re.IGNORECASE), "English page description data"),
            (re.compile(r"data-description-zh\s*=", re.IGNORECASE), "Chinese page description data"),
        )
        for pattern, label in checks:
            if not pattern.search(document):
                add(findings, "ERROR", "website.structure", f"Missing {label}", path)
        for locale in ("en", "zh"):
            content = localized_text(document, locale)
            if len(content) < minimum:
                add(findings, "ERROR", "website.locale_content", f"{locale} content is incomplete ({len(content)} characters)", path)
            elif locale == "zh" and not CHINESE_PATTERN.search(content):
                add(findings, "ERROR", "website.locale_chinese", "Chinese content contains no Chinese characters", path)
            else:
                add(findings, "PASS", "website.locale_content", f"{path.name} contains complete {locale} content", path)
        for locale in ("en", "zh"):
            if not re.search(rf"data-language-option\s*=\s*['\"]{locale}['\"]", document, re.IGNORECASE):
                add(findings, "ERROR", "website.language_switch", f"Missing {locale} language control", path)

    if script.is_file():
        script_text = read(script)
        for token in ("URLSearchParams", "localStorage", "document.documentElement.lang", "data-language-option"):
            if token not in script_text:
                add(findings, "ERROR", "website.language_script", f"site.js is missing language behavior: {token}", script)
    if "privacy.html" not in index_text:
        add(findings, "ERROR", "website.privacy_link", "Product website does not link to privacy.html", index)
    index_emails = set(EMAIL_PATTERN.findall(index_text))
    privacy_emails = set(EMAIL_PATTERN.findall(privacy_text))
    if not index_emails:
        add(findings, "ERROR", "website.contact", "Product website has no support email", index)
    if not privacy_emails:
        add(findings, "ERROR", "privacy.contact", "Privacy policy has no contact email", privacy)
    if index_emails and privacy_emails and not (index_emails & privacy_emails):
        add(findings, "WARN", "website.contact_mismatch", "Website and privacy policy use different contact emails")
    if "privacy" not in privacy_text.casefold() or "隐私" not in privacy_text:
        add(findings, "ERROR", "privacy.heading", "Privacy policy must identify itself in English and Chinese", privacy)


def image_files(base: Path, ignored_parts: set[str] | None = None) -> list[Path]:
    ignored = {part.casefold() for part in (ignored_parts or set())}
    if not base.is_dir():
        return []
    return sorted(
        path
        for path in base.rglob("*")
        if path.is_file()
        and path.suffix.lower() in IMAGE_SUFFIXES
        and not ({part.casefold() for part in path.relative_to(base).parts[:-1]} & ignored)
    )


def app_store_preview_files(root: Path) -> list[Path]:
    bases = (root / "artifacts/app-store-previews/final", root / "docs/release/app_store_previews")
    found: set[Path] = set()
    for base in bases:
        found.update(image_files(base, {"background", "backgrounds", "qa", "source", "sources", "evidence"}))
    return sorted(found)


def has_alpha(image: Image.Image) -> bool:
    return image.mode in {"RGBA", "LA"} or (image.mode == "P" and "transparency" in image.info)


def infer_ipad_support(root: Path) -> bool | None:
    project_files = [path for path in (root / "ios").rglob("project.pbxproj") if "Pods" not in path.parts] if (root / "ios").is_dir() else []
    if not project_files:
        return None
    values: list[str] = []
    for path in project_files:
        values.extend(re.findall(r"TARGETED_DEVICE_FAMILY\s*=\s*([^;]+);", read(path)))
    normalized = {value.replace('"', "").replace(" ", "") for value in values}
    if any("2" in value.split(",") for value in normalized):
        return True
    if normalized and all(value == "1" for value in normalized):
        return False
    return None


def validate_app_store_previews(root: Path, findings: list[Finding], manifest_ipad: bool | None) -> None:
    paths = app_store_preview_files(root)
    if not paths:
        add(findings, "ERROR", "app_store_screenshots.missing", "No final App Store screenshots were found")
        return
    sizes: list[tuple[int, int]] = []
    iphone_count = 0
    ipad_count = 0
    for path in paths:
        try:
            with Image.open(path) as image:
                size = image.size
                sizes.append(size)
                if has_alpha(image):
                    add(findings, "ERROR", "app_store_screenshots.alpha", f"Image has alpha/transparency; mode={image.mode}", path)
                if size in IPHONE_ACCEPTED:
                    iphone_count += 1
                elif size in IPAD_ACCEPTED:
                    ipad_count += 1
                else:
                    add(findings, "ERROR", "app_store_screenshots.dimensions", f"Unrecognized App Store screenshot size: {size[0]}x{size[1]}", path)
        except Exception as error:
            add(findings, "ERROR", "app_store_screenshots.read", f"Cannot read image: {error}", path)
    if iphone_count == 0:
        add(findings, "ERROR", "app_store_screenshots.iphone", "No accepted iPhone screenshot was found")
    elif not any(size in IPHONE_REQUIRED for size in sizes):
        add(findings, "ERROR", "app_store_screenshots.iphone_required", "Missing current iPhone Dynamic Island medium-display screenshot")
    else:
        add(findings, "PASS", "app_store_screenshots.iphone_required", f"Found {iphone_count} accepted iPhone screenshot(s)")
    supports_ipad = manifest_ipad if manifest_ipad is not None else infer_ipad_support(root)
    if supports_ipad is True:
        if not any(size in IPAD_REQUIRED for size in sizes):
            add(findings, "ERROR", "app_store_screenshots.ipad_required", "App supports iPad but has no current 13-inch iPad screenshot")
        else:
            add(findings, "PASS", "app_store_screenshots.ipad_required", f"Found {ipad_count} accepted iPad screenshot(s)")
    elif supports_ipad is None:
        add(findings, "WARN", "app_store_screenshots.ipad_unknown", "Could not determine whether the app supports iPad")
    for size, count in sorted(Counter(sizes).items()):
        if count > 10:
            add(findings, "ERROR", "app_store_screenshots.count", f"{count} screenshots use {size[0]}x{size[1]}; maximum per size is 10")
        else:
            add(findings, "PASS", "app_store_screenshots.group", f"{count} App Store screenshot(s) at {size[0]}x{size[1]}")


def play_group(path: Path, final_root: Path) -> str:
    relative = path.relative_to(final_root)
    return str(relative.parent) if str(relative.parent) != "." else "default"


def recommended_play_shape(size: tuple[int, int]) -> bool:
    width, height = size
    return min(size) >= 1080 and (width * 16 == height * 9 or width * 9 == height * 16)


def validate_google_play_assets(root: Path, findings: list[Finding]) -> None:
    final_root = root / "artifacts/google-play-listing/final"
    paths = image_files(final_root)
    feature_paths = [path for path in paths if "feature-graphic" in path.stem.casefold()]
    screenshot_paths = [path for path in paths if path not in feature_paths]
    if not feature_paths:
        add(findings, "ERROR", "play_feature.missing", "No Google Play feature graphic was found", final_root)
    for path in feature_paths:
        try:
            with Image.open(path) as image:
                if image.size != (1024, 500):
                    add(findings, "ERROR", "play_feature.dimensions", f"Feature graphic is {image.width}x{image.height}; required 1024x500", path)
                elif has_alpha(image) or image.mode != "RGB":
                    add(findings, "ERROR", "play_feature.mode", f"Feature graphic must be 24-bit RGB without alpha; mode={image.mode}", path)
                else:
                    add(findings, "PASS", "play_feature.valid", "Feature graphic is 1024x500 RGB", path)
        except Exception as error:
            add(findings, "ERROR", "play_feature.read", f"Cannot read feature graphic: {error}", path)

    if len(screenshot_paths) < 2:
        add(findings, "ERROR", "play_screenshots.count", f"Google Play requires at least 2 screenshots; found {len(screenshot_paths)}", final_root)
    groups: dict[str, list[tuple[Path, tuple[int, int]]]] = {}
    for path in screenshot_paths:
        try:
            with Image.open(path) as image:
                size = image.size
                groups.setdefault(play_group(path, final_root), []).append((path, size))
                if has_alpha(image) or image.mode != "RGB":
                    add(findings, "ERROR", "play_screenshots.mode", f"Screenshot must be 24-bit RGB without alpha; mode={image.mode}", path)
                shortest, longest = min(size), max(size)
                if shortest < 320 or longest > 3840 or longest > shortest * 2:
                    add(findings, "ERROR", "play_screenshots.dimensions", f"Invalid Google Play screenshot dimensions: {size[0]}x{size[1]}", path)
        except Exception as error:
            add(findings, "ERROR", "play_screenshots.read", f"Cannot read screenshot: {error}", path)
    for group, records in sorted(groups.items()):
        count = len(records)
        if count > 8:
            add(findings, "ERROR", "play_screenshots.group_count", f"{group} has {count} screenshots; maximum per device type is 8")
        elif count < 2:
            add(findings, "WARN", "play_screenshots.group_count", f"{group} has only {count} screenshot")
        else:
            add(findings, "PASS", "play_screenshots.group_count", f"{group} has {count}/8 screenshots")
        if count >= 4 and all(recommended_play_shape(size) for _, size in records):
            add(findings, "PASS", "play_screenshots.recommended", f"{group} meets the four high-resolution 9:16 or 16:9 recommendation")
        else:
            add(findings, "WARN", "play_screenshots.recommended", f"{group} does not yet meet the recommended four 1080px 9:16 or 16:9 screenshots")


def validate(
    root: Path,
    description: Path | None = None,
    keywords: Path | None = None,
    play_short_description: Path | None = None,
    website: Path | None = None,
) -> list[Finding]:
    findings: list[Finding] = []
    manifest_ipad, app_name = validate_manifest(root, findings)
    validate_description(root, findings, description)
    validate_keywords(root, findings, keywords, app_name)
    validate_play_short_description(root, findings, play_short_description)
    validate_html(root, findings, website)
    validate_app_store_previews(root, findings, manifest_ipad)
    validate_google_play_assets(root, findings)
    return findings


def report(findings: list[Finding], root: Path) -> str:
    errors = sum(finding.level == "ERROR" for finding in findings)
    warnings = sum(finding.level == "WARN" for finding in findings)
    passes = sum(finding.level == "PASS" for finding in findings)
    lines = [
        "# Store Release Kit QA",
        "",
        f"Target: `{root}`",
        "",
        f"Result: {'FAIL' if errors else 'PASS'} — {errors} error(s), {warnings} warning(s), {passes} passed check(s)",
        "",
        "## Findings",
        "",
    ]
    for finding in findings:
        location = f" — `{finding.path}`" if finding.path else ""
        lines.append(f"- **{finding.level}** `{finding.code}`: {finding.message}{location}")
    lines.extend(
        [
            "",
            "Passing this report does not prove runtime capture platform or authenticity, visual quality, public hosting, legal review, App Store Connect or Play Console upload, processing, TestFlight or Play testing availability, submission, review, or device behavior.",
            "",
        ]
    )
    return "\n".join(lines)


def self_test() -> None:
    with tempfile.TemporaryDirectory(prefix="release-kit-validate-") as temporary:
        root = Path(temporary)
        (root / "artifacts/app-store-listing").mkdir(parents=True)
        (root / "artifacts/app-store-listing/description-en.txt").write_text("A focused planner for projects, notes, and daily progress.")
        (root / "artifacts/app-store-listing/keywords-en.txt").write_text("planning,projects,offline,organizer,progress")
        (root / "artifacts/google-play-listing").mkdir(parents=True)
        (root / "artifacts/google-play-listing/short-description-en.txt").write_text("Plan projects, notes, and daily progress with clarity.")
        (root / "release-kit.yml").write_text(
            "schema_version: 2\nidentity:\n  app_name: Fixture\n  operator: Fixture Studio\n"
            "contact:\n  support_email: support@fixture.test\n  production_domain: https://fixture.test\n"
            "platforms:\n  ios:\n    iphone: true\n    ipad: true\n  android:\n    phone: true\n"
            "privacy:\n  effective_date: 2026-10-09\nwebsite:\n  locales:\n    - en\n    - zh-Hans\n"
        )
        website = root / "website"
        website.mkdir()
        (website / "styles.css").write_text('[data-lang][hidden] { display: none; }')
        (website / "site.js").write_text(
            'const q = new URLSearchParams(location.search); localStorage.getItem("lang"); '
            'document.documentElement.lang = "en"; document.querySelector("[data-language-option]");'
        )
        common = (
            '<html lang="en"><head><meta name="viewport" content="width=device-width">'
            '<title>Fixture</title><script src="site.js" defer></script></head>'
            '<body data-title-en="Fixture" data-title-zh="示例" data-description-en="Fixture app" data-description-zh="示例应用">'
            '<button data-language-option="en">EN</button><button data-language-option="zh">中文</button>'
        )
        english_product = "A focused workspace for planning projects, keeping useful notes, and reviewing meaningful daily progress without losing context."
        chinese_product = (
            "一个专注的工作空间，用于规划项目、保存实用笔记并回顾每天的重要进展，让相关内容始终清晰且易于查找。"
            "所有展示的功能都来自实际应用，并以简洁可靠的方式帮助用户完成日常工作、整理信息和查看下一步安排。"
        )
        (website / "index.html").write_text(
            common + f'<main><section data-lang="en">{english_product}</section><section data-lang="zh">{chinese_product}</section></main>'
            '<a href="privacy.html">Privacy</a><a href="mailto:support@fixture.test">Support</a></body></html>'
        )
        english_privacy = "Privacy Policy. We explain information and data, device permissions, network services, storage, retention and deletion, exports and sharing, children, policy changes, and contact details. " * 2
        chinese_privacy = "隐私政策。我们说明信息与数据、设备权限、网络服务、存储、保留与删除、导出与共享、儿童隐私、政策变更和联系信息。" * 4
        (website / "privacy.html").write_text(
            common + f'<main><article data-lang="en">{english_privacy}</article><article data-lang="zh">{chinese_privacy}</article></main>'
            '<a href="mailto:support@fixture.test">Contact</a></body></html>'
        )
        app_store_final = root / "artifacts/app-store-previews/final"
        app_store_final.mkdir(parents=True)
        Image.new("RGB", (1206, 2622), "#0B6B63").save(app_store_final / "iphone.png")
        Image.new("RGB", (2752, 2064), "#17312E").save(app_store_final / "ipad.png")
        play_final = root / "artifacts/google-play-listing/final/en-US/phone"
        play_final.mkdir(parents=True)
        for index in range(4):
            Image.new("RGB", (1080, 1920), "#0B6B63").save(play_final / f"{index + 1:02d}.png")
        Image.new("RGB", (1024, 500), "#17312E").save(root / "artifacts/google-play-listing/final/feature-graphic-en.png")
        findings = validate(root)
        errors = [finding for finding in findings if finding.level == "ERROR"]
        if errors:
            raise AssertionError("\n".join(f"{finding.code}: {finding.message}" for finding in errors))
    print("validate_release_kit self-test passed")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("app_root", type=Path, nargs="?")
    parser.add_argument("--description", type=Path)
    parser.add_argument("--keywords", type=Path)
    parser.add_argument("--play-short-description", type=Path)
    parser.add_argument("--website", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    if not args.app_root:
        parser.error("app_root is required unless --self-test is used")
    root = args.app_root.resolve()
    findings = validate(root, args.description, args.keywords, args.play_short_description, args.website)
    rendered = report(findings, root)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(rendered)
        print(args.report)
    else:
        print(rendered, end="")
    raise SystemExit(1 if any(finding.level == "ERROR" for finding in findings) else 0)


if __name__ == "__main__":
    main()
