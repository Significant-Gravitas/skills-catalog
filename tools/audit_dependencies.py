#!/usr/bin/env python3
"""Report static package references as JSON; never import or execute skill code.

--check fails only definite missing/escaping Markdown file links. Literal paths,
Python imports, native commands and generated state are narrower heuristics and
remain review items. An optional provenance/dependency-review.json accepts exact
{package, file, kind, target, classification, reason} reference exceptions.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from typing import Any
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent.parent
REVIEW_CLASSES = {"project-state", "generated-output", "native-runtime", "optional-reference", "reviewed-nonlocal"}
RESOURCE_PREFIXES = ("references/", "scripts/", "assets/", "tools/", "support/", "templates/", "shared/", "./", "../")
STATE_PREFIXES = (".agents/", ".claude/", "memory/")
STATE_FILES = {"TASKS.md", "CLAUDE.md"}
DYNAMIC = re.compile(r"\$\{|\{\{|\{(?:baseDir|skill[_-]?root|package[_-]?root)\}|<[A-Za-z][^>]*>|\$[A-Za-z_]")
FILE_SUFFIX = re.compile(r"\.(?:md|txt|json|ya?ml|toml|py|js|mjs|cjs|sh|html|css|svg|png|csv|sql|lock)$", re.I)
INLINE_CODE = re.compile(r"(?<!`)(`+)(?!`)(.*?)\1(?!`)")
NATIVE_COMMAND = re.compile(r"^/[a-zA-Z0-9_-]+:[a-zA-Z0-9_:/.-]+$")

LIMITATIONS = [
    "Static reference inventory, not proof of complete dependencies or runtime compatibility; no skill code, shell commands, imports or services are executed.",
    "Markdown inline and reference-style links are checked outside fenced and inline code. File existence is checked after decoding URL paths and removing query/fragment; heading/HTML anchors are reported but not validated.",
    "Known literal file references are inventoried from inline/fenced code; missing literal paths may be examples, outputs or runtime inputs and do not fail --check.",
    "Python AST imports are inspected without executing code. Conditional imports, installed modules, namespace packages, dynamic loading and script working-directory behavior cannot be established statically; import findings do not fail --check.",
    "JavaScript/shell imports, HTML links, templated Markdown, filesystem calls and remote URL availability are not exhaustively analyzed. Native commands, interpolation and known project-state paths require runtime review.",
    "Hidden files/directories are included. Symlink/reparse subtrees are reported and not traversed. Only SKILL.md-parent directories are package roots; support outside those roots is not implicitly available to a package.",
    "Exact-match reviewed references are visible with their reason and original classification. Unused or hash-mismatched review records are reported for maintenance; they never silently match broader paths.",
    "Literal original paths inside ATTRIBUTION.md are classified as source provenance only when they exactly match source repo/path pairs in provenance/files.json; normal Markdown file links there are still checked.",
]


def _is_link(path: Path) -> bool:
    return path.is_symlink() or bool(getattr(path.lstat(), "st_file_attributes", 0) & 0x400)


def _walk(directory: Path):
    """Include dotfiles; do not traverse any symlink/junction subtree."""
    for current, dirs, files in os.walk(directory, followlinks=False):
        for name in sorted(dirs.copy()):
            child = Path(current) / name
            if _is_link(child):
                dirs.remove(name)
                yield child, True
        dirs.sort()
        for name in sorted(files):
            child = Path(current) / name
            yield child, _is_link(child)


def _visible_markdown(text: str) -> tuple[str, list[tuple[int, str]]]:
    """Mask fenced blocks while retaining offsets and collecting code for review."""
    lines = text.splitlines(keepends=True)
    fence = None
    visible, code = [], []
    for number, line in enumerate(lines, 1):
        opening = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line)
        if fence:
            if re.match(r"^ {0,3}" + re.escape(fence[0]) + "{" + str(fence[1]) + r",}\s*$", line):
                fence = None
            else:
                code.append((number, line))
            visible.append(re.sub(r"[^\r\n]", " ", line))
        elif opening:
            fence = (opening[1][0], len(opening[1]))
            visible.append(re.sub(r"[^\r\n]", " ", line))
        else:
            visible.append(line)
    return "".join(visible), code


def _destination(text: str, offset: int = 0) -> tuple[str, int] | None:
    """Read an angle destination or one balanced, escaped Markdown token."""
    i = offset
    while i < len(text) and text[i].isspace():
        i += 1
    start = i
    if i < len(text) and text[i] == "<":
        end = text.find(">", i + 1)
        return (text[i + 1:end], end + 1) if end >= 0 else None
    depth = 0
    while i < len(text):
        char = text[i]
        if char == "\\" and i + 1 < len(text):
            i += 2
            continue
        if char == "(":
            depth += 1
        elif char == ")":
            if not depth:
                break
            depth -= 1
        elif char.isspace() and not depth:
            break
        i += 1
    return text[start:i], i


def markdown_links(text: str):
    visible, _ = _visible_markdown(text)
    visible = INLINE_CODE.sub(lambda m: " " * len(m[0]), visible)
    definitions = {}
    for m in re.finditer(r"(?m)^ {0,3}\[(?!\^)([^\]\n]+)\]:[^\S\r\n]*(.*)$", visible):
        dest = _destination(m[2])
        if dest:
            definitions[" ".join(m[1].casefold().split())] = (dest[0], visible.count("\n", 0, m.start()) + 1)
    # Definitions are metadata, not uses; unused definitions do not create errors.
    without_definitions = re.sub(r"(?m)^ {0,3}\[[^\]\n]+\]:.*$", lambda m: " " * len(m[0]), visible)
    occupied = []
    for m in re.finditer(r"!?\[[^\]\n]*\]\(", without_definitions):
        destination = _destination(without_definitions, m.end())
        if not destination:
            continue
        target, end = destination
        # An optional title may follow; demand a closing delimiter rather than
        # treating arbitrary prose after a malformed link as a filesystem path.
        tail = without_definitions[end:]
        closing = re.match(r'''\s*(?:(?:"[^"\n]*"|'[^'\n]*'|\([^\n]*?\))\s*)?\)''', tail)
        if closing:
            occupied.append((m.start(), end + closing.end()))
            yield visible.count("\n", 0, m.start()) + 1, target
    for m in re.finditer(r"!?\[([^\]\n]+)\](?:\[([^\]\n]*)\])?", without_definitions):
        if any(a <= m.start() < b for a, b in occupied):
            continue
        key = " ".join((m[2] or m[1]).casefold().split())
        if key in definitions:
            yield visible.count("\n", 0, m.start()) + 1, definitions[key][0]


def _unescape(target: str) -> str:
    return re.sub(r"\\([\\`*{}\[\]()#+.!_<> -])", r"\1", target)


def _local(package: Path, source: Path, target: str, *, literal: bool = False) -> dict:
    raw = _unescape(target.strip())
    if NATIVE_COMMAND.fullmatch(raw):
        return {"classification": "native-command", "status": "review"}
    if DYNAMIC.search(raw) or raw.startswith("~"):
        return {"classification": "dynamic-runtime-reference", "status": "review"}
    if raw.startswith("//"):
        return {"classification": "external-url", "status": "unverified"}
    if re.match(r"^[A-Za-z]:[/\\]", raw) or raw.startswith("file:"):
        return {"classification": "absolute-filesystem-reference", "status": "review"}
    try:
        parsed = urlsplit(raw)
    except ValueError:
        return {"classification": "unparsed-reference", "status": "review"}
    if parsed.scheme:
        return {"classification": "external-url" if parsed.scheme in {"http", "https"} else "external-scheme", "status": "unverified"}
    if not parsed.path:
        return {"classification": "document-anchor", "status": "ok", "anchor_checked": False}
    path = unquote(parsed.path).replace("\\", "/")
    if path.startswith("/"):
        return {"classification": "root-relative-reference", "status": "review", "note": "Could be a site route or host path; not presumed package-local."}
    root = package.resolve()
    candidates = [source.parent / path]
    if literal and not path.startswith("../"):
        candidates.append(package / path)
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved.is_relative_to(root) and resolved.exists():
            return {"classification": "local-file" if resolved.is_file() else "local-directory", "status": "ok", "resolved": resolved.relative_to(root).as_posix(), "anchor_checked": False if parsed.fragment else None}
    # Existing paths win over the runtime-state heuristics, including hidden
    # package support such as .mcp.json. Never blanket-ignore dot directories.
    if ".." not in path.split("/") and (path.startswith(STATE_PREFIXES) or path in STATE_FILES):
        return {"classification": "project-state", "status": "review"}
    if not candidates[0].resolve().is_relative_to(root):
        return {"classification": "escaping-local-path", "status": "review" if literal else "error"}
    return {"classification": "unresolved-literal" if literal else "missing-local-file", "status": "review" if literal else "error"}


def _literal_candidates(text: str):
    visible, fenced = _visible_markdown(text)
    for m in INLINE_CODE.finditer(visible):
        candidate = m[2].strip()
        line = visible.count("\n", 0, m.start()) + 1
        if candidate and not re.fullmatch(r"\.[A-Za-z0-9]+", candidate) and (NATIVE_COMMAND.fullmatch(candidate) or DYNAMIC.search(candidate) or candidate.startswith(STATE_PREFIXES) or (" " not in candidate and (candidate.startswith(RESOURCE_PREFIXES) or FILE_SUFFIX.search(candidate)))):
            yield line, candidate
    # Only path-shaped single tokens in code blocks, not arbitrary quoted API
    # field names or prose. They are review inventory, never definite errors.
    for line, code in fenced:
        for m in re.finditer(r"(?<![\w/])(?:\.{1,2}/|references/|scripts/|assets/|tools/|templates/|\.agents/|\.claude/)[^\s`'\"<>|;)]+", code):
            candidate = m[0].rstrip(",")
            if FILE_SUFFIX.search(candidate):
                yield line, candidate


def _python_imports(package: Path, source: Path, raw: bytes):
    try:
        tree = ast.parse(raw, filename=source.name)
    except (SyntaxError, ValueError, UnicodeError) as exc:
        yield 1, source.name, {"classification": "python-not-parsed", "status": "review", "note": type(exc).__name__}
        return
    root = package.resolve()
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Import, ast.ImportFrom)):
            continue
        if isinstance(node, ast.ImportFrom) and node.level:
            directory = source.parent
            for _ in range(node.level - 1):
                directory = directory.parent
            target = "." * node.level + (node.module or "")
            if not directory.resolve().is_relative_to(root):
                yield node.lineno, target, {"classification": "escaping-python-relative-import", "status": "review"}
                continue
            modules = [node.module] if node.module else [a.name for a in node.names]
            for module in modules:
                stem = directory.joinpath(*module.split("."))
                options = [stem.with_suffix(".py"), stem / "__init__.py"]
                existing = next((p for p in options if p.is_file() and p.resolve().is_relative_to(root)), None)
                yield node.lineno, target + (" " + module if node.module is None else ""), {"classification": "python-local-import" if existing else "unresolved-python-relative-import", "status": "ok" if existing else "review", **({"resolved": existing.relative_to(package).as_posix()} if existing else {"note": "May be a namespace, attribute, compiled extension or runtime import context."})}
        else:
            modules = [node.module] if isinstance(node, ast.ImportFrom) else [a.name for a in node.names]
            for module in modules:
                stem = source.parent.joinpath(*module.split("."))
                existing = next((p for p in [stem.with_suffix(".py"), stem / "__init__.py"] if p.is_file() and p.resolve().is_relative_to(root)), None)
                yield node.lineno, module, {"classification": "python-local-import" if existing else "python-environment-import", "status": "ok" if existing else "unverified", **({"resolved": existing.relative_to(package).as_posix()} if existing else {})}


def _load_reviews(path: Path) -> list[dict]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schema_version") != 1 or not isinstance(data.get("references", []), list):
        raise ValueError("dependency review must have schema_version: 1 and an optional references: []")
    seen = set()
    for item in data.get("references", []):
        if not isinstance(item, dict) or any(not isinstance(item.get(k), str) or not item[k].strip() for k in ("package", "file", "kind", "target", "classification", "reason")):
            raise ValueError("every reviewed reference needs exact package, file, kind, target, classification and reason strings")
        key = tuple(item[k] for k in ("package", "file", "kind", "target"))
        if key in seen or item["classification"] not in REVIEW_CLASSES:
            raise ValueError("duplicate or unsupported reviewed reference")
        seen.add(key)
        if "source_sha256" in item and not re.fullmatch(r"[a-f0-9]{64}", item["source_sha256"]):
            raise ValueError("review source_sha256 must be a lowercase SHA-256 hash")
    return data.get("references", [])


def audit(root: Path = ROOT, review_path: Path | None = None) -> dict[str, Any]:
    root = root.resolve()
    reviews = _load_reviews(review_path or root / "provenance/dependency-review.json")
    indexed = {tuple(r[k] for k in ("package", "file", "kind", "target")): r for r in reviews}
    matched = set()
    findings, packages, hashes = [], [], {}
    source_paths = set()
    provenance_path = root / "provenance/files.json"
    if provenance_path.exists():
        provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
        for record in provenance.get("files", []):
            origin = record.get("source")
            if isinstance(origin, dict) and isinstance(origin.get("repo"), str) and isinstance(origin.get("path"), str):
                source_paths.add(origin["repo"] + "/" + origin["path"])
    skills = root / "skills"
    discovered = list(_walk(skills)) if skills.is_dir() else []
    package_roots = sorted({p.parent for p, link in discovered if p.name == "SKILL.md" and not link})
    for package in package_roots:
        package_id = package.relative_to(skills).as_posix()
        # A nested SKILL.md is another package, not supplementary content here.
        nested = [p for p in package_roots if p != package and p.is_relative_to(package)]
        file_count = 0
        start = len(findings)
        for source, link in _walk(package):
            if any(source.is_relative_to(p) for p in nested):
                continue
            relative = source.relative_to(package).as_posix()
            if link:
                findings.append(dict(package=package_id, file=relative, line=1, kind="filesystem", target=relative, classification="symlink-resource-not-scanned", status="review"))
                continue
            file_count += 1
            raw = source.read_bytes()
            hashes[(package_id, relative)] = hashlib.sha256(raw).hexdigest()
            if source.suffix.lower() in {".md", ".markdown"}:
                try:
                    text = raw.decode("utf-8-sig")
                except UnicodeDecodeError:
                    findings.append(dict(package=package_id, file=relative, line=1, kind="markdown", target=relative, classification="markdown-not-utf8", status="review"))
                    continue
                for line, target in markdown_links(text):
                    findings.append(dict(package=package_id, file=relative, line=line, kind="markdown-link", target=target, **_local(package, source, target)))
                for line, target in _literal_candidates(text):
                    result = _local(package, source, target, literal=True)
                    if source.name == "ATTRIBUTION.md" and target in source_paths:
                        result = {"classification": "source-provenance-reference", "status": "informational", "note": "Exact original repo/path recorded in provenance/files.json; not an installed resource path."}
                    findings.append(dict(package=package_id, file=relative, line=line, kind="literal-reference", target=target, **result))
            elif source.suffix.lower() == ".py":
                for line, target, result in _python_imports(package, source, raw):
                    findings.append(dict(package=package_id, file=relative, line=line, kind="python-import", target=target, **result))
        packages.append({"package": package_id, "files_scanned": file_count, "references": len(findings) - start})
    for finding in findings:
        key = tuple(finding[k] for k in ("package", "file", "kind", "target"))
        review = indexed.get(key)
        if review and ("source_sha256" not in review or review["source_sha256"] == hashes.get(key[:2])):
            matched.add(key)
            finding.update(original_classification=finding["classification"], original_status=finding["status"], classification=review["classification"], status="reviewed", review_reason=review["reason"])
    unused = [{**r, "note": "Not matched, or source_sha256 no longer matches."} for key, r in indexed.items() if key not in matched]
    # Discovery can encounter links before reaching any package root.
    discovery_notes = [{"path": p.relative_to(skills).as_posix(), "classification": "symlink-not-traversed"} for p, link in discovered if link]
    return {"schema_version": 1, "scope": "static package reference audit", "limitations": LIMITATIONS, "check_policy": "Only findings with status=error (definite missing/escaping Markdown file links) fail --check. Review inventory is not an execution verdict.", "counts": {"packages": len(packages), "files_scanned": sum(p["files_scanned"] for p in packages), "references": len(findings), "definite_errors": sum(f["status"] == "error" for f in findings), "review_items": sum(f["status"] == "review" for f in findings), "reviewed_references": sum(f["status"] == "reviewed" for f in findings), "unused_reviews": len(unused), "classifications": dict(sorted(Counter(f["classification"] for f in findings).items()))}, "packages": packages, "findings": findings, "unused_reviews": unused, "discovery_notes": discovery_notes}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="catalogue repository root")
    parser.add_argument("--review", type=Path, help="optional reviewed-reference JSON (default: ROOT/provenance/dependency-review.json)")
    parser.add_argument("--check", action="store_true", help="return 1 only for definite local Markdown link errors")
    args = parser.parse_args(argv)
    try:
        report = audit(args.root, args.review)
    except (OSError, ValueError) as exc:
        print(json.dumps({"schema_version": 1, "audit_error": str(exc), "error_type": type(exc).__name__}, indent=2))
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if args.check and report["counts"]["definite_errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
