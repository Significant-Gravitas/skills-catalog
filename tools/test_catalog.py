"""Offline regression tests for flat packages, retained originals and safe replay."""
from __future__ import annotations

import copy
import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path

import yaml

import check
import package
import vendor

PIN = "1" * 40


class CatalogTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="catalog-test-", dir=Path(__file__).parent)
        self.root = Path(self.temporary.name).resolve()
        self.assertEqual(self.root.parent, Path(__file__).resolve().parent)
        self.addCleanup(self.temporary.cleanup)
        self.entries, self.records, self.proofs = [], [], {}
        for slug, upstream in (("first-skill", "skills/one"), ("second-skill", "skills/two")):
            entry = dict(slug=slug, source=f"example/repo/{upstream}", license="MIT", categories=["operations"], required_providers=[])
            self.entries.append(entry)
            url = f"https://github.com/example/repo/blob/{PIN}/{upstream}/SKILL.md"
            original = b'---\r\nname: "Original Name"\r\ndescription: Source description.\r\nuser-invocable: false\r\nmetadata:\r\n  version: 2\r\n---\r\nRead [guide](../shared/guide.md).\r\nKeep this authored procedure.\r\n'
            transformations = [
                dict(kind="replace", old="../shared/guide.md", new="references/guide.md", expected_count=1, reason="Relocate the required reference into the package."),
                dict(kind="frontmatter", updates=dict(name=slug, license="MIT", metadata=dict(author="Example contributors", source=entry["source"], source_url=url)), reason="Record original attribution and unique installed name."),
                dict(kind="notice", text="> Packaging notice: metadata and reference path adapted; original retained.", reason="Disclose the recorded changes."),
            ]
            primary = self.add_file(f"skills/{slug}/SKILL.md", f"{upstream}/SKILL.md", original, role="skill", transformations=transformations)
            self.add_file(f"skills/{slug}/LICENSE", "LICENSE", b"Copyright Example\r\nMIT license fixture\r\n", role="license")
            self.add_file(f"skills/{slug}/references/guide.md", "shared/guide.md", b"Read-only reference.\r\n")
            self.add_file(f"skills/{slug}/assets/example.bin", f"{upstream}/assets/example.bin", b"\x00\xff\r\n")
            self.add_generated(f"skills/{slug}/ATTRIBUTION.md", "Example contributors; fixture provenance.\n")
            self.proofs[slug] = dict(schema_version=3, slug=slug, name=slug, original_name="Original Name", source=dict(repo="example/repo", commit=PIN, path=upstream), source_url=url, author="Example contributors", license=dict(spdx="MIT", file=f"skills/{slug}/LICENSE", source_url=f"https://github.com/example/repo/blob/{PIN}/LICENSE"), status="core", primary_sha256=primary["source"]["sha256"], packaged_sha256=primary["sha256"], source_modified=True, packaging=dict(notes="Fixture recorded changes."), evidence_ids=["observed-installs"])
        self.save()

    def add_file(self, path, source_path, data, *, role="support", mode="100644", transformations=None):
        digest = hashlib.sha256(data).hexdigest()
        source = dict(repo="example/repo", commit=PIN, path=source_path, blob_sha1=check.git_blob_sha1(data), sha256=digest, size=len(data), archive="provenance/originals/" + digest)
        archive = self.root / source["archive"]
        archive.parent.mkdir(parents=True, exist_ok=True)
        archive.write_bytes(data)
        record = dict(path=path, source=source, mode=mode, role=role, transformations=transformations or [], reason="Required fixture package member.")
        self.records.append(record)
        self.render(record)
        return record

    def add_generated(self, path, content):
        record = dict(path=path, source=None, role="attribution", mode="100644", transformations=[], content=content, reason="Redistribution attribution.")
        self.records.append(record)
        self.render(record)
        return record

    def render(self, record):
        data = package.render_file(record, self.root)
        record.update(sha256=hashlib.sha256(data).hexdigest(), size=len(data))
        destination = self.root / record["path"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
        if os.name != "nt":
            destination.chmod(0o755 if record["mode"] == "100755" else 0o644)
        return data

    def save(self):
        (self.root / "catalog.yml").write_text(yaml.safe_dump(dict(skills=self.entries)), encoding="utf-8")
        provenance = self.root / "provenance"
        (provenance / "skills").mkdir(parents=True, exist_ok=True)
        (provenance / "files.json").write_text(json.dumps(dict(schema_version=3, files=self.records)), encoding="utf-8")
        (provenance / "evidence.json").write_text(json.dumps(dict(schema_version=2, observations=[dict(id="observed-installs", value=42)])), encoding="utf-8")
        for slug, proof in self.proofs.items():
            (provenance / "skills" / f"{slug}.json").write_text(json.dumps(proof), encoding="utf-8")

    def errors(self):
        return "\n".join(check.validate(self.root).errors)

    def remove_outputs(self):
        for record in self.records:
            (self.root / record["path"]).unlink()

    def test_packages_have_unique_names_preserving_duplicate_upstream_names(self):
        before = {r["path"]: (self.root / r["path"]).read_bytes() for r in self.records}
        self.assertEqual(self.errors(), "")
        self.assertEqual(check.validate(self.root, expected_count=2).errors, [])
        self.assertIn("expected 43", "\n".join(check.validate(self.root, expected_count=43).errors))
        self.assertEqual(before, {p: (self.root / p).read_bytes() for p in before})
        metadata, body = check.frontmatter(before[self.records[0]["path"]], "test")
        self.assertIs(metadata["user-invocable"], False)
        self.assertEqual(metadata["metadata"]["version"], "2")
        self.assertIn("Keep this authored procedure.", body)

    def test_duplicate_registry_ids_are_rejected(self):
        self.entries[1]["slug"] = self.entries[0]["slug"]
        self.save()
        self.assertIn("duplicate registry ID", self.errors())

    def test_traversal_and_windows_ambiguous_paths_are_rejected(self):
        for unsafe in ("../outside", "/absolute", "C:/escape", "skills/../../escape", "skills\\escape", "skills/.. /escape"):
            with self.subTest(path=unsafe), self.assertRaises(check.ValidationError):
                check.confined_path(self.root, unsafe)
        self.records[0]["path"] = "skills/../outside"
        self.save()
        self.assertIn("normalized and confined", self.errors())

    def test_source_path_cannot_escape_pinned_repository(self):
        self.records[0]["source"]["path"] = "../../other"
        self.save()
        self.assertIn("normalized and confined", self.errors())

    def test_same_size_output_edit_is_detected(self):
        target = self.root / self.records[0]["path"]
        target.write_bytes(target.read_bytes().replace(b"authored", b"tampered", 1))
        self.assertIn("SHA-256", self.errors())

    def test_original_sha256_and_git_blob_are_independently_verified(self):
        record = self.records[0]
        record["source"]["blob_sha1"] = "0" * 40
        self.save()
        self.assertIn("original Git blob SHA-1", self.errors())
        original = self.root / record["source"]["archive"]
        original.write_bytes(original.read_bytes().replace(b"authored", b"tampered"))
        self.assertIn("SHA-256", self.errors())

    def test_frontmatter_name_mismatch_fails_even_with_consistent_hashes(self):
        record = self.records[0]
        record["transformations"][1]["updates"]["name"] = "unregistered-name"
        self.render(record)
        self.proofs["first-skill"]["packaged_sha256"] = record["sha256"]
        self.save()
        self.assertIn("frontmatter name differs", self.errors())

    def test_untracked_outputs_and_unselected_skill_roots_fail(self):
        path = self.root / "skills/first-skill/surprise.md"
        path.write_text("not declared", encoding="utf-8")
        self.assertIn("not tracked", self.errors())
        path.unlink()
        self.add_file("skills/first-skill/nested/SKILL.md", "examples/SKILL.md", b"example")
        self.save()
        self.assertIn("additional SKILL.md", self.errors())

    def test_license_is_required_unchanged_and_bound_to_source(self):
        license_record = self.records.pop(1)
        (self.root / license_record["path"]).unlink()
        self.save()
        self.assertIn("required manifest file absent", self.errors())
        self.records.append(license_record)
        self.render(license_record)
        self.proofs["first-skill"]["license"]["source_url"] = f"https://github.com/example/repo/blob/{PIN}/other/LICENSE"
        self.save()
        self.assertIn("license source URL differs", self.errors())
        license_record["transformations"] = [dict(kind="notice", text="changed", reason="fixture")]
        self.save()
        self.assertIn("license bytes may not be transformed", self.errors())

    def test_sidecar_identity_license_author_evidence_and_both_hashes_are_bound(self):
        original = copy.deepcopy(self.proofs["first-skill"])
        cases = [
            (lambda p: p["source"].update(commit="2" * 40), "source commit/repo does not match"),
            (lambda p: p["license"].update(spdx="Apache-2.0"), "license identity differs"),
            (lambda p: p.update(author=" "), "author attribution"),
            (lambda p: p.update(status="unknown"), "status must be"),
            (lambda p: p.update(evidence_ids=["missing"]), "unresolved evidence"),
            (lambda p: p.update(primary_sha256="0" * 64), "primary_sha256 or packaged_sha256 differs"),
            (lambda p: p.update(packaged_sha256="0" * 64), "primary_sha256 or packaged_sha256 differs"),
            (lambda p: p.update(original_name="Incorrect"), "original_name differs"),
            (lambda p: p.update(source_modified=False), "source_modified differs"),
        ]
        for mutate, message in cases:
            with self.subTest(message=message):
                self.proofs["first-skill"] = copy.deepcopy(original)
                mutate(self.proofs["first-skill"])
                self.save()
                self.assertIn(message, self.errors())

    def test_manifest_source_pin_must_equal_skill_provenance(self):
        self.records[0]["source"]["commit"] = "2" * 40
        self.save()
        self.assertIn("source commit/repo does not match", self.errors())

    def test_symlinks_are_rejected(self):
        link = self.root / "skills/linked"
        try:
            link.symlink_to(self.root / "provenance", target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("host cannot create symlinks")
        self.assertIn("symlink/reparse", self.errors())

    @unittest.skipIf(os.name == "nt", "Windows executable bits are checked in Git index")
    def test_strict_posix_executable_mode_check(self):
        target = self.root / self.records[0]["path"]
        target.chmod(0o755)
        self.assertIn("executable mode", "\n".join(check.validate(self.root, strict_modes=True).errors))

    def test_restore_replays_adaptations_and_preserves_crlf_binary_licenses(self):
        expected = {r["path"]: (self.root / r["path"]).read_bytes() for r in self.records}
        originals = {r["source"]["archive"]: (self.root / r["source"]["archive"]).read_bytes() for r in self.records if r["source"]}
        self.remove_outputs()
        self.assertEqual(vendor.restore_missing(self.root), len(self.records))
        self.assertEqual(self.errors(), "")
        for path, data in {**expected, **originals}.items():
            self.assertEqual((self.root / path).read_bytes(), data)
        self.assertEqual(vendor.restore_missing(self.root), 0)

    def test_bad_original_prevents_all_output_writes(self):
        self.remove_outputs()
        (self.root / self.records[0]["source"]["archive"]).write_bytes(b"bad original")
        with self.assertRaises(check.ValidationError):
            vendor.restore_missing(self.root)
        self.assertTrue(all(not (self.root / r["path"]).exists() for r in self.records))

    def test_restore_never_overwrites_dirty_existing_output(self):
        target = self.root / self.records[0]["path"]
        target.write_bytes(b"my local edits")
        (self.root / self.records[1]["path"]).unlink()
        with self.assertRaises(check.ValidationError):
            vendor.restore_missing(self.root)
        self.assertEqual(target.read_bytes(), b"my local edits")
        self.assertFalse((self.root / self.records[1]["path"]).exists())

    def test_atomic_publication_refuses_concurrent_existing_file(self):
        target = self.root / self.records[0]["path"]
        old = target.read_bytes()
        with self.assertRaises(FileExistsError):
            vendor._publish_missing(self.root, self.records[0]["path"], b"replacement", "100644")
        self.assertEqual(target.read_bytes(), old)
        self.assertEqual(list(target.parent.glob(".vendor-*")), [])

    def test_unknown_missing_or_excess_originals_are_rejected(self):
        path = self.root / "provenance/originals" / ("0" * 64)
        path.write_bytes(b"unreferenced")
        self.assertIn("archive inventory differs", self.errors())
        path.unlink()
        (self.root / self.records[0]["source"]["archive"]).unlink()
        self.assertIn("archive inventory differs", self.errors())

    def test_undeclared_or_miscounted_transforms_are_rejected(self):
        record = self.records[0]
        record["transformations"][0]["expected_count"] = 2
        self.save()
        self.assertIn("replacement count changed", self.errors())
        record["transformations"][0]["kind"] = "execute"
        self.save()
        self.assertIn("unknown transformation kind", self.errors())
        record["transformations"] = [dict(kind="frontmatter", updates=dict(description="Replacement instructions"), reason="Not permitted in this curation.")]
        self.save()
        self.assertIn("frontmatter changes may only", self.errors())

    def test_text_replacement_cannot_silently_change_original_frontmatter_fields(self):
        record = self.records[0]
        record["transformations"].insert(0, dict(kind="replace", old="Source description.", new="Different task.", expected_count=1, reason="This fixture edit is deliberately outside permitted metadata changes."))
        self.render(record)
        self.proofs["first-skill"]["packaged_sha256"] = record["sha256"]
        self.save()
        self.assertIn("original frontmatter fields changed", self.errors())

    def test_allowed_tools_changes_cannot_add_capabilities(self):
        record = self.records[0]
        record["transformations"][1]["updates"]["allowed-tools"] = "WebFetch"
        self.render(record)
        self.proofs["first-skill"]["packaged_sha256"] = record["sha256"]
        self.save()
        self.assertIn("allowed-tools may change only", self.errors())

    def test_hidden_or_deep_package_members_are_rejected(self):
        original = self.records[2]["path"]
        for relative in (".hidden", "reference with spaces.md", "/".join(["dir"] * 8 + ["file.txt"])):
            with self.subTest(path=relative):
                self.records[2]["path"] = "skills/first-skill/" + relative
                self.save()
                self.assertIn("unsafe package segment or path depth", self.errors())
        self.records[2]["path"] = original

    def test_sibling_count_limit_includes_license_and_attribution_not_root(self):
        # Four siblings already exist. 96 more reaches exactly 100.
        for n in range(96):
            self.add_file(f"skills/first-skill/references/file-{n}.txt", f"refs/file-{n}.txt", b"Reference.")
        self.save()
        self.assertEqual(self.errors(), "")
        self.add_file("skills/first-skill/references/overflow.txt", "refs/overflow.txt", b"Reference.")
        self.save()
        self.assertIn("exceeds 100 sibling files", self.errors())

    def test_per_file_byte_limit_boundary(self):
        record = self.add_file("skills/first-skill/assets/large.bin", "large.bin", b"x" * (2 * 1024 * 1024))
        self.save()
        self.assertEqual(self.errors(), "")
        # An independently replayable larger original exceeds the actual cap.
        self.records.remove(record)
        (self.root / record["source"]["archive"]).unlink()
        self.add_file(record["path"], "large.bin", b"x" * (2 * 1024 * 1024 + 1))
        self.save()
        self.assertIn("package file exceeds 2 MiB", self.errors())

    def test_total_package_limit_includes_root_and_all_siblings(self):
        # Ten allowed 2 MiB siblings consume the total cap by themselves;
        # SKILL.md, LICENSE and existing resources must make the package fail.
        for n in range(10):
            self.add_file(f"skills/first-skill/assets/large-{n}.bin", f"large-{n}.bin", b"x" * (2 * 1024 * 1024))
        self.save()
        self.assertIn("package exceeds 20 MiB", self.errors())

    def test_description_body_and_trigger_caps_are_checked_independently(self):
        entry, proof = self.entries[0], self.proofs["first-skill"]
        meta, body = check.frontmatter((self.root / self.records[0]["path"]).read_bytes(), "test")
        for changes, text, message in ((dict(description="x" * 1025), body, "description"), ({}, "x" * 50001, "body"), (dict(triggers=[str(i) for i in range(11)]), body, "triggers"), (dict(triggers=["x" * 65]), body, "triggers")):
            content = ("---\n" + yaml.safe_dump({**meta, **changes}) + "---\n" + text).encode()
            with self.subTest(field=message), self.assertRaisesRegex(check.ValidationError, message):
                check._skill_content(content, entry, proof)


if __name__ == "__main__":
    unittest.main()
