"""PR 2 preservation regression checks; never execute skill contents."""
from __future__ import annotations

import copy
import hashlib
import json
import unittest

import check
import test_catalog as fixtures
import vendor


class CarryforwardTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.CatalogTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        fixture = self.fixture
        self.root = fixture.root
        # Give the pending same-name proposal normal, fully checked import
        # provenance. Its installed bytes intentionally differ from PR 2.
        slug = check.PR2_PENDING_SLUG
        entry = copy.deepcopy(fixture.entries[0])
        entry["slug"] = slug
        fixture.entries.append(entry)
        proof = copy.deepcopy(fixture.proofs["first-skill"])
        proof.update(slug=slug, name=slug)
        proof["license"]["file"] = f"skills/{slug}/LICENSE"
        for original in list(fixture.records):
            if not original["path"].startswith("skills/first-skill/"):
                continue
            record = copy.deepcopy(original)
            record["path"] = record["path"].replace("skills/first-skill/", f"skills/{slug}/", 1)
            for transform in record["transformations"]:
                if transform["kind"] == "frontmatter":
                    transform["updates"]["name"] = slug
            fixture.records.append(record)
            fixture.render(record)
            if record["role"] == "skill":
                proof["packaged_sha256"] = record["sha256"]
        fixture.proofs[slug] = proof
        self.manifest = dict(schema_version=1, source=copy.deepcopy(check.PR2_SOURCE),
                             added_slugs=[], retained=[], unresolved=[])
        for n in range(167):
            name = f"pr2-skill-{n:03d}" if n < 166 else slug
            metadata = dict(slug=name, source="platform", categories=["operations"], required_providers=[])
            content = f"---\nname: {name}\ndescription: Existing PR 2 skill.\n---\nKeep these existing instructions.\n".encode()
            path = f"skills/{name}/SKILL.md"
            record = dict(path=path, mode="100644", size=len(content),
                          sha256=hashlib.sha256(content).hexdigest(), blob_sha1=check.git_blob_sha1(content))
            row = dict(slug=name, catalog_entry=metadata, files=[record])
            self.manifest["added_slugs"].append(name)
            if n < 166:
                self.manifest["retained"].append(row)
                fixture.entries.append(copy.deepcopy(metadata))
                destination = self.root / path
                destination.parent.mkdir(parents=True)
                destination.write_bytes(content)
            else:
                row["reason"] = "Exact-name choice is pending; imported package remains the proposal."
                self.manifest["unresolved"].append(row)
        self.save()

    def save(self):
        self.fixture.save()
        (self.root / "provenance/pr2-carryforward.json").write_text(json.dumps(self.manifest), encoding="utf-8")

    def errors(self):
        return "\n".join(check.validate(self.root).errors)

    def test_retains_original_platform_bytes_without_inventing_upstream_licenses(self):
        result = check.validate(self.root, expected_count=169)
        self.assertEqual(result.errors, [])
        self.assertEqual(len(result.provenance), 3)
        self.assertEqual(len(result.carryforward), 166)
        self.assertEqual(result.unresolved, {check.PR2_PENDING_SLUG})
        self.assertFalse((self.root / "skills/pr2-skill-000/LICENSE").exists())
        self.assertFalse((self.root / "provenance/skills/pr2-skill-000.json").exists())

    def test_protected_file_cannot_be_edited_or_deleted(self):
        path = self.root / "skills/pr2-skill-000/SKILL.md"
        path.write_bytes(path.read_bytes().replace(b"Keep", b"Lose"))
        self.assertIn("SHA-256 differs", self.errors())
        path.unlink()
        self.assertIn("protected PR 2 file", self.errors())
        with self.assertRaises(check.ValidationError):
            vendor.restore_missing(self.root)
        self.assertFalse(path.exists())

    def test_catalog_metadata_and_membership_are_protected(self):
        entry = next(e for e in self.fixture.entries if e["slug"] == "pr2-skill-000")
        entry["required_providers"] = ["unexpected-provider"]
        self.save()
        self.assertIn("catalog metadata differs", self.errors())
        self.fixture.entries.remove(entry)
        self.save()
        self.assertIn("protected PR 2 catalog entries are missing", self.errors())

    def test_original_source_pin_and_complete_added_inventory_cannot_silently_change(self):
        self.manifest["source"]["commit"] = "0" * 40
        self.save()
        self.assertIn("immutable PR 2 source identity differs", self.errors())
        self.manifest["source"] = copy.deepcopy(check.PR2_SOURCE)
        self.manifest["added_slugs"].pop(0)
        self.manifest["retained"].pop(0)
        self.save()
        self.assertIn("all 167 added slugs", self.errors())

    def test_only_explicit_pending_name_exception_is_allowed(self):
        self.manifest["unresolved"][0]["slug"] = "some-other-decision"
        self.manifest["unresolved"][0]["catalog_entry"]["slug"] = "some-other-decision"
        self.save()
        self.assertIn("only product-experiment-design", self.errors())

    def test_pending_proposal_still_requires_full_import_provenance(self):
        proof = self.fixture.proofs[check.PR2_PENDING_SLUG]
        proof["license"]["spdx"] = "invented-license"
        self.save()
        self.assertIn("per-skill license identity differs", self.errors())

    def test_extra_protected_package_file_is_rejected(self):
        (self.root / "skills/pr2-skill-000/extra.py").write_text("do_not_execute()", encoding="utf-8")
        self.assertIn("not tracked", self.errors())


if __name__ == "__main__":
    unittest.main()
