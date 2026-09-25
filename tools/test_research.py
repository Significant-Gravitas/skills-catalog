"""Mutation tests for omissions, attribution evidence and deferred source integrity."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import check_research

PIN = "1" * 40
ACTIVE = "example/sales:skills/research"
OTHER_ACTIVE = "example/sales:skills/writing"
DEFERRED = "example/native:ads"
NOTICE_REPO = "Knowatoa/ai-visibility-skills"
NOTICE_PIN = "29f9cd57e976527b1f136bec27af5fc06364690c"
NOTICE_URL = f"https://github.com/{NOTICE_REPO}/blob/{NOTICE_PIN}/LICENSE"


class ResearchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="research-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.roster = {"commit": PIN, "expected_experts": 32, "expected_assignments": 321, "experts": []}
        self.coverage = {"schema_version": 1, "experts": []}
        for number in range(32):
            name = f"Expert {number}"
            slugs = [f"expert-{number}-skill-{i}" for i in range(11 if number == 31 else 10)]
            self.roster["experts"].append({"name": name, "job_title": "Researcher", "bundled_skills": slugs})
            self.coverage["experts"].append({"name": name, "role": "Researcher", "kit": [ACTIVE, DEFERRED], "original_skills": [{"slug": slug, "essential_function": "Research the supplied account and summarize evidence.", "disposition": "role-kit", "gap": None, "replacements": [{"id": ACTIVE, "fit": "broader", "why": "Supplies the evidence research workflow."}]} for slug in slugs]})
        capture = self.add_capture(b"Full archived response showing the observed metric.\n")
        self.evidence = {"observations": [{"id": "usage", "capture": capture, "original_response_sha256": capture["sha256"]}]}
        for slug, path in [("account-research", "skills/research"), ("account-writing", "skills/writing")]:
            self.write(f"provenance/skills/{slug}.json", {"source": {"repo": "example/sales", "path": path, "commit": PIN}, "evidence_ids": ["usage"]})
        self.deferred = {"schema_version": 1, "skills": [], "ads-native-source-files": []}
        for path in ("ads/SKILL.md", "skills/ads-audit/SKILL.md", "LICENSE", "THIRD_PARTY_NOTICES.md"):
            data = ("Original source for " + path + "\n").encode()
            self.deferred["ads-native-source-files"].append(self.add_source(path, data))
        for path in ("ads", "skills/ads-audit"):
            self.deferred["skills"].append({"id": "example/native:" + path, "name": Path(path).name, "source": {"repo": "example/native", "commit": PIN, "path": path}, "license": "MIT", "license_paths": ["LICENSE"], "notice_paths": ["THIRD_PARTY_NOTICES.md"], "author": "Original Author", "reason": "Native runtime is unavailable in the importer.", "source_files_ref": "ads-native-source-files", "evidence_ids": ["usage"]})
        notice = self.add_source("LICENSE", b"Fixture for a separately attributed third-party MIT notice.\n")
        notice.update(repo=NOTICE_REPO, commit=NOTICE_PIN)
        self.deferred["ads-native-source-files"].append(notice)
        self.deferred["skills"][0]["additional_licenses"] = [{"spdx": "MIT", "author": "Wafris LLC (d/b/a Knowatoa)", "source_url": NOTICE_URL}]
        self.save()

    def write(self, path, value):
        destination = self.root / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(value), encoding="utf-8")

    def add_capture(self, data):
        digest = hashlib.sha256(data).hexdigest()
        path = "provenance/evidence-files/" + digest
        destination = self.root / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
        return {"file": path, "sha256": digest, "size": len(data)}

    def add_source(self, path, data):
        digest = hashlib.sha256(data).hexdigest()
        archive = "provenance/deferred-originals/" + digest
        destination = self.root / archive
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
        return {"repo": "example/native", "commit": PIN, "path": path, "sha256": digest, "blob_sha1": hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest(), "size": len(data), "mode": "100644", "archive": archive}

    def save(self):
        self.write("provenance/roster-baseline.json", self.roster)
        self.write("provenance/expert-coverage.json", self.coverage)
        self.write("provenance/evidence.json", self.evidence)
        self.write("provenance/deferred-skills.json", self.deferred)

    def assert_failure(self, phrase):
        self.save()
        errors = check_research.validate(self.root)
        self.assertTrue(any(phrase in error for error in errors), errors)

    def test_complete_roster_and_shared_deferred_sources_pass(self):
        self.assertEqual(check_research.validate(self.root), [])

    def test_inline_deferred_files_and_its_extra_evidence_pass(self):
        for entry in self.deferred["skills"]:
            entry["files"] = copy.deepcopy(self.deferred[entry.pop("source_files_ref")])
        del self.deferred["ads-native-source-files"]
        self.deferred["skills"][0]["evidence"] = [self.add_capture(b"Independent licensing inspection\n")]
        self.save()
        self.assertEqual(check_research.validate(self.root), [])

    def test_missing_expert_is_detected_even_when_declared_totals_are_unchanged(self):
        self.coverage["experts"].pop()
        self.assert_failure("expert roster mismatch")

    def test_replacing_an_expert_with_duplicate_does_not_preserve_coverage(self):
        self.coverage["experts"][-1] = copy.deepcopy(self.coverage["experts"][0])
        self.assert_failure("duplicate expert")

    def test_missing_original_is_detected(self):
        self.coverage["experts"][0]["original_skills"].pop()
        self.assert_failure("original roster mismatch")

    def test_duplicate_original_cannot_hide_an_omission_at_same_total(self):
        rows = self.coverage["experts"][0]["original_skills"]
        rows[-1] = copy.deepcopy(rows[0])
        self.assert_failure("duplicate original skill row")

    def test_both_roster_and_coverage_cannot_be_shrunk_by_editing_expected_counts(self):
        self.roster["experts"].pop()
        self.coverage["experts"].pop()
        self.roster["expected_experts"] = 31
        self.roster["expected_assignments"] = 310
        self.assert_failure("declared totals must be 32 experts and 321 assignments")

    def test_unknown_kit_and_mapping_ids_are_rejected(self):
        self.coverage["experts"][0]["kit"].append("invented/repo:skill")
        self.coverage["experts"][0]["original_skills"][0]["replacements"][0]["id"] = "invented/repo:skill"
        self.assert_failure("unresolved replacement id")

    def test_real_replacement_from_another_kit_is_not_accepted(self):
        self.coverage["experts"][0]["original_skills"][0]["replacements"][0]["id"] = OTHER_ACTIVE
        self.assert_failure("replacement does not belong to this expert's kit")

    def test_full_coverage_requires_a_real_replacement(self):
        row = self.coverage["experts"][0]["original_skills"][0]
        row.update(disposition="covered", replacements=[])
        self.assert_failure("covered disposition requires a replacement")

    def test_partial_and_gap_require_explanation(self):
        for disposition in ("partial", "gap"):
            with self.subTest(disposition=disposition):
                row = self.coverage["experts"][0]["original_skills"][0]
                row.update(disposition=disposition, gap="  ")
                self.assert_failure("must explain missing capability")

    def test_capture_is_required_not_just_a_claimed_response_hash(self):
        self.evidence["observations"][0].pop("capture")
        self.assert_failure("file record must be an object")

    def test_archived_response_tampering_is_detected(self):
        capture = self.evidence["observations"][0]["capture"]
        (self.root / capture["file"]).write_bytes(b"Different upstream claim\n")
        self.assert_failure("captured bytes differ")

    def test_original_response_hash_cannot_disagree_with_capture(self):
        self.evidence["observations"][0]["original_response_sha256"] = "0" * 64
        self.assert_failure("capture differs from original_response_sha256")

    def test_evidence_reference_must_resolve(self):
        self.deferred["skills"][0]["evidence_ids"] = ["missing-observation"]
        self.assert_failure("unresolved evidence id")

    def test_deferred_source_tampering_and_blob_identity_are_checked(self):
        source = self.deferred["ads-native-source-files"][0]
        (self.root / source["archive"]).write_bytes(b"Tampered skill advice\n")
        self.assert_failure("original Git blob SHA-1 differs")

    def test_blob_mismatch_is_caught_even_when_sha256_matches(self):
        self.deferred["ads-native-source-files"][0]["blob_sha1"] = "0" * 40
        self.assert_failure("original Git blob SHA-1 differs")

    def test_deferred_primary_must_match_pinned_skill_path(self):
        self.deferred["skills"][0]["source"]["path"] = "missing"
        self.deferred["skills"][0]["id"] = "example/native:missing"
        self.assert_failure("primary SKILL.md absent")

    def test_missing_license_remains_error_after_removing_its_archive(self):
        rows = self.deferred["ads-native-source-files"]
        license_file = next(r for r in rows if r["path"] == "LICENSE")
        rows.remove(license_file)
        (self.root / license_file["archive"]).unlink()
        self.assert_failure("controlling ancestor license source file is absent")

    def test_required_notice_is_checked_even_when_license_is_present(self):
        rows = self.deferred["ads-native-source-files"]
        notice = next(r for r in rows if r["path"] == "THIRD_PARTY_NOTICES.md")
        rows.remove(notice)
        (self.root / notice["archive"]).unlink()
        self.assert_failure("declared notice_paths are absent")

    def test_cross_repository_notice_is_required_after_row_and_archive_removal(self):
        rows = self.deferred["ads-native-source-files"]
        notice = next(r for r in rows if r["repo"] == NOTICE_REPO)
        rows.remove(notice)
        (self.root / notice["archive"]).unlink()
        self.assert_failure("declared additional license is absent from exact pinned sources")

    def test_same_license_name_from_wrong_repo_or_commit_cannot_satisfy_notice(self):
        notice = next(r for r in self.deferred["ads-native-source-files"] if r["repo"] == NOTICE_REPO)
        for field, replacement in (("repo", "unrelated/project"), ("commit", "2" * 40)):
            with self.subTest(field=field):
                original = notice[field]
                notice[field] = replacement
                self.assert_failure("declared additional license is absent from exact pinned sources")
                notice[field] = original

    def test_additional_notice_requires_a_pinned_github_blob_url(self):
        declaration = self.deferred["skills"][0]["additional_licenses"][0]
        for url in (NOTICE_URL.replace(NOTICE_PIN, "main"), NOTICE_URL + "?raw=1",
                    NOTICE_URL + "#L1", NOTICE_URL.replace("github.com", "github.com.example.com"),
                    NOTICE_URL.replace("github.com", "user@github.com"), None):
            with self.subTest(url=url):
                declaration["source_url"] = url
                self.save()
                self.assertTrue(any("additional license[0]" in error for error in check_research.validate(self.root)))

    def test_unsafe_archive_pointer_is_rejected_without_following_it(self):
        self.deferred["ads-native-source-files"][0]["archive"] = "../outside"
        self.assert_failure("archive must be provenance/deferred-originals/<sha256>")

    def test_symlinked_capture_cannot_read_outside_repository(self):
        capture = self.evidence["observations"][0]["capture"]
        target = self.root / capture["file"]
        content = target.read_bytes()
        outside = self.root / "outside-response"
        outside.write_bytes(content)
        target.unlink()
        try:
            target.symlink_to(outside)
        except OSError as exc:
            self.skipTest(f"Host does not permit test symlinks: {exc}")
        self.assert_failure("symlink/reparse point")

    def test_unreferenced_archive_cannot_be_smuggled_into_bundle(self):
        self.add_source("unselected/secret-looking.txt", b"Unreviewed source bytes\n")
        self.assert_failure("orphan archive")

    def test_missing_mode_is_not_silently_normalized(self):
        self.deferred["ads-native-source-files"][0].pop("mode")
        self.assert_failure("mode must preserve")

    def test_source_cannot_be_both_installed_and_deferred(self):
        self.write("provenance/skills/collision.json", {"source": copy.deepcopy(self.deferred["skills"][0]["source"]), "evidence_ids": ["usage"]})
        self.assert_failure("installed/deferred overlap")

    def test_non_object_documents_and_unresolved_refs_return_errors_not_crashes(self):
        self.deferred["skills"][0]["source_files_ref"] = {"invalid": "key"}
        self.assert_failure("source_files_ref does not resolve")
        self.write("provenance/roster-baseline.json", [])
        self.assertTrue(any("document must be a JSON object" in e for e in check_research.validate(self.root)))

    def test_duplicate_json_keys_do_not_silently_replace_roster(self):
        (self.root / "provenance/roster-baseline.json").write_text('{"experts": [], "experts": []}', encoding="utf-8")
        self.assertTrue(any("duplicate JSON key" in e for e in check_research.validate(self.root)))


if __name__ == "__main__":
    unittest.main()
