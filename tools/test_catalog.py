"""Offline regression tests for preservation, provenance and immutable replay."""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

import check
import vendor

PIN = "1" * 40


class CatalogTests(unittest.TestCase):
    def setUp(self) -> None:
        # Explicitly owned test directories remain inside this tools directory.
        self.temporary = tempfile.TemporaryDirectory(prefix="catalog-test-", dir=Path(__file__).parent)
        self.root = Path(self.temporary.name).resolve()
        self.assertEqual(self.root.parent, Path(__file__).resolve().parent)
        self.addCleanup(self.temporary.cleanup)
        self.entries = []
        self.records = []
        self.proofs = {}
        self.contents = {}
        for slug, upstream in (("first-registration", "skills/one"), ("second-registration", "skills/two")):
            path = f"skills/example/repo/{upstream}"
            # Original names may be duplicate, mixed case, spaced or non-slugs.
            name = "Original Name"
            entry = dict(slug=slug, name=name, path=path, package_root="skills/example/repo", source=f"example/repo/{upstream}", upstream_commit=PIN, license="MIT", categories=["operations"], required_providers=[], status="core", experts=["Example"])
            entry["provenance"] = f"provenance/skills/{slug}.json"
            self.entries.append(entry)
            body = b'---\r\nname: "Original Name"\r\ndescription: source text\r\n---\r\n[Shared](../shared/example.md)\r\n'
            # Exceed old body caps deliberately: preservation is not import parity.
            body += b"unchanged\r\n" * 5100
            primary = self.add_file(f"{path}/SKILL.md", f"{upstream}/SKILL.md", body)
            self.add_file(f"{path}/LICENSE", "LICENSE", b"Copyright Example\r\nMIT license fixture\r\n", role="license-copy")
            self.proofs[slug] = dict(slug=slug, name=name, status="core", source=dict(repo="example/repo", commit=PIN, path=upstream), author="Example upstream contributors", license=dict(spdx="MIT", file=path + "/LICENSE", source_url=f"https://github.com/example/repo/blob/{PIN}/LICENSE"), primary_sha256=primary["sha256"], evidence_ids=["observed-installs"])
        self.add_file("skills/example/repo/skills/shared/.example.bin", "skills/shared/.example.bin", b"\x00\xff\r\n")
        self.save()

    def add_file(self, path, source_path, data, *, role="upstream", mode="100644"):
        record = dict(path=path, source=dict(repo="example/repo", commit=PIN, path=source_path, blob_sha1=check.git_blob_sha1(data)), sha256=hashlib.sha256(data).hexdigest(), size=len(data), mode=mode, role=role)
        self.records.append(record)
        self.contents[vendor.raw_url(record)] = data
        destination = self.root / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
        return record

    def save(self):
        (self.root / "catalog.yml").write_text(yaml.safe_dump(dict(schema_version=2, skills=self.entries)), encoding="utf-8")
        provenance = self.root / "provenance"
        (provenance / "skills").mkdir(parents=True, exist_ok=True)
        (provenance / "files.json").write_text(json.dumps(dict(schema_version=2, files=self.records)), encoding="utf-8")
        (provenance / "evidence.json").write_text(json.dumps(dict(schema_version=2, observations=[dict(id="observed-installs", value=42)])), encoding="utf-8")
        for slug, proof in self.proofs.items():
            (provenance / "skills" / f"{slug}.json").write_text(json.dumps(proof), encoding="utf-8")

    def errors(self):
        return "\n".join(check.validate(self.root).errors)

    def remove_sources(self):
        for record in self.records:
            (self.root / record["path"]).unlink()

    def test_original_bytes_names_and_shared_layout_are_accepted(self):
        before = {r["path"]: (self.root / r["path"]).read_bytes() for r in self.records}
        self.assertEqual(self.errors(), "")
        self.assertEqual(check.validate(self.root, expected_count=2).errors, [])
        self.assertIn("expected 43", "\n".join(check.validate(self.root, expected_count=43).errors))
        self.assertEqual(before, {p: (self.root / p).read_bytes() for p in before})

    def test_duplicate_registry_ids_are_rejected_but_duplicate_names_are_not(self):
        self.entries[1]["slug"] = self.entries[0]["slug"]
        self.save()
        self.assertIn("duplicate registry ID", self.errors())

    def test_catalog_and_manifest_path_traversal_are_rejected(self):
        for unsafe in ("../outside", "/absolute", "C:/escape", "skills/../../escape", "skills\\escape", "skills/.. /escape"):
            with self.subTest(path=unsafe):
                with self.assertRaises(check.ValidationError):
                    check.confined_path(self.root, unsafe)
        self.records[0]["path"] = "skills/../outside"
        self.save()
        self.assertIn("normalized and confined", self.errors())

    def test_source_path_cannot_escape_pinned_repository(self):
        self.records[0]["source"]["path"] = "../../other"
        self.save()
        self.assertIn("normalized and confined", self.errors())

    def test_same_size_source_edit_is_detected_by_sha256(self):
        target = self.root / self.records[0]["path"]
        target.write_bytes(target.read_bytes().replace(b"unchanged", b"tampered!", 1))
        self.assertIn("SHA-256", self.errors())

    def test_git_blob_identity_is_checked_independently(self):
        self.records[0]["source"]["blob_sha1"] = "0" * 40
        self.save()
        self.assertIn("Git blob SHA-1", self.errors())

    def test_frontmatter_name_is_checked_even_when_hashes_match(self):
        record = self.records[0]
        target = self.root / record["path"]
        data = target.read_bytes().replace(b"Original Name", b"Different Name")
        target.write_bytes(data)
        record.update(size=len(data), sha256=hashlib.sha256(data).hexdigest())
        record["source"]["blob_sha1"] = check.git_blob_sha1(data)
        self.proofs[self.entries[0]["slug"]]["primary_sha256"] = record["sha256"]
        self.save()
        self.assertIn("frontmatter name differs", self.errors())

    def test_untracked_files_and_undeclared_skill_files_fail(self):
        self.add_file("skills/example/repo/surprise/SKILL.md", "surprise/SKILL.md", b"---\nname: surprise\n---\n")
        self.assertIn("not tracked", self.errors())
        self.save()
        self.assertIn("SKILL.md completeness differs", self.errors())

    def test_license_copy_is_required_and_bound_to_its_actual_source(self):
        license_record = self.records.pop(1)
        (self.root / license_record["path"]).unlink()
        self.save()
        self.assertIn("required manifest file absent", self.errors())
        self.records.append(license_record)
        (self.root / license_record["path"]).write_bytes(self.contents[vendor.raw_url(license_record)])
        self.proofs[self.entries[0]["slug"]]["license"]["source_url"] = f"https://github.com/example/repo/blob/{PIN}/other/LICENSE"
        self.save()
        self.assertIn("license source URL differs", self.errors())

    def test_sidecar_identity_licensing_attribution_and_evidence_are_checked(self):
        slug = self.entries[0]["slug"]
        original = json.loads(json.dumps(self.proofs[slug]))
        cases = [
            (lambda p: p["source"].update(commit="2" * 40), "provenance source differs"),
            (lambda p: p["license"].update(spdx="Apache-2.0"), "license identity differs"),
            (lambda p: p.update(author=" "), "author attribution"),
            (lambda p: p.update(status="conditional"), "provenance status differs"),
            (lambda p: p.update(evidence_ids=["missing"]), "unresolved evidence"),
            (lambda p: p.update(primary_sha256="0" * 64), "primary_sha256 differs"),
        ]
        for mutate, message in cases:
            with self.subTest(message=message):
                self.proofs[slug] = json.loads(json.dumps(original))
                mutate(self.proofs[slug])
                self.save()
                self.assertIn(message, self.errors())

    def test_manifest_source_pin_must_equal_catalog_pin(self):
        self.records[0]["source"]["commit"] = "2" * 40
        self.save()
        self.assertIn("source commit does not match", self.errors())

    def test_symlink_source_is_rejected(self):
        link = self.root / "skills" / "linked"
        try:
            link.symlink_to(self.root / "provenance", target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("host cannot create symlinks")
        self.assertIn("symlink/reparse", self.errors())

    @unittest.skipIf(os.name == "nt", "Windows executable bits are checked in Git index")
    def test_optional_posix_executable_mode_check(self):
        target = self.root / self.records[0]["path"]
        target.chmod(0o755)
        self.assertIn("executable mode", "\n".join(check.validate(self.root, strict_modes=True).errors))

    def test_replay_restores_exact_crlf_binary_and_license_bytes_at_pinned_urls(self):
        self.remove_sources()
        requested = []
        def fetch(url):
            requested.append(url)
            self.assertIn(f"/{PIN}/", url)
            self.assertNotIn("HEAD", url)
            return self.contents[url]
        count = vendor.fetch_missing(self.root, fetcher=fetch)
        self.assertEqual(count, len(self.records))
        self.assertEqual(self.errors(), "")
        self.assertEqual(len(requested), len(set(requested)))  # identical license source fetched once
        for record in self.records:
            self.assertEqual((self.root / record["path"]).read_bytes(), self.contents[vendor.raw_url(record)])

    def test_replay_rejects_all_bad_downloads_before_first_source_write(self):
        self.remove_sources()
        def fetch(url):
            return b"bad data" if url.endswith("SKILL.md") else self.contents[url]
        with self.assertRaises(check.ValidationError):
            vendor.fetch_missing(self.root, fetcher=fetch)
        self.assertTrue(all(not (self.root / r["path"]).exists() for r in self.records))

    def test_replay_fails_dirty_existing_file_before_network_and_never_overwrites(self):
        target = self.root / self.records[0]["path"]
        target.write_bytes(b"my local edits")
        with patch.object(vendor, "download", side_effect=AssertionError("network should not run")) as get:
            with self.assertRaises(check.ValidationError):
                vendor.fetch_missing(self.root, fetcher=get)
        self.assertEqual(target.read_bytes(), b"my local edits")

    def test_atomic_publication_refuses_concurrent_existing_file(self):
        target = self.root / self.records[0]["path"]
        old = target.read_bytes()
        with self.assertRaises(FileExistsError):
            vendor._publish_missing(self.root, self.records[0]["path"], b"replacement", "100644")
        self.assertEqual(target.read_bytes(), old)
        self.assertEqual(list(target.parent.glob(".vendor-*")), [])


if __name__ == "__main__":
    unittest.main()
