"""Read-only inventory and opt-in disposable behavioral verification.

This is not a shell parser, sandbox, or proof against malicious project code.
Never invoke make (including make -n) without --allow-exec.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import shlex
import signal
import subprocess
import tempfile
import tomllib

REQUIRED = (
    "help",
    "setup",
    "format",
    "lint",
    "test",
    "check",
    "build",
    "clean",
    "release-check",
    "release",
)
SKILL = Path(__file__).resolve().parents[1]


def read(path):
    if path.is_symlink():
        raise ValueError(f"refusing symlink: {path}")
    return path.read_text(errors="replace") if path.is_file() else ""


def targets(text):
    found = {}
    current = []
    for line in text.splitlines():
        match = re.match(r"^([A-Za-z][\w .-]*):([^=].*|)$", line)
        if match:
            current = match[1].split()
            for name in current:
                found[name] = {"dependencies": match[2].split("#")[0].split(), "recipe": ""}
        elif line.startswith("\t"):
            for name in current:
                found[name]["recipe"] += line.strip() + "\n"
    return found


def version_info(project):
    cargo = read(project / "Cargo.toml")
    pyproject = read(project / "pyproject.toml")
    package = read(project / "package.json")
    if cargo:
        value = tomllib.loads(cargo).get("package", {}).get("version")
        return "rust", value if isinstance(value, str) else None
    if pyproject:
        return "python", tomllib.loads(pyproject).get("project", {}).get("version")
    if package:
        return "javascript", json.loads(package).get("version")
    return "source", read(project / "VERSION").strip() or None


def run_command(project, args, timeout=60):
    """Bounded time and retained output; resource limits apply to child processes."""
    import resource

    def limits():
        resource.setrlimit(resource.RLIMIT_FSIZE, (128 * 1024 * 1024, 128 * 1024 * 1024))
        resource.setrlimit(resource.RLIMIT_NOFILE, (128, 128))
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))

    environment = {
        k: v
        for k, v in os.environ.items()
        if k
        in (
            "PATH",
            "HOME",
            "RUSTUP_HOME",
            "CARGO_HOME",
            "LANG",
            "NIX_SSL_CERT_FILE",
            "SSL_CERT_FILE",
            "TMPDIR",
        )
    }
    environment.update(
        {
            "PYTHONDONTWRITEBYTECODE": "1",
            "CARGO_NET_OFFLINE": "true",
            "CARGO_TARGET_DIR": str(project / "target"),
            "RELEASE_SOURCE_ID": "disposable-verification-snapshot",
        }
    )
    with tempfile.TemporaryFile() as log:
        process = subprocess.Popen(
            args,
            cwd=project,
            env=environment,
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
            preexec_fn=limits,
        )
        timed_out = False
        try:
            process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
        finally:
            # Remove descendants even when a parent exits early.
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()
        log.seek(0)
        output = log.read(256 * 1024).decode(errors="replace")
    return {
        "command": args,
        "exit_code": process.returncode,
        "timed_out": timed_out,
        "output": output,
    }


def audit(project, allow_exec=False, timeout=60):
    checks = {}

    def record(name, state, detail, evidence=None):
        checks[name] = {"status": state, "detail": detail}
        if evidence is not None:
            checks[name]["evidence"] = evidence

    def assess(name, condition, detail):
        record(name, "PASS" if condition else "FAIL", detail)

    make = read(project / "Makefile")
    rules = targets(make)
    missing = sorted(set(REQUIRED) - rules.keys())
    assess("makefile_contract", not missing, "missing targets: " + ", ".join(missing))
    meaningful = [
        n
        for n in REQUIRED
        if n in rules and not rules[n]["dependencies"] and not rules[n]["recipe"].strip()
    ]
    assess("nonempty_targets", not meaningful, "empty targets: " + ", ".join(meaningful))
    kind, version = version_info(project)
    record(
        "version_source",
        "PASS" if version else "UNKNOWN",
        f"{kind} authoritative version: {version}; workspace/dynamic versions need review",
    )
    changelog = (
        read(project / "CHANGELOG.md")
        or read(project / "CHANGES.md")
        or read(project / "CHANGES.rst")
    )
    match = re.search(r"^(?:##\s+\[?|Version\s+)(\d+\.\d+\.\d+(?:-[\w.-]+)?)", changelog, re.M)
    if match and version:
        assess(
            "changelog_version",
            match[1] == version,
            f"latest release {match[1]}, source {version}; Unreleased headers are ignored",
        )
    else:
        record("changelog_version", "UNKNOWN", "review release history/version policy manually")
    if kind == "rust" and version:
        lock = read(project / "Cargo.lock")
        name = tomllib.loads(read(project / "Cargo.toml"))["package"]["name"]
        packages = tomllib.loads(lock).get("package", []) if lock else []
        assess(
            "lock_consistency",
            any(p["name"] == name and p["version"] == version for p in packages),
            "root package version must agree with lock",
        )
    else:
        record(
            "lock_consistency", "UNKNOWN", "inspect dependency resolver and frozen install behavior"
        )
    docs = read(project / "README.md") + "\n" + read(project / "RELEASE.md")
    command_lines = []
    fence = None
    for line in docs.splitlines():
        if line.strip().startswith("```"):
            fence = line.strip()[3:] if fence is None else None
        elif fence in ("", "sh", "bash", "shell"):
            command_lines.append(line)
        elif fence is None:
            command_lines.extend(re.findall(r"`([^`]+)`", line))
    advertised = set()
    for line in command_lines:
        advertised.update(re.findall(r"(?:^|[;&|]\s*)\s*\$?\s*make\s+([a-z][\w-]*)", line))
    bad_docs = sorted(advertised - rules.keys())
    assess(
        "documented_commands", not bad_docs, "unknown documented targets: " + ", ".join(bad_docs)
    )
    release_docs = read(project / "RELEASE.md")
    record(
        "release_strategy",
        "PASS"
        if all(t in release_docs for t in ("make release-check", "vVERSION", "approval"))
        else "UNKNOWN",
        "requires review of version, source, artifact, publication and recovery semantics",
    )
    ci_files = list((project / ".github/workflows").glob("*.y*ml"))
    ci = "\n".join(read(p) for p in ci_files)
    ci_targets = set(re.findall(r"\bmake\s+([a-z][\w-]*)", ci))
    if ci_files:
        assess(
            "ci_targets",
            not (ci_targets - rules.keys()),
            "unknown CI targets: " + ", ".join(sorted(ci_targets - rules.keys())),
        )
        record(
            "ci_interface",
            "PASS" if {"setup", "check", "build"} <= ci_targets else "UNKNOWN",
            "CI should reuse make setup, make check, make build; native CI may be valid",
        )
    else:
        record("ci_targets", "UNKNOWN", "no GitHub Actions workflow inspected; inspect other CI")
        record("ci_interface", "UNKNOWN", "CI not identified")
    # These are conservative diagnostics, not an attempt to interpret arbitrary shell.
    clean = rules.get("clean", {}).get("recipe", "")
    dangerous_clean = re.search(
        r"(?:rm\s+.*(?:\.\./|\$\((?:HOME|PWD)|\$HOME|/home/|/tmp/)|git\s+clean)", clean
    )
    assess(
        "cleanup_boundary",
        not dangerous_clean,
        "reject obvious cleanup outside owned generated paths",
    )
    release = rules.get("release", {}).get("recipe", "")
    external = re.search(
        r"git\s+(?:push|tag)|cargo\s+publish|(?:npm|pnpm)\s+publish|gh\s+release|curl\s", release
    )
    record(
        "publication_boundary",
        "FAIL" if external else "UNKNOWN",
        "direct publication/tagging detected"
        if external
        else "indirect scripts need review; no publication executed",
    )
    shell = read(project / "shell.nix") or read(project / "flake.nix")
    record(
        "development_environment",
        "PASS" if shell else "UNKNOWN",
        "Nix definition found; pins and declared tools still require review"
        if shell
        else "inspect setup/tool declarations",
    )
    record(
        "containers",
        "UNKNOWN",
        "context dependent; do not add containers to satisfy this checker",
    )
    record(
        "operational_readiness",
        "UNKNOWN",
        "CLI failure behavior or service health, shutdown and recovery require review",
    )
    # Only the exact reviewed local preparation helper is safe to execute automatically
    # after --allow-exec. Alternative implementations remain UNKNOWN, not rejected.
    helper = read(project / "scripts/release.py")
    reviewed = (
        bool(helper)
        and helper == read(SKILL / "baseline/scripts/release.py")
        and release.strip() == "@python3 scripts/release.py prepare"
        and rules.get("release", {}).get("dependencies") == ["release-check"]
        and clean.strip() == "@python3 scripts/release.py clean"
    )
    if reviewed and not external:
        if kind == "rust" and not (project / "Dockerfile").exists():
            record(
                "containers",
                "NOT APPLICABLE",
                "reviewed dependency-free CLI profile has no service or container requirement",
            )
        record(
            "publication_boundary",
            "PASS",
            "reviewed helper only prepares local files; no remote mutation",
        )
    runtime = (
        "help_runtime",
        "setup_runtime",
        "lint_runtime",
        "tests_execute",
        "check_runtime",
        "build_runtime",
        "test_failure_propagates",
        "check_failure_propagates",
        "release_invalid_state",
        "release_artifact",
        "cleanup_runtime",
        "undeclared_tools",
    )
    if not allow_exec:
        for name in runtime:
            record(name, "SKIP", "repository execution not authorized; static audit only")
    elif missing:
        for name in runtime:
            record(name, "SKIP", "resolve missing Makefile targets before behavioral checks")
    else:
        with tempfile.TemporaryDirectory(prefix="sdd-foundation-") as directory:
            copy = Path(directory) / "project"
            # No hooks, local credentials, existing build products or large VCS history.
            shutil.copytree(
                project,
                copy,
                symlinks=True,
                ignore=shutil.ignore_patterns(
                    ".git", "target", "dist", ".venv", "node_modules", "__pycache__", ".env", "runs"
                ),
            )
            symlinks = [p for p in copy.rglob("*") if p.is_symlink()]
            if symlinks:
                raise ValueError("execution copy contains symlinks; review/remove them first")

            def execute(name, target, success=True):
                evidence = run_command(copy, ["make", target], timeout)
                ok = not evidence["timed_out"] and ((evidence["exit_code"] == 0) == success)
                record(name, "PASS" if ok else "FAIL", f"make {target}", evidence)
                return evidence

            help_result = execute("help_runtime", "help")
            assess(
                "help_documents_targets",
                all(
                    re.search(r"\b" + re.escape(t) + r"\b", help_result["output"]) for t in REQUIRED
                ),
                "help must name every required target",
            )
            execute("setup_runtime", "setup")
            execute("lint_runtime", "lint")
            result = execute("tests_execute", "test")
            discovered = re.search(
                r"(?:Ran\s+[1-9]\d*\s+tests?|[1-9]\d*\s+passed)", result["output"]
            )
            if not discovered:
                record("tests_execute", "FAIL", "no nonzero native test-count evidence", result)
            execute("check_runtime", "check")
            execute("build_runtime", "build")
            if kind in ("rust", "python"):
                testdir = copy / "tests"
                testdir.mkdir(exist_ok=True)
                if kind == "rust":
                    fault = testdir / "sdd_foundation_injected.rs"
                    fault.write_text(
                        "#[test]\nfn sdd_injected_failure() {\n"
                        '    let n: i32 = std::env::var("SDD_SENTINEL")\n'
                        '        .unwrap_or("4".into())\n'
                        "        .parse()\n"
                        "        .unwrap();\n"
                        '    assert_eq!(n, 5, "SDD_INJECTED_FAILURE");\n}\n'
                    )
                else:
                    fault = testdir / "test_sdd_foundation_injected.py"
                    fault.write_text(
                        "import unittest\nclass Injected(unittest.TestCase):\n"
                        ' def test_sdd_failure(self): self.fail("SDD_INJECTED_FAILURE")\n'
                    )
                try:
                    for name, target in [
                        ("test_failure_propagates", "test"),
                        ("check_failure_propagates", "check"),
                    ]:
                        evidence = execute(name, target, success=False)
                        if "SDD_INJECTED_FAILURE" not in evidence["output"]:
                            record(
                                name,
                                "UNKNOWN",
                                "injected test not demonstrably executed; adapt test location",
                                evidence,
                            )
                finally:
                    fault.unlink()
            else:
                for name in ("test_failure_propagates", "check_failure_propagates"):
                    record(name, "UNKNOWN", "supply a native failing-test probe for this layout")
            if kind == "rust" and version:
                manifest = copy / "Cargo.toml"
                original = manifest.read_text()
                lockfile = copy / "Cargo.lock"
                original_lock = lockfile.read_text()
                lockfile.write_text(
                    original_lock.replace('version = "' + version + '"', 'version = "999.0.0"', 1)
                )
                manifest.write_text(
                    original.replace('version = "' + version + '"', 'version = "999.0.0"', 1)
                )
                try:
                    execute("release_invalid_state", "release-check", success=False)
                finally:
                    manifest.write_text(original)
                    lockfile.write_text(original_lock)
            else:
                record(
                    "release_invalid_state",
                    "UNKNOWN",
                    "no automated metadata mutation for this version source",
                )
            if reviewed and not external and not dangerous_clean:
                execute("release_ready", "release-check")
                execute("release_artifact", "release")
                # Independent checksum/archive validation, not helper's written claim.
                try:
                    import tarfile

                    sums = (copy / "dist/SHA256SUMS").read_text().strip().split()
                    artifact = copy / "dist" / sums[1]
                    assert artifact.parent.resolve() == (copy / "dist").resolve()
                    assert hashlib.sha256(artifact.read_bytes()).hexdigest() == sums[0]
                    with tarfile.open(artifact) as tar:
                        names = tar.getnames()
                        assert "manifest.json" in names and all(
                            ".." not in Path(n).parts and not n.startswith("/") for n in names
                        )
                        metadata = json.load(tar.extractfile("manifest.json"))
                        assert metadata["version"] == version
                        assert metadata["source"] == "disposable-verification-snapshot"
                        assert metadata["dirty_preview"] is True
                        if kind == "rust":
                            name = tomllib.loads(read(copy / "Cargo.toml"))["package"]["name"]
                            assert set(names) == {
                                name,
                                "README.md",
                                "LICENSE",
                                "CHANGELOG.md",
                                "manifest.json",
                            }
                            assert tar.getmember(name).mode == 0o755
                            binary_version = run_command(
                                copy, [str(copy / "target/release" / name), "--version"], timeout
                            )
                            assert (
                                binary_version["exit_code"] == 0
                                and binary_version["output"].strip() == version
                            ), "compiled binary version differs"
                            assert (
                                tar.extractfile(name).read()
                                == (copy / "target/release" / name).read_bytes()
                            )
                    assess(
                        "artifact_integrity",
                        True,
                        "independent archive, bytes, version and SHA256 checks",
                    )
                    if kind == "rust":
                        record(
                            "operational_readiness",
                            "PASS",
                            "CLI success and overflow exit behavior exercised by release validation; service operations not applicable",
                        )
                except (OSError, AssertionError, ValueError, KeyError) as error:
                    record("artifact_integrity", "FAIL", str(error))
                outside = Path(directory) / "outside"
                outside.mkdir()
                sentinel = outside / "keep.txt"
                sentinel.write_text("user data")
                targetdir = copy / "target"
                if targetdir.exists():
                    shutil.rmtree(targetdir)
                targetdir.symlink_to(outside, target_is_directory=True)
                try:
                    execute("cleanup_runtime", "clean", success=False)
                    assess(
                        "cleanup_preserves_data",
                        sentinel.read_text() == "user data",
                        "symlink escape tripwire remains",
                    )
                finally:
                    targetdir.unlink()
            else:
                for name in ("release_artifact", "cleanup_runtime"):
                    record(
                        name,
                        "UNKNOWN",
                        "unreviewed release/cleanup code not executed; review or provide native probes",
                    )
            setup_evidence = checks["setup_runtime"].get("evidence", {})
            setup_output = (
                setup_evidence.get("output", "") if setup_evidence.get("exit_code") == 0 else ""
            )
            commands = "\n".join(r["recipe"] for r in rules.values())
            tools = set()
            builtins = {"echo", "printf", "true", "false", "test", "if", "for", "cd", "exit"}
            for recipe in commands.splitlines():
                try:
                    words = shlex.split(recipe.lstrip("@-+"))
                except ValueError:
                    continue
                if (
                    words
                    and re.fullmatch(r"[a-z][a-z0-9_-]*", words[0])
                    and words[0] not in builtins
                ):
                    tools.add(words[0])
            declared = docs + shell + read(copy / "pyproject.toml")
            absent = [t for t in tools if t.lower() not in (declared + setup_output).lower()]
            assess(
                "undeclared_tools",
                not absent,
                "tools absent from environment/setup/docs: " + ", ".join(sorted(absent)),
            )
    counts = {
        s: sum(v["status"] == s for v in checks.values())
        for s in ("PASS", "FAIL", "SKIP", "UNKNOWN", "NOT APPLICABLE")
    }
    inventory = {}
    for name in (
        "pyproject.toml",
        "Cargo.toml",
        "Cargo.lock",
        "package.json",
        "uv.lock",
        "requirements.txt",
        "requirements-dev.txt",
        "shell.nix",
        "flake.nix",
        "README.md",
        "LICENSE",
        "LICENSE.txt",
        "AGENTS.md",
        "CHANGELOG.md",
        "CHANGES.md",
    ):
        contents = read(project / name)
        if contents:
            inventory[name] = {
                "sha256": hashlib.sha256(contents.encode()).hexdigest(),
                "bytes": len(contents.encode()),
            }
    for name in ("docker/Dockerfile", "docker/docker-compose.yml", "manage.py"):
        contents = read(project / name)
        if contents:
            inventory[name] = {
                "sha256": hashlib.sha256(contents.encode()).hexdigest(),
                "bytes": len(contents.encode()),
            }
    capabilities = {
        "makefile": "REQUIRED",
        "release_management": "REQUIRED",
        "tests": "REQUIRED",
        "documentation": "REQUIRED",
        "environment": "REQUIRED",
        "agent_instructions": "RECOMMENDED",
        "containers": "NOT APPLICABLE"
        if checks["containers"]["status"] == "NOT APPLICABLE"
        else "OPTIONAL",
        "registry_publication": "OPTIONAL",
    }
    return {
        "schema_version": 1,
        "project": str(project),
        "inventory": inventory,
        "capabilities": capabilities,
        "mode": "verify" if allow_exec else "audit",
        "checks": checks,
        "summary": counts,
        "limitations": [
            "Static syntax recognition is conservative, not full Make/shell/YAML interpretation.",
            "Authorized execution uses a disposable copy and limits, not a security sandbox.",
            "PASS applies to the named observation, not complete engineering readiness.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--allow-exec",
        action="store_true",
        help="authorize reviewed project commands in a temporary copy",
    )
    parser.add_argument("--timeout", type=int, default=60)
    args = parser.parse_args()
    if not 1 <= args.timeout <= 600:
        parser.error("timeout must be 1..600 seconds per command")
    project = args.project.resolve()
    if args.output and args.output.resolve().is_relative_to(project):
        parser.error("report must be outside the evaluated repository to keep audit read-only")
    try:
        report = audit(project, args.allow_exec, args.timeout)
    except (OSError, ValueError, KeyError) as error:
        report = {
            "checks": {"inspection": {"status": "UNKNOWN", "detail": str(error)}},
            "summary": {"FAIL": 0, "UNKNOWN": 1},
        }
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)
    else:
        print(text, end="")
    return (
        1
        if report["summary"].get("FAIL")
        else 2
        if any(report["summary"].get(s) for s in ("SKIP", "UNKNOWN"))
        else 0
    )


if __name__ == "__main__":
    raise SystemExit(main())
