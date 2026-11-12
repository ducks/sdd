"""Independent controls use only disposable, reviewed fixtures; no remote operations."""

import contextlib
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/codebase-foundation"
BASELINE = SKILL / "baseline"
spec = importlib.util.spec_from_file_location("foundation_checker", SKILL / "verify/run.py")
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


def snapshot(project):
    return {
        str(p.relative_to(project)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in project.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts
    }


@contextlib.contextmanager
def fixture():
    with tempfile.TemporaryDirectory(prefix="foundation-control-") as directory:
        project = Path(directory) / "project"
        shutil.copytree(
            BASELINE, project, ignore=shutil.ignore_patterns("target", "dist", "__pycache__")
        )
        yield project


def replace(project, name, old, new):
    path = project / name
    text = path.read_text()
    assert old in text, (name, old)
    path.write_text(text.replace(old, new, 1))


class FoundationTests(unittest.TestCase):
    def test_static_audit_is_readonly_and_never_executes_make(self):
        with fixture() as project:
            before = snapshot(project)
            with patch.object(
                subprocess, "Popen", side_effect=AssertionError("execution forbidden")
            ):
                report = checker.audit(project)
            self.assertEqual(snapshot(project), before)
            self.assertEqual(report["checks"]["tests_execute"]["status"], "SKIP")
            self.assertEqual(report["summary"]["FAIL"], 0)

    def test_baseline_bootstrap_and_independent_release_probes(self):
        with fixture() as project:
            before = snapshot(project)
            report = checker.audit(project, True)
            (ROOT / "runs").mkdir(exist_ok=True)
            (ROOT / "runs/foundation-baseline.json").write_text(json.dumps(report, indent=2) + "\n")
            self.assertEqual(report["summary"]["FAIL"], 0, report)
            self.assertEqual(report["summary"]["UNKNOWN"], 0, report)
            self.assertEqual(report["summary"]["SKIP"], 0)
            self.assertEqual(
                snapshot(project), before, "verification must not change bootstrap source"
            )
            self.assertEqual(report["checks"]["test_failure_propagates"]["status"], "PASS")
            self.assertEqual(report["checks"]["release_invalid_state"]["status"], "PASS")
            self.assertEqual(report["checks"]["artifact_integrity"]["status"], "PASS")

    def test_improve_preserves_legacy_source_tests_and_make_target(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory) / "legacy"
            project.mkdir()
            (project / "src").mkdir()
            (project / "tests").mkdir()
            for filename in ("Cargo.toml", "Cargo.lock"):
                shutil.copy2(BASELINE / filename, project / filename)
            (project / "src/lib.rs").write_text(
                "pub fn double(n: i64) -> Option<i64> {\n"
                "    i64::try_from(i128::from(n) * 2).ok()\n}\n"
            )
            shutil.copy2(BASELINE / "src/main.rs", project / "src/main.rs")
            (project / "tests/legacy.rs").write_text(
                "#[test]\nfn preserves_business_behavior() {\n"
                "    assert_eq!(foundation_demo::double(21), Some(42));\n}\n"
            )
            (project / "Makefile").write_text("verify:\n\tcargo test --locked --offline\n")
            original = snapshot(project)
            result = checker.run_command(project, ["cargo", "test", "--locked", "--offline"])
            self.assertEqual(result["exit_code"], 0, result)
            # Add engineering files only. Preserve an existing developer alias.
            for name in ("scripts", ".github"):
                shutil.copytree(BASELINE / name, project / name)
            for name in (
                "README.md",
                "RELEASE.md",
                "CHANGELOG.md",
                "LICENSE",
                "shell.nix",
                ".gitignore",
                "AGENTS.md",
            ):
                shutil.copy2(BASELINE / name, project / name)
            (project / "Makefile").write_text(
                (BASELINE / "Makefile").read_text() + "\nverify: test\n"
            )
            for name, digest in original.items():
                if name != "Makefile":
                    self.assertEqual(
                        hashlib.sha256((project / name).read_bytes()).hexdigest(), digest
                    )
            report = checker.audit(project, True)
            (ROOT / "runs").mkdir(exist_ok=True)
            (ROOT / "runs/foundation-improve.json").write_text(json.dumps(report, indent=2) + "\n")
            self.assertEqual(report["summary"]["FAIL"], 0, report)
            self.assertEqual(report["summary"]["UNKNOWN"], 0, report)
            self.assertFalse((project / "Dockerfile").exists())
            self.assertIn("verify", checker.targets((project / "Makefile").read_text()))

    def test_defective_static_controls(self):
        cases = [
            (
                "missing_check",
                "Makefile",
                "check: lint test",
                "other: lint test",
                "makefile_contract",
            ),
            (
                "unsafe_publication",
                "Makefile",
                "\t@python3 scripts/release.py prepare",
                "\tgit push origin main",
                "publication_boundary",
            ),
            ("wrong_changelog", "CHANGELOG.md", "## 0.1.0", "## 9.0.0", "changelog_version"),
            (
                "missing_ci_target",
                ".github/workflows/check.yml",
                "make check",
                "make imaginary",
                "ci_targets",
            ),
            (
                "missing_doc_target",
                "README.md",
                "make setup",
                "make imaginary",
                "documented_commands",
            ),
            (
                "escaping_clean",
                "Makefile",
                "\t@python3 scripts/release.py clean",
                "\trm -rf ../outside",
                "cleanup_boundary",
            ),
            (
                "lock_drift",
                "Cargo.lock",
                'version = "0.1.0"',
                'version = "9.0.0"',
                "lock_consistency",
            ),
        ]
        results = []
        for name, path, old, new, check in cases:
            with self.subTest(name=name), fixture() as project:
                replace(project, path, old, new)
                report = checker.audit(project)
                self.assertEqual(report["checks"][check]["status"], "FAIL", report)
                results.append(
                    {
                        "control": name,
                        "expected": "FAIL",
                        "observed": report["checks"][check]["status"],
                    }
                )
        (ROOT / "runs").mkdir(exist_ok=True)
        (ROOT / "runs/foundation-static-controls.json").write_text(
            json.dumps(results, indent=2) + "\n"
        )

    def test_defective_behavioral_controls(self):
        cases = [
            (
                "noop_tests",
                "test: ## Run unit, integration and documentation tests\n\tcargo test --locked --offline",
                "test: ## Run unit, integration and documentation tests\n\t@true",
                "tests_execute",
            ),
            (
                "swallowed_failure",
                "check: lint test ## Complete local quality gate",
                "check: ## Complete local quality gate\n\tcargo test --locked --offline || true",
                "check_failure_propagates",
            ),
            (
                "unchecked_release",
                "release-check: check build ## Validate metadata, tree, tags, docs and the built binary\n\t@python3 scripts/release.py check",
                "release-check: ## Validate metadata, tree, tags, docs and the built binary\n\t@true",
                "release_invalid_state",
            ),
            (
                "undeclared_tool",
                "setup: ## Validate installed native tools; enter nix-shell to obtain them\n\t@python3 scripts/release.py setup",
                "setup: ## Validate installed native tools; enter nix-shell to obtain them\n\tmystery-tool",
                "undeclared_tools",
            ),
        ]
        results = []
        for name, old, new, check in cases:
            with self.subTest(name=name), fixture() as project:
                replace(project, "Makefile", old, new)
                report = checker.audit(project, True)
                self.assertEqual(report["checks"][check]["status"], "FAIL", report)
                results.append(
                    {
                        "control": name,
                        "expected": "FAIL",
                        "observed": report["checks"][check]["status"],
                    }
                )
        (ROOT / "runs").mkdir(exist_ok=True)
        (ROOT / "runs/foundation-runtime-controls.json").write_text(
            json.dumps(results, indent=2) + "\n"
        )

    def test_alternative_make_recipes_not_reference_matching(self):
        with fixture() as project:
            replace(
                project,
                "Makefile",
                "\tcargo test --locked --offline",
                "\tcargo test --offline --locked --all-targets",
            )
            report = checker.audit(project, True)
            self.assertEqual(report["summary"]["FAIL"], 0, report)
            self.assertEqual(report["summary"]["UNKNOWN"], 0, report)

    def test_alternative_release_is_unknown_not_declared_broken(self):
        with fixture() as project:
            (project / "scripts/release.py").write_text(
                "# Different reviewed workflow would need native probes.\n"
            )
            report = checker.audit(project)
            self.assertEqual(report["checks"]["publication_boundary"]["status"], "UNKNOWN")
            self.assertEqual(report["summary"]["FAIL"], 0)

    def test_make_in_prose_is_not_a_documented_command(self):
        with fixture() as project:
            with (project / "README.md").open("a") as f:
                f.write(
                    "\nMake sure the examples make it clear how to make the change.\n"
                    "```sh\n./manage.py check\n```\nUse --loop to make it run.\n"
                    "```sh\n./manage.py run\n```\n"
                )
            report = checker.audit(project)
            self.assertEqual(report["checks"]["documented_commands"]["status"], "PASS")

    def test_timeout_kills_process_group(self):
        with tempfile.TemporaryDirectory() as directory:
            result = checker.run_command(
                Path(directory), [sys.executable, "-c", "import time;time.sleep(30)"], timeout=1
            )
            self.assertTrue(result["timed_out"])
            self.assertNotEqual(result["exit_code"], 0)

    def test_audit_rejects_output_inside_target(self):
        with fixture() as project:
            result = subprocess.run(
                [
                    sys.executable,
                    str(SKILL / "verify/run.py"),
                    "--project",
                    str(project),
                    "--output",
                    str(project / "report.json"),
                ],
                capture_output=True,
            )
            self.assertEqual(result.returncode, 2)
            self.assertFalse((project / "report.json").exists())

    def test_cleanup_and_archive_symlink_boundaries(self):
        with fixture() as project, tempfile.TemporaryDirectory() as directory:
            outside = Path(directory)
            (outside / "keep").write_text("valuable")
            (project / "target").symlink_to(outside, target_is_directory=True)
            result = checker.run_command(project, ["python3", "scripts/release.py", "clean"])
            self.assertNotEqual(result["exit_code"], 0)
            self.assertEqual((outside / "keep").read_text(), "valuable")
            (project / "target").unlink()
            (project / "target").mkdir()
            (project / "target/generated.txt").write_text("owned build output")
            (project / "untracked-source.txt").write_text("preserve source")
            result = checker.run_command(project, ["make", "clean"])
            self.assertEqual(result["exit_code"], 0, result)
            self.assertFalse((project / "target").exists())
            self.assertEqual((project / "untracked-source.txt").read_text(), "preserve source")
            result = checker.run_command(project, ["make", "build"])
            self.assertEqual(result["exit_code"], 0, result)
            (project / "dist").symlink_to(outside, target_is_directory=True)
            result = checker.run_command(project, ["python3", "scripts/release.py", "prepare"])
            self.assertNotEqual(result["exit_code"], 0)
            self.assertIn("dist must not be a symlink", result["output"])
            self.assertEqual(sorted(p.name for p in outside.iterdir()), ["keep"])

    def test_archive_reproducible_for_identical_bytes(self):
        spec = importlib.util.spec_from_file_location(
            "release_helper", BASELINE / "scripts/release.py"
        )
        helper = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(helper)
        with tempfile.TemporaryDirectory() as directory:
            a, b = Path(directory) / "a.tar.gz", Path(directory) / "b.tar.gz"
            members = [("README.md", b"example", 0o644), ("tool", b"executable", 0o755)]
            self.assertEqual(helper.archive(a, members), helper.archive(b, list(reversed(members))))

    def test_release_rejects_existing_tag_dirty_tree_and_missing_source_identity(self):
        spec = importlib.util.spec_from_file_location(
            "release_guards", BASELINE / "scripts/release.py"
        )
        helper = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(helper)
        with fixture() as project, patch.object(helper, "ROOT", project):
            with patch.dict(os.environ, {}, clear=True):
                with self.assertRaisesRegex(AssertionError, "RELEASE_SOURCE_ID"):
                    helper.tree_state()
            (project / ".git").mkdir()

            def fake_command(*args):
                if args[:2] == ("git", "status"):
                    return " M src/lib.rs"
                return "pretend-reviewed-revision"

            with (
                patch.object(helper, "command", side_effect=fake_command),
                patch.dict(os.environ, {}, clear=True),
            ):
                with self.assertRaisesRegex(AssertionError, "dirty"):
                    helper.tree_state()

            def tagged(*args):
                if args[:2] == ("git", "status"):
                    return ""
                if args[:2] == ("git", "tag"):
                    return "v0.1.0"
                return "pretend-reviewed-revision"

            with patch.object(helper, "command", side_effect=tagged):
                with self.assertRaisesRegex(AssertionError, "already exists"):
                    helper.check()


if __name__ == "__main__":
    unittest.main()
