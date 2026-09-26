"""Release integrity and reference tests; no external accounts are used."""

import copy
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

import release


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.git("init", "--quiet")
        self.git("config", "core.autocrlf", "false")
        (self.root / "catalog.yml").write_text(
            "skills:\n  - slug: example\n    categories: [operations]\n    source: platform\n",
            encoding="utf-8", newline="\n",
        )
        package = self.root / "skills/example"
        package.mkdir(parents=True)
        (package / "SKILL.md").write_text(
            "---\nname: example\ndescription: An example\n---\nInstructions.\n",
            encoding="utf-8", newline="\n",
        )
        (package / "support.txt").write_bytes(b"preserve all bytes\n")
        (self.root / "experts").mkdir()
        self.write_expert("alex", ["example"])
        self.git("add", ".")
        catalog_hash, packages = release.inventory(self.root)
        experts = release.expert_inventory(self.root, {p["slug"] for p in packages})
        self.manifest = {
            "schema_version": 2,
            "release_key": "test-release",
            "provenance": {"source": "test"},
            "catalog_sha256": catalog_hash,
            "packages": packages,
            "experts": experts,
            "retirements": [],
            "retired_experts": [],
            "system_packages": [],
        }

    def write_expert(self, key, skills, name=None):
        lines = [f"key: {key}", f"name: {name or key.title()}", "skills:"]
        lines += [f"- {slug}" for slug in skills]
        (self.root / "experts" / f"{key}.yml").write_text(
            "\n".join(lines) + "\n", encoding="utf-8", newline="\n",
        )

    def git(self, *args):
        return subprocess.run(
            ["git", "-C", str(self.root), *args], check=True, capture_output=True
        ).stdout

    def test_complete_folder_passes(self):
        release.check(self.root, self.manifest)
        self.assertEqual(2, len(self.manifest["packages"][0]["files"]))

    def test_supporting_file_edit_fails(self):
        (self.root / "skills/example/support.txt").write_bytes(b"changed\n")
        with self.assertRaisesRegex(release.ReleaseError, "package bytes"):
            release.check(self.root, self.manifest)

    def test_line_ending_conversion_fails(self):
        path = self.root / "skills/example/SKILL.md"
        path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n"))
        with self.assertRaisesRegex(release.ReleaseError, "package bytes"):
            release.check(self.root, self.manifest)

    def test_metadata_edit_fails(self):
        path = self.root / "catalog.yml"
        path.write_bytes(path.read_bytes().replace(b"operations", b"sales"))
        with self.assertRaisesRegex(release.ReleaseError, "catalog.yml hash mismatch"):
            release.check(self.root, self.manifest)

    def test_missing_supporting_file_fails(self):
        (self.root / "skills/example/support.txt").unlink()
        with self.assertRaisesRegex(release.ReleaseError, "package bytes"):
            release.check(self.root, self.manifest)

    def test_untracked_file_is_not_silently_omitted(self):
        (self.root / "skills/example/extra.txt").write_bytes(b"extra")
        with self.assertRaisesRegex(release.ReleaseError, "stage regular files"):
            release.check(self.root, self.manifest)

    def test_extra_directory_fails(self):
        (self.root / "skills/unlisted").mkdir()
        with self.assertRaisesRegex(release.ReleaseError, "directories must equal"):
            release.check(self.root, self.manifest)

    def test_executable_bit_changes_tree_hash(self):
        before = self.manifest["packages"][0]["tree_sha256"]
        self.git("update-index", "--chmod=+x", "skills/example/support.txt")
        _, after = release.inventory(self.root)
        self.assertNotEqual(before, after[0]["tree_sha256"])
        self.assertTrue(after[0]["files"][1]["executable"])
        with self.assertRaisesRegex(release.ReleaseError, "package bytes"):
            release.check(self.root, self.manifest)

    def test_canonical_hash_is_independent_of_object_key_order(self):
        files = self.manifest["packages"][0]["files"]
        reordered = [{"sha256": f["sha256"], "executable": f["executable"], "path": f["path"]} for f in files]
        self.assertEqual(release.canonical_json(files), release.canonical_json(reordered))

    def test_duplicate_package_fails(self):
        self.manifest["packages"].append(copy.deepcopy(self.manifest["packages"][0]))
        with self.assertRaisesRegex(release.ReleaseError, "duplicate package"):
            release.validate_manifest(self.manifest)

    def test_unknown_assigned_skill_fails(self):
        self.manifest["experts"][0]["skills"].append("missing")
        with self.assertRaisesRegex(release.ReleaseError, "assigned skill missing"):
            release.validate_manifest(self.manifest)

    def test_duplicate_assignment_fails(self):
        self.manifest["experts"][0]["skills"].append("example")
        with self.assertRaisesRegex(release.ReleaseError, "duplicate skill assignment"):
            release.validate_manifest(self.manifest)

    def test_duplicate_expert_key_fails(self):
        self.manifest["experts"].append(copy.deepcopy(self.manifest["experts"][0]))
        with self.assertRaisesRegex(release.ReleaseError, "duplicate expert key"):
            release.validate_manifest(self.manifest)

    def test_active_skill_retirement_fails(self):
        self.manifest["retirements"] = ["example"]
        with self.assertRaisesRegex(release.ReleaseError, "active package cannot be retired"):
            release.validate_manifest(self.manifest)

    def test_explicit_unassigned_retirement_is_valid(self):
        self.manifest["retirements"] = ["old-skill"]
        release.validate_manifest(self.manifest)

    def test_path_traversal_fails(self):
        self.manifest["packages"][0]["files"][0]["path"] = "../outside.md"
        with self.assertRaisesRegex(release.ReleaseError, "invalid file path"):
            release.validate_manifest(self.manifest)

    def test_system_packages_fail_until_supported(self):
        self.manifest["system_packages"] = [{"key": "guide"}]
        with self.assertRaisesRegex(release.ReleaseError, "supported schema extension"):
            release.validate_manifest(self.manifest)

    def test_unknown_fields_fail(self):
        self.manifest["experts"][0]["ownerUserId"] = "must-not-be-used"
        with self.assertRaisesRegex(release.ReleaseError, "exactly"):
            release.validate_manifest(self.manifest)

    def test_expert_entry_carries_file_hash_and_skills(self):
        expert = self.manifest["experts"][0]
        self.assertEqual({"key", "sha256", "skills"}, set(expert))
        self.assertEqual(["example"], expert["skills"])
        data = (self.root / "experts/alex.yml").read_bytes()
        self.assertEqual(release.sha256(data), expert["sha256"])

    def test_edited_expert_file_fails(self):
        path = self.root / "experts/alex.yml"
        path.write_bytes(path.read_bytes().replace(b"name: Alex", b"name: Alexandra"))
        with self.assertRaisesRegex(release.ReleaseError, "expert file bytes differ"):
            release.check(self.root, self.manifest)

    def test_unlisted_expert_file_fails(self):
        self.write_expert("blake", ["example"])
        with self.assertRaisesRegex(release.ReleaseError, "not listed in release.json: blake"):
            release.check(self.root, self.manifest)

    def test_listed_expert_without_file_fails(self):
        (self.root / "experts/alex.yml").unlink()
        with self.assertRaisesRegex(release.ReleaseError, "have no file: alex"):
            release.check(self.root, self.manifest)

    def test_manifest_skills_differing_from_yaml_fail(self):
        self.manifest["experts"][0]["skills"] = []
        with self.assertRaisesRegex(release.ReleaseError, "skills differ from experts/alex.yml"):
            release.check(self.root, self.manifest)

    def test_expert_key_must_match_file_name(self):
        path = self.root / "experts/alex.yml"
        path.write_bytes(path.read_bytes().replace(b"key: alex", b"key: alexa"))
        with self.assertRaisesRegex(release.ReleaseError, "key must equal the file name"):
            release.check(self.root, self.manifest)

    def test_expert_bundling_unknown_slug_fails(self):
        self.write_expert("alex", ["example", "missing"])
        with self.assertRaisesRegex(release.ReleaseError, "not an active package: missing"):
            release.check(self.root, self.manifest)

    def test_retired_expert_overlapping_experts_fails(self):
        self.manifest["retired_experts"] = ["alex"]
        with self.assertRaisesRegex(release.ReleaseError, "active expert cannot be retired"):
            release.validate_manifest(self.manifest)

    def test_retired_experts_must_be_sorted(self):
        self.manifest["retired_experts"] = ["zed", "blake"]
        with self.assertRaisesRegex(release.ReleaseError, "retired_experts must be sorted"):
            release.validate_manifest(self.manifest)

    def test_explicit_retired_expert_is_valid(self):
        self.manifest["retired_experts"] = ["blake"]
        release.check(self.root, self.manifest)

    def test_unknown_top_level_key_fails(self):
        self.manifest["environment"] = "production"
        with self.assertRaisesRegex(release.ReleaseError, "release must have exactly"):
            release.validate_manifest(self.manifest)

    def test_schema_version_1_fails(self):
        self.manifest["schema_version"] = 1
        with self.assertRaisesRegex(release.ReleaseError, "unsupported schema_version"):
            release.validate_manifest(self.manifest)

    def test_invalid_expert_hash_fails(self):
        self.manifest["experts"][0]["sha256"] = "not-a-hash"
        with self.assertRaisesRegex(release.ReleaseError, "invalid alex expert hash"):
            release.validate_manifest(self.manifest)

    def test_refresh_regenerates_experts_and_keeps_authored_fields(self):
        self.write_expert("alex", ["example"], name="Alexandra")
        self.manifest["retired_experts"] = ["blake"]
        refreshed = release.refreshed(self.root, self.manifest)
        self.assertEqual(list(release.TOP_LEVEL_KEYS), list(refreshed))
        self.assertEqual(["blake"], refreshed["retired_experts"])
        self.assertEqual("test-release", refreshed["release_key"])
        self.assertNotEqual(self.manifest["experts"][0]["sha256"], refreshed["experts"][0]["sha256"])
        release.check(self.root, refreshed)

    @unittest.skipIf(os.name == "nt", "Windows symlink creation needs separate OS permission")
    def test_symlink_fails(self):
        path = self.root / "skills/example/support.txt"
        path.unlink()
        path.symlink_to(self.root / "catalog.yml")
        with self.assertRaisesRegex(release.ReleaseError, "symlink"):
            release.inventory(self.root)


if __name__ == "__main__":
    unittest.main()
