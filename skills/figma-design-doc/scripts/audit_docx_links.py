#!/usr/bin/env python3
"""Read DOCX Figma links and compare an independently verified inventory.

This utility does not fetch URLs or edit DOCX files. Python standard library only.
"""
import argparse
from collections import Counter
import json
from pathlib import Path, PurePosixPath
import re
import sys
from urllib.parse import parse_qs, unquote, urlsplit
import xml.etree.ElementTree as ET
from zipfile import BadZipFile, ZipFile

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
URL_RE = re.compile(r"https?://(?:(?!https?://)[^\s<>\"'])+", re.I)
FIELD_RE = re.compile(r'^\s*HYPERLINK\s+(?:"([^"]+)"|(\S+))', re.I)
PART_RE = re.compile(r"word/(?:document|header\d+|footer\d+|footnotes|endnotes)\.xml$")


def urls_in(text):
    return [m.group().rstrip("。；，、）)]}>") for m in URL_RE.finditer(text)]


def figma_target(url):
    """Return effective file/branch key and optional normalized node ID."""
    parsed = urlsplit(url)
    host = (parsed.hostname or "").lower()
    if host != "figma.com" and not host.endswith(".figma.com"):
        return None
    parts = [unquote(p) for p in parsed.path.split("/") if p]
    if len(parts) < 2 or parts[0] not in {"design", "file"}:
        return None
    key = parts[1]
    if len(parts) >= 4 and parts[2] == "branch":
        key = parts[3]
    node = parse_qs(parsed.query).get("node-id", [None])[0]
    return key, node.replace("-", ":") if node else None


def visible_text(node):
    def collect(n, first=False):
        if n.tag in {W + "del", W + "moveFrom", W + "instrText"}:
            return ""
        if n.tag == W + "p" and not first:
            return ""
        if n.tag == W + "t":
            return n.text or ""
        return "".join(collect(c) for c in n)
    return collect(node, True)


def extract_docx(path):
    records, issues, plain_urls = [], [], []
    with ZipFile(path) as package:
        names = package.namelist()
        for part in sorted(n for n in names if PART_RE.fullmatch(n)):
            root = ET.fromstring(package.read(part))
            rp = str(PurePosixPath(part).parent / "_rels" / (PurePosixPath(part).name + ".rels"))
            rels = {}
            if rp in names:
                rels = {n.get("Id"): n.get("Target") for n in ET.fromstring(package.read(rp))}
            context, stack = "", []

            def add(url, label, kind, heading):
                if not url:
                    return
                found = urls_in(url)
                if len(found) > 1 and any(figma_target(u) for u in found):
                    issues.append({"part": part, "issue": "concatenated hyperlink target", "url": url})
                    return
                target = figma_target(url)
                if target is None:
                    return
                record = {"part": part, "context": heading, "label": label,
                          "url": url, "file_key": target[0], "node_id": target[1], "kind": kind}
                records.append(record)
                for displayed in urls_in(label):
                    shown = figma_target(displayed)
                    if shown is not None and shown != target:
                        issues.append({"part": part, "issue": "visible URL differs from hyperlink target",
                                       "displayed": displayed, "url": url})

            for paragraph in root.iter(W + "p"):
                start = len(records)
                text = visible_text(paragraph)

                def walk(n):
                    if n is not paragraph and n.tag == W + "p":
                        return
                    if n.tag in {W + "del", W + "moveFrom"}:
                        return
                    if n.tag == W + "hyperlink":
                        rid = n.get(R + "id")
                        if rid and not rels.get(rid):
                            issues.append({"part": part, "issue": "missing hyperlink relationship", "id": rid})
                        label = visible_text(n)
                        add(rels.get(rid), label, "relationship", context)
                        for f in stack:
                            if f["separated"]:
                                f["label"].append(label)
                                f["nested_urls"].append(rels.get(rid))
                        return
                    if n.tag == W + "fldSimple":
                        m = FIELD_RE.match(n.get(W + "instr", ""))
                        if m:
                            label = visible_text(n)
                            add(m.group(1) or m.group(2), label, "simple_field", context)
                            for f in stack:
                                if f["separated"]:
                                    f["label"].append(label)
                            return
                    if n.tag == W + "fldChar":
                        kind = n.get(W + "fldCharType")
                        if kind == "begin":
                            stack.append({"instruction": [], "label": [], "separated": False,
                                          "context": context, "nested_urls": []})
                        elif kind == "separate" and stack:
                            stack[-1]["separated"] = True
                        elif kind == "end" and stack:
                            field = stack.pop()
                            m = FIELD_RE.match("".join(field["instruction"]))
                            if m:
                                url = m.group(1) or m.group(2)
                                if url not in field["nested_urls"]:
                                    add(url, "".join(field["label"]), "complex_field", field["context"])
                        return
                    if n.tag == W + "instrText":
                        if stack and not stack[-1]["separated"]:
                            stack[-1]["instruction"].append(n.text or "")
                        return
                    if n.tag == W + "t":
                        for f in stack:
                            if f["separated"]:
                                f["label"].append(n.text or "")
                        return
                    for child in n:
                        walk(child)

                walk(paragraph)
                emitted = records[start:]
                raw = Counter(u for u in urls_in(text) if figma_target(u))
                for link in emitted:
                    raw.subtract(u for u in urls_in(link["label"]) if figma_target(u))
                for url, count in raw.items():
                    if count > 0:
                        plain_urls.append({"part": part, "url": url, "occurrences": count})
                if not emitted and text.strip() and not urls_in(text):
                    context = text.strip()
            if stack:
                issues.append({"part": part, "issue": "unterminated field", "count": len(stack)})
    return {"links": records, "plain_text_urls": plain_urls, "issues": issues}


