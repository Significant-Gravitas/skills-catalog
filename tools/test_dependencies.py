"""Targeted, offline tests of static dependency classification and failure policy."""
from __future__ import annotations

from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest

import audit_dependencies as audit


class DependencyAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="dependency-test-", dir=Path(__file__).parent)
        self.root = Path(self.temp.name).resolve()
        self.assertEqual(self.root.parent, Path(__file__).resolve().parent)
        self.addCleanup(self.temp.cleanup)
        self.package = self.root / "skills/example"
        self.put("SKILL.md", "# Example\n")

    def put(self, path, content):
        file = self.package / path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(content, encoding="utf-8")
        return file

    def report(self):
        return audit.audit(self.root)

    def test_file_fragments_spaces_parentheses_and_hidden_support(self):
        self.put("references/space name.md", "# Actual heading\n")
        self.put("references/a(b).md", "# Parentheses\n")
        self.put(".hidden/config.json", "{}")
        self.put(".hidden/guide.md", "[same](config.json)\n")
        self.put("SKILL.md", '[encoded](references/space%20name.md#not-validated)\n[angle](<references/space name.md> "Title")\n[balanced](references/a(b).md)\n![image](.hidden/config.json)\n[anchor](#local)\n')
        result = self.report()
        self.assertEqual(result["counts"]["definite_errors"], 0)
        self.assertEqual(result["counts"]["files_scanned"], 5)
        self.assertTrue(any(f["file"] == ".hidden/guide.md" for f in result["findings"]))
        self.assertTrue(any(f.get("anchor_checked") is False for f in result["findings"]))

    def test_reference_links_and_examples_are_distinguished(self):
        self.put("references/ok.md", "# Fine\n")
        self.put("SKILL.md", '''[Example][ref]\n[Short]\n[ref]: <references/ok.md> "Title"\n[short]: references/ok.md\n[unused]: absent.md\n\n`[literal](not-a-link.md)`\n```markdown\n[example](also-not-a-link.md)\n```\nFootnote[^1].\n[^1]: This is explanatory prose, not a path.\n''')
        result = self.report()
        links = [f for f in result["findings"] if f["kind"] == "markdown-link"]
        self.assertEqual(len(links), 2)
        self.assertEqual(result["counts"]["definite_errors"], 0)

    def test_definite_missing_and_decoded_escape_are_errors(self):
        self.put("SKILL.md", "[missing](references/missing.md)\n[escape](%2e%2e/other/SKILL.md)\n[hidden missing](.hidden/missing.json)\n[state traversal](.agents/../../outside.md)\n[site path](/docs/index)\n")
        result = self.report()
        self.assertEqual(result["counts"]["definite_errors"], 4)
        classes = {f["classification"] for f in result["findings"]}
        self.assertIn("escaping-local-path", classes)
        self.assertIn("missing-local-file", classes)
        self.assertIn("root-relative-reference", classes)

    def test_runtime_urls_and_literal_paths_do_not_claim_missing_files(self):
        self.put("SKILL.md", "[remote](https://example.com/guide.md#x)\n[state](.agents/product-marketing.md)\n[native](${CLAUDE_PLUGIN_ROOT}/skills/dashboard.html)\nUse `scripts/output.py` and `/commercial-legal:review`.\n")
        result = self.report()
        self.assertEqual(result["counts"]["definite_errors"], 0)
        classes = {f["classification"] for f in result["findings"]}
        self.assertTrue({"external-url", "project-state", "dynamic-runtime-reference", "unresolved-literal", "native-command"}.issubset(classes))

    def test_python_ast_inventory_never_executes_source(self):
        self.put("scripts/helper.py", "VALUE = 1\n")
        self.put("scripts/main.py", "from .helper import VALUE\nfrom .missing import VALUE\nimport made_up_external_library\nfrom pathlib import Path\nPath('AUDIT_MUST_NOT_EXECUTE').write_text('bad')\n")
        result = self.report()
        self.assertEqual(result["counts"]["definite_errors"], 0)
        classes = {f["classification"] for f in result["findings"]}
        self.assertTrue({"python-local-import", "unresolved-python-relative-import", "python-environment-import"}.issubset(classes))
        self.assertFalse((self.root / "AUDIT_MUST_NOT_EXECUTE").exists())
        self.assertFalse((Path.cwd() / "AUDIT_MUST_NOT_EXECUTE").exists())

    def test_exact_documented_review_is_visible_and_stale_hash_does_not_hide_error(self):
        self.put("SKILL.md", "[generated](reports/latest.md)\n[other](reports/other.md)\n")
        review = self.root / "provenance/dependency-review.json"
        review.parent.mkdir(parents=True)
        record = dict(package="example", file="SKILL.md", kind="markdown-link", target="reports/latest.md", classification="generated-output", reason="Created by the documented reporting workflow at runtime.")
        review.write_text(json.dumps(dict(schema_version=1, references=[record])), encoding="utf-8")
        result = self.report()
        self.assertEqual(result["counts"]["definite_errors"], 1)
        self.assertEqual(result["counts"]["reviewed_references"], 1)
        reviewed = next(f for f in result["findings"] if f["status"] == "reviewed")
        self.assertEqual(reviewed["original_classification"], "missing-local-file")
        record["source_sha256"] = "0" * 64
        review.write_text(json.dumps(dict(schema_version=1, references=[record])), encoding="utf-8")
        result = self.report()
        self.assertEqual(result["counts"]["definite_errors"], 2)
        self.assertEqual(result["counts"]["unused_reviews"], 1)

    def test_cli_json_and_check_exit_policy(self):
        self.put("SKILL.md", "Use `scripts/runtime.py`.\n")
        output = io.StringIO()
        with redirect_stdout(output):
            self.assertEqual(audit.main(["--root", str(self.root), "--check"]), 0)
        self.assertEqual(json.loads(output.getvalue())["counts"]["review_items"], 1)
        self.put("SKILL.md", "[missing](references/missing.md)\n")
        with redirect_stdout(io.StringIO()):
            self.assertEqual(audit.main(["--root", str(self.root), "--check"]), 1)
            self.assertEqual(audit.main(["--root", str(self.root)]), 0)

    def test_source_attribution_paths_do_not_masquerade_as_installed_dependencies(self):
        provenance = self.root / "provenance"
        provenance.mkdir()
        (provenance / "files.json").write_text(json.dumps({"files": [{"source": {"repo": "owner/repo", "path": "old/SKILL.md"}}]}), encoding="utf-8")
        # Existing package-review metadata can coexist with optional exceptions.
        (provenance / "dependency-review.json").write_text(json.dumps({"schema_version": 1, "packages": []}), encoding="utf-8")
        self.put("ATTRIBUTION.md", "Original `owner/repo/old/SKILL.md`.\n[real missing link](references/missing.md)\n")
        self.put("SKILL.md", "Read `owner/repo/old/SKILL.md`. File extension `.json`.\n")
        result = self.report()
        self.assertEqual(result["counts"]["definite_errors"], 1)
        source = next(f for f in result["findings"] if f["classification"] == "source-provenance-reference")
        self.assertEqual(source["file"], "ATTRIBUTION.md")
        self.assertTrue(any(f["classification"] == "unresolved-literal" and f["file"] == "SKILL.md" for f in result["findings"]))
        self.assertFalse(any(f["target"] == ".json" for f in result["findings"]))

    def test_symlink_escape_is_reported_without_reading_target(self):
        outside = self.root / "outside.md"
        outside.write_text("[must not scan](hidden-error.md)", encoding="utf-8")
        try:
            (self.package / "outside.md").symlink_to(outside)
        except (OSError, NotImplementedError):
            self.skipTest("symlink creation unavailable on this host")
        self.put("SKILL.md", "[escape](outside.md)\n")
        result = self.report()
        self.assertEqual(result["counts"]["definite_errors"], 1)
        self.assertTrue(any(f["classification"] == "symlink-resource-not-scanned" for f in result["findings"]))
        self.assertFalse(any(f["target"] == "hidden-error.md" for f in result["findings"]))


if __name__ == "__main__":
    unittest.main()
