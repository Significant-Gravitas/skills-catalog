#!/usr/bin/env python3
"""Replay reviewed packaging changes; never execute upstream skill code.

The provenance manifest is a build/audit record, not an AutoGPT import format.
Only ordinary skills/<name>/ packages are consumed by the platform.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import yaml

FRONTMATTER = re.compile(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|$)(.*)\Z", re.S)


def split_frontmatter(text: str) -> tuple[dict, str]:
    match = FRONTMATTER.fullmatch(text)
    if match is None:
        raise ValueError("SKILL.md must begin with YAML frontmatter")
    metadata = yaml.safe_load(match.group(1))
    if not isinstance(metadata, dict):
        raise ValueError("frontmatter must be a mapping")
    return metadata, match.group(2)


def metadata_string(value: object) -> str:
    """Agent Skills metadata values are strings; preserve scalar meaning."""
    if isinstance(value, str):
        return value
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
    if value is True:
        return "true"
    if value is False:
        return "false"
    return str(value)


def render_file(record: dict, root: Path) -> bytes:
    """Render one manifest member from its original bytes and counted edits."""
    source = record.get("source")
    if source is None:
        if record.get("transformations"):
            raise ValueError("generated content cannot have source transformations")
        return record["content"].encode("utf-8")
    relative = source["archive"]
    if not re.fullmatch(r"provenance/originals/[0-9a-f]{64}", relative):
        raise ValueError("invalid original archive path")
    archive = root / relative
    if archive.is_symlink() or not archive.resolve().is_relative_to(root.resolve()):
        raise ValueError("original archive escapes repository")
    data = archive.read_bytes()
    if len(data) != source["size"] or hashlib.sha256(data).hexdigest() != source["sha256"]:
        raise ValueError("original archive checksum mismatch")
    for change in record.get("transformations", []):
        if not change.get("reason"):
            raise ValueError("every transformation needs a review reason")
        text = data.decode("utf-8")
        kind = change["kind"]
        if kind == "replace":
            old, new = change["old"], change["new"]
            expected = change["expected_count"]
            if not old or old == new or not isinstance(expected, int) or expected < 1:
                raise ValueError("replacement must be a nonempty, counted change")
            if text.count(old) != expected:
                raise ValueError(f"replacement count changed for {record['path']}: {old!r}")
            data = text.replace(old, new).encode("utf-8")
        elif kind == "frontmatter":
            frontmatter, body = split_frontmatter(text)
            for key, value in change["updates"].items():
                if key == "metadata":
                    existing = frontmatter.get("metadata", {})
                    if not isinstance(existing, dict):
                        raise ValueError("upstream metadata is not a mapping")
                    frontmatter[key] = {str(k): metadata_string(v) for k, v in {**existing, **value}.items()}
                else:
                    frontmatter[key] = value
            # Normalize the YAML header only. Do not trim/reflow authored prose.
            header = yaml.safe_dump(frontmatter, allow_unicode=True, sort_keys=False, width=10000)
            data = ("---\n" + header + "---\n" + body).encode("utf-8")
        elif kind == "notice":
            notice = change["text"]
            match = FRONTMATTER.fullmatch(text)
            if match:
                # Preserve the already-rendered header; put the notice in the body.
                position = match.start(2)
                text = text[:position] + "\n" + notice + "\n\n" + text[position:]
            else:
                text = notice + "\n\n" + text
            data = text.encode("utf-8")
        else:
            raise ValueError(f"unsupported packaging transformation: {kind}")
    return data