def target_key(row):
    return row["file_key"], (row.get("node_id") or "").replace("-", ":") or None


def check_inventory(links, inventory):
    if not isinstance(inventory, dict) or not isinstance(inventory.get("targets"), list):
        raise ValueError("Inventory must contain a targets array")
    scopes = {target_key(s) for s in inventory.get("scopes", [])}
    if not scopes:
        raise ValueError("Inventory must declare user-provided scopes")
    expected, problems, hidden = set(), [], []
    for row in inventory["targets"]:
        key = target_key(row)
        if not key[0] or not key[1]:
            raise ValueError("Inventory targets require file_key and node_id")
        expected.add(key)
        if row.get("role") not in {"page", "annotation", "entry"}:
            problems.append({"target": list(key), "issue": "missing or unsupported role"})
        if row.get("verified") is not True or row.get("exists") is not True:
            problems.append({"target": list(key), "issue": "target lacks positive verification evidence"})
        if (key[0], (row.get("scope_node_id") or "").replace("-", ":")) not in scopes:
            problems.append({"target": list(key), "issue": "target scope not in declared user scope"})
        if row.get("visible") is False and row.get("hidden_state_reason"):
            hidden.append({"target": list(key), "reason": row["hidden_state_reason"]})
        elif row.get("visible") is not True:
            problems.append({"target": list(key), "issue": "hidden or unverified visibility without state reason"})
    actual = {target_key(r) for r in links}
    return {"missing_targets": [list(k) for k in sorted(expected - actual, key=str)],
            "unexpected_targets": [list(k) for k in sorted(actual - expected, key=str)],
            "evidence_problems": problems, "intentional_hidden_states": hidden,
            "expected_unique_targets": len(expected)}


def preservation_check(before, after):
    """Keep original label/URL pairs as an ordered subsequence, allowing additions."""
    remaining = iter(after)
    missing = []
    for old in before:
        if not any((n["url"], n["label"]) == (old["url"], old["label"]) for n in remaining):
            missing.append({"label": old["label"], "url": old["url"]})
    return {"preserved": not missing, "missing_or_reordered_links": missing,
            "before_link_count": len(before)}


def audit(path, inventory=None, preserve_from=None):
    report = extract_docx(path)
    counts = Counter(target_key(r) for r in report["links"])
    report.update({"document": str(Path(path).resolve()), "clickable_figma_links": len(report["links"]),
                   "unique_figma_targets": len(counts),
                   "repeated_targets": [{"target": list(k), "occurrences": n} for k, n in counts.items() if n > 1],
                   "live_figma_access_performed": False})
    failures = bool(report["issues"])
    if inventory is not None:
        report["inventory_check"] = check_inventory(report["links"], inventory)
        failures |= any(report["inventory_check"][k] for k in ["missing_targets", "unexpected_targets", "evidence_problems"])
    if preserve_from is not None:
        original = extract_docx(preserve_from)
        report["preservation_check"] = preservation_check(original["links"], report["links"])
        if original["issues"]:
            report["preservation_check"]["baseline_issues"] = original["issues"]
        failures |= bool(original["issues"]) or not report["preservation_check"]["preserved"]
    report["local_checks_passed"] = not failures
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("document", type=Path)
    parser.add_argument("--inventory", type=Path)
    parser.add_argument("--preserve-from", type=Path)
    parser.add_argument("--json", dest="json_path", type=Path)
    args = parser.parse_args()
    try:
        if args.json_path and args.json_path.resolve() in {p.resolve() for p in [args.document, args.inventory, args.preserve_from] if p}:
            raise ValueError("JSON output must not overwrite an input file")
        inventory = json.loads(args.inventory.read_text()) if args.inventory else None
        report = audit(args.document, inventory, args.preserve_from)
        output = json.dumps(report, ensure_ascii=False, indent=2)
        if args.json_path:
            args.json_path.write_text(output + "\n", encoding="utf-8")
        print(output)
        return 0 if report["local_checks_passed"] else 1
    except (OSError, BadZipFile, ET.ParseError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
