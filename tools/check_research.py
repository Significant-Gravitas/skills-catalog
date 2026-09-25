#!/usr/bin/env python3
"""Check complete expert coverage and locally retained research bytes offline.

This checks provenance structure and integrity, not the quality of expert advice,
license interpretation, upstream execution, or successful platform installation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
from urllib.parse import unquote, urlsplit

EXPECTED_EXPERTS = 32
EXPECTED_ASSIGNMENTS = 321
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
SHA1 = re.compile(r"[0-9a-f]{40}\Z")
REPO = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\Z")
DISPOSITIONS = {"role-kit", "covered", "partial", "gap", "onboarding"}
LICENSE_NAMES = {"LICENSE", "LICENSE.md", "LICENSE.txt", "LICENCE", "LICENCE.md", "LICENCE.txt", "COPYING", "COPYING.md", "COPYING.txt"}


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key!r}")
        result[key] = value
    return result


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def _relative(value):
    if not isinstance(value, str) or not value or "\\" in value or ":" in value:
        raise ValueError(f"unsafe relative path: {value!r}")
    if any(ord(c) < 32 for c in value):
        raise ValueError("control character in path")
    if any(p in {"", ".", ".."} or p != p.strip() or p.endswith(".") for p in value.split("/")):
        raise ValueError(f"unnormalized relative path: {value!r}")
    return value


def _linked(path):
    try:
        return path.is_symlink() or bool(getattr(path.lstat(), "st_file_attributes", 0) & 0x400)
    except FileNotFoundError:
        return False


def _confined(root, value):
    value = _relative(value)
    target = root
    for part in value.split("/"):
        target = target / part
        if _linked(target):
            raise ValueError(f"symlink/reparse point: {value}")
    if not target.resolve().is_relative_to(root.resolve()):
        raise ValueError(f"path escapes root: {value}")
    return target


def _identity(source):
    if not isinstance(source, dict) or not REPO.fullmatch(str(source.get("repo", ""))):
        raise ValueError("source repo must be owner/repository")
    if not isinstance(source.get("commit"), str) or not SHA1.fullmatch(source["commit"]):
        raise ValueError("source commit must be an immutable 40-character SHA")
    path = _relative(source.get("path"))
    return source["repo"] + ":" + path


def _github_blob_identity(value):
    """Extract an exact pinned source identity, not merely a licence basename."""
    if not isinstance(value, str) or any(ord(c) < 33 for c in value):
        raise ValueError("additional license source_url must be an immutable GitHub blob URL")
    url = urlsplit(value)
    if url.scheme != "https" or url.netloc != "github.com" or url.query or url.fragment:
        raise ValueError("additional license source_url must be an immutable GitHub blob URL")
    parts = unquote(url.path, errors="strict").split("/", 5)
    if len(parts) != 6 or parts[0] or parts[3] != "blob":
        raise ValueError("additional license source_url must be an immutable GitHub blob URL")
    source = {"repo": parts[1] + "/" + parts[2], "commit": parts[4], "path": parts[5]}
    _identity(source)
    return source["repo"], source["commit"], source["path"]


def validate(root: Path) -> list[str]:
    """Return actionable errors; never execute or import retained upstream code."""
    root = Path(root).resolve()
    errors = []
    evidence_archives, deferred_archives = set(), set()

    def error(label, message):
        errors.append(f"{label}: {message}")

    def read_json(relative):
        try:
            result = json.loads(_confined(root, relative).read_text(encoding="utf-8"), object_pairs_hook=_pairs)
            if not isinstance(result, dict):
                raise ValueError("document must be a JSON object")
            return result
        except (OSError, UnicodeError, ValueError) as exc:
            error(relative, str(exc))
            return {}

    def array(document, key, label):
        if not isinstance(document, dict) or not isinstance(document.get(key), list):
            error(label, f"{key} must be an array")
            return []
        return document[key]

    def checked_bytes(record, path_key, prefix, label, referenced, *, blob=False):
        if not isinstance(record, dict):
            error(label, "file record must be an object")
            return
        digest, size, relative = record.get("sha256"), record.get("size"), record.get(path_key)
        if not isinstance(digest, str) or not SHA256.fullmatch(digest):
            error(label, "invalid SHA-256")
            return
        if type(size) is not int or size < 0:
            error(label, "size must be a nonnegative integer")
            return
        if relative != prefix + digest:
            error(label, f"{path_key} must be {prefix}<sha256>")
            return
        referenced.add(relative)
        try:
            content = _confined(root, relative).read_bytes()
            if len(content) != size or hashlib.sha256(content).hexdigest() != digest:
                error(label, "captured bytes differ from size/SHA-256")
            if blob:
                expected = record.get("blob_sha1")
                got = hashlib.sha1(b"blob " + str(len(content)).encode("ascii") + b"\0" + content).hexdigest()
                if not isinstance(expected, str) or not SHA1.fullmatch(expected) or got != expected:
                    error(label, "original Git blob SHA-1 differs or is invalid")
        except (OSError, ValueError) as exc:
            error(label, str(exc))

    baseline = read_json("provenance/roster-baseline.json")
    roster_rows = array(baseline, "experts", "roster baseline")
    if not isinstance(baseline.get("commit"), str) or not SHA1.fullmatch(baseline["commit"]):
        error("roster baseline", "missing immutable roster commit")
    if baseline.get("expected_experts") != EXPECTED_EXPERTS or baseline.get("expected_assignments") != EXPECTED_ASSIGNMENTS:
        error("roster baseline", "declared totals must be 32 experts and 321 assignments")
    roster = {}
    assignment_total = 0
    for i, row in enumerate(roster_rows):
        label = f"roster expert[{i}]"
        if not isinstance(row, dict) or not _text(row.get("name")) or not _text(row.get("job_title")):
            error(label, "name and job_title are required")
            continue
        name = row["name"]
        if name in roster:
            error(label, f"duplicate expert {name}")
        slugs = array(row, "bundled_skills", label)
        if any(not _text(s) for s in slugs):
            error(label, "bundled_skills must contain nonempty slug strings")
            slugs = [s for s in slugs if _text(s)]
        if len(set(slugs)) != len(slugs):
            error(label, "duplicate original skill assignment")
        roster[name] = set(slugs)
        assignment_total += len(slugs)
    if len(roster_rows) != EXPECTED_EXPERTS or len(roster) != EXPECTED_EXPERTS or assignment_total != EXPECTED_ASSIGNMENTS:
        error("roster baseline", f"actual totals differ: {len(roster_rows)} rows, {len(roster)} unique experts, {assignment_total} assignments")

    evidence = read_json("provenance/evidence.json")
    observations = array(evidence, "observations", "evidence")
    observation_ids = set()
    for i, observation in enumerate(observations):
        label = f"evidence observation[{i}]"
        if not isinstance(observation, dict) or not _text(observation.get("id")):
            error(label, "observation id is required")
            continue
        if observation["id"] in observation_ids:
            error(label, "duplicate observation id")
        observation_ids.add(observation["id"])
        capture = observation.get("capture")
        checked_bytes(capture, "file", "provenance/evidence-files/", label, evidence_archives)
        if isinstance(capture, dict) and observation.get("original_response_sha256") is not None and observation["original_response_sha256"] != capture.get("sha256"):
            error(label, "capture differs from original_response_sha256")

    def evidence_ids(record, label):
        ids = record.get("evidence_ids", [])
        if not isinstance(ids, list) or any(not _text(i) for i in ids):
            error(label, "evidence_ids must be an array of observation ids")
        elif len(ids) != len(set(ids)) or any(i not in observation_ids for i in ids):
            error(label, "duplicate or unresolved evidence id")

    installed = set()
    try:
        proofs_dir = _confined(root, "provenance/skills")
        if not proofs_dir.is_dir():
            error("installed sources", "provenance/skills directory is missing")
        for path in sorted(proofs_dir.glob("*.json")):
            relative = path.relative_to(root).as_posix()
            proof = read_json(relative)
            try:
                identity = _identity(proof.get("source"))
                if identity in installed:
                    error(relative, "duplicate installed source identity")
                installed.add(identity)
            except ValueError as exc:
                error(relative, str(exc))
            evidence_ids(proof, relative)
    except (OSError, ValueError) as exc:
        error("installed sources", str(exc))

    deferred_doc = read_json("provenance/deferred-skills.json")
    deferred_rows = array(deferred_doc, "skills", "deferred sources")
    deferred_ids, checked_collections = set(), set()
    for i, entry in enumerate(deferred_rows):
        label = f"deferred skill[{i}]"
        if not isinstance(entry, dict):
            error(label, "entry must be an object")
            continue
        source = entry.get("source")
        try:
            identity = _identity(source)
            if entry.get("id") != identity:
                error(label, "id must equal source repo:path")
            if identity in deferred_ids:
                error(label, "duplicate deferred identity")
            deferred_ids.add(identity)
        except ValueError as exc:
            error(label, str(exc))
            source = None
        if not _text(entry.get("author")) or not _text(entry.get("reason")):
            error(label, "original author and deferral reason are required")
        if not _text(entry.get("license")) and not isinstance(entry.get("license"), dict):
            error(label, "license metadata is required, including for a license holdout")
        evidence_ids(entry, label)
        for j, capture in enumerate(entry.get("evidence", []) if isinstance(entry.get("evidence", []), list) else []):
            checked_bytes(capture.get("capture", capture) if isinstance(capture, dict) else capture, "file", "provenance/evidence-files/", f"{label} evidence[{j}]", evidence_archives)
        if "files" in entry and "source_files_ref" in entry:
            error(label, "use files or source_files_ref, not both")
        if "source_files_ref" in entry:
            ref = entry["source_files_ref"]
            files = deferred_doc.get(ref) if isinstance(ref, str) else None
            collection = ("shared", ref) if isinstance(ref, str) else ("invalid-ref", i)
            if not isinstance(files, list):
                error(label, "source_files_ref does not resolve to a root file array")
                files = []
        else:
            files = entry.get("files")
            collection = ("entry", i)
            if not isinstance(files, list):
                error(label, "files must be an array")
                files = []
        valid_files = [f for f in files if isinstance(f, dict)]
        if collection not in checked_collections:
            checked_collections.add(collection)
            seen_sources = set()
            for j, record in enumerate(files):
                file_label = f"deferred files {collection}[{j}]"
                if not isinstance(record, dict):
                    error(file_label, "file record must be an object")
                    continue
                try:
                    _identity(record)
                    source_key = (record["repo"], record["commit"], record["path"])
                    if source_key in seen_sources:
                        error(file_label, "duplicate source file")
                    seen_sources.add(source_key)
                except ValueError as exc:
                    error(file_label, str(exc))
                if record.get("mode") not in ("100644", "100755"):
                    error(file_label, "mode must preserve 100644 or 100755")
                checked_bytes(record, "archive", "provenance/deferred-originals/", file_label, deferred_archives, blob=True)
        if source:
            same_source = [f for f in valid_files if f.get("repo") == source["repo"] and f.get("commit") == source["commit"]]
            paths = {f.get("path") for f in same_source if isinstance(f.get("path"), str)}
            if source["path"] + "/SKILL.md" not in paths:
                error(label, "primary SKILL.md absent at the declared repo/commit/path")
            ancestors = {str(p) for p in (PurePosixPath(source["path"]), *PurePosixPath(source["path"]).parents)}
            if not any(PurePosixPath(p).name in LICENSE_NAMES and str(PurePosixPath(p).parent) in ancestors for p in paths):
                error(label, "controlling ancestor license source file is absent")
            for field in ("license_paths", "notice_paths"):
                declared = entry.get(field, [])
                if not isinstance(declared, list) or any(not isinstance(p, str) or p not in paths for p in declared):
                    error(label, f"declared {field} are absent from matching pinned sources")
        additional = entry.get("additional_licenses", [])
        if not isinstance(additional, list):
            error(label, "additional_licenses must be an array")
            additional = []
        file_identities = {(f["repo"], f["commit"], f["path"]) for f in valid_files
                           if all(isinstance(f.get(k), str) for k in ("repo", "commit", "path"))}
        for j, notice in enumerate(additional):
            notice_label = f"{label} additional license[{j}]"
            try:
                identity = _github_blob_identity(notice.get("source_url") if isinstance(notice, dict) else None)
                if identity not in file_identities:
                    error(notice_label, "declared additional license is absent from exact pinned sources")
            except ValueError as exc:
                error(notice_label, str(exc))
    overlap = installed & deferred_ids
    if overlap:
        error("source identities", "installed/deferred overlap: " + ", ".join(sorted(overlap)))
    available = installed | deferred_ids

    coverage = read_json("provenance/expert-coverage.json")
    if coverage.get("schema_version") != 1:
        error("expert coverage", "schema_version must be 1")
    expert_rows = array(coverage, "experts", "expert coverage")
    covered_experts = set()
    covered_assignments = 0
    for i, expert in enumerate(expert_rows):
        label = f"coverage expert[{i}]"
        if not isinstance(expert, dict) or not _text(expert.get("name")):
            error(label, "name is required")
            continue
        name = expert["name"]
        label = f"coverage {name}"
        if name in covered_experts:
            error(label, "duplicate expert")
        covered_experts.add(name)
        if not _text(expert.get("role")):
            error(label, "role is required")
        kit_rows = array(expert, "kit", label)
        kit = {s for s in kit_rows if isinstance(s, str)}
        if len(kit) != len(kit_rows):
            error(label, "kit contains duplicate or invalid identities")
        unresolved = kit - available
        if unresolved:
            error(label, "unresolved kit id: " + ", ".join(sorted(unresolved)))
        originals = array(expert, "original_skills", label)
        covered_assignments += len(originals)
        slugs = []
        for j, original in enumerate(originals):
            row_label = f"{label} original[{j}]"
            if not isinstance(original, dict) or not _text(original.get("slug")):
                error(row_label, "slug is required")
                continue
            slugs.append(original["slug"])
            if not _text(original.get("essential_function")):
                error(row_label, "essential_function is required")
            disposition = original.get("disposition")
            if not isinstance(disposition, str) or disposition not in DISPOSITIONS:
                error(row_label, "invalid disposition")
                disposition = None
            if disposition in {"partial", "gap"} and not _text(original.get("gap")):
                error(row_label, "partial/gap disposition must explain missing capability")
            replacements = array(original, "replacements", row_label)
            if disposition == "covered" and not replacements:
                error(row_label, "covered disposition requires a replacement")
            mapping_ids = []
            for k, replacement in enumerate(replacements):
                mapping_label = f"{row_label} replacement[{k}]"
                if not isinstance(replacement, dict):
                    error(mapping_label, "replacement must be an object")
                    continue
                identity = replacement.get("id")
                if not isinstance(identity, str) or identity not in available:
                    error(mapping_label, "unresolved replacement id")
                elif identity not in kit:
                    error(mapping_label, "replacement does not belong to this expert's kit")
                if isinstance(identity, str):
                    mapping_ids.append(identity)
                if not _text(replacement.get("fit")) or not _text(replacement.get("why")):
                    error(mapping_label, "fit and why are required")
            if len(mapping_ids) != len(set(mapping_ids)):
                error(row_label, "duplicate replacement id")
        if len(slugs) != len(set(slugs)):
            error(label, "duplicate original skill row")
        expected = roster.get(name, set())
        if set(slugs) != expected:
            error(label, f"original roster mismatch; missing={sorted(expected - set(slugs))}, extra={sorted(set(slugs) - expected)}")
    if covered_experts != set(roster):
        error("expert coverage", f"expert roster mismatch; missing={sorted(set(roster) - covered_experts)}, extra={sorted(covered_experts - set(roster))}")
    if len(expert_rows) != EXPECTED_EXPERTS or len(covered_experts) != EXPECTED_EXPERTS or covered_assignments != EXPECTED_ASSIGNMENTS:
        error("expert coverage", f"actual totals differ: {len(expert_rows)} rows, {len(covered_experts)} unique experts, {covered_assignments} assignments")

    def orphan_check(directory, referenced):
        try:
            base = _confined(root, directory)
            if not base.exists():
                if referenced:
                    error(directory, "archive directory is absent")
                return
            for current, dirs, files in os.walk(base, followlinks=False):
                for name in dirs + files:
                    path = Path(current) / name
                    relative = path.relative_to(root).as_posix()
                    if _linked(path):
                        error(relative, "symlink/reparse point in archive")
                    elif path.is_file() and relative not in referenced:
                        error(relative, "orphan archive is not referenced by provenance")
        except (OSError, ValueError) as exc:
            error(directory, str(exc))

    orphan_check("provenance/deferred-originals", deferred_archives)
    orphan_check("provenance/evidence-files", evidence_archives)
    return errors


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    args = parser.parse_args(argv)
    errors = validate(args.root)
    print(json.dumps({"status": "PASS" if not errors else "FAIL", "errors": errors}, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
