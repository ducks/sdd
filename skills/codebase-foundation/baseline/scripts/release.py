"""Local release preparation. No network, tagging, commits or publication."""

import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import tomllib

ROOT = Path.cwd().resolve()


def command(*args):
    return subprocess.check_output(args, cwd=ROOT, text=True, stderr=subprocess.STDOUT).strip()


def metadata():
    if (ROOT / "Cargo.toml").exists():
        package = tomllib.loads((ROOT / "Cargo.toml").read_text())["package"]
        name, version = package["name"], package["version"]
        lock = tomllib.loads((ROOT / "Cargo.lock").read_text())
        assert any(
            p["name"] == name and p["version"] == version for p in lock.get("package", [])
        ), "Cargo.lock package version mismatch"
        return name, version, "rust"
    return "sdd", (ROOT / "VERSION").read_text().strip(), "source"


def setup():
    assert sys.version_info >= (3, 12), "Python 3.12+ required"
    tools = ["make", "git"]
    if (ROOT / "Cargo.toml").exists():
        tools += ["cargo", "rustfmt", "cc"]
    for tool in tools:
        assert shutil.which(tool), f"missing declared tool: {tool}"
        print(command(tool, "--version").splitlines()[0])
    if "cargo" in tools:
        print(command("cargo", "clippy", "--version"))
    print(sys.version.splitlines()[0])


def safe_directory(name):
    path = ROOT / name
    assert not path.is_symlink(), f"{name} must not be a symlink"
    assert path.resolve().parent == ROOT, "owned directory escaped root"
    return path


def tree_state():
    # Do not mistake a containing checkout for this project's own Git history.
    if (ROOT / ".git").exists():
        status = command("git", "status", "--porcelain", "--untracked-files=all")
        assert not status or os.getenv("RELEASE_ALLOW_DIRTY") == "1", "working tree is dirty"
        if status:
            print("Explicit dirty preview:\n" + status)
        revision = command("git", "rev-parse", "HEAD")
        return revision, bool(status)
    revision = os.getenv("RELEASE_SOURCE_ID")
    assert revision, "exported tree requires explicit RELEASE_SOURCE_ID"
    return revision, True


def check():
    name, version, kind = metadata()
    assert re.fullmatch(r"\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?", version), "invalid SemVer"
    changelog = (ROOT / "CHANGELOG.md").read_text()
    match = re.search(r"^##\s+\[?(\d+\.\d+\.\d+(?:-[\w.-]+)?)\]?", changelog, re.M)
    assert match and match[1] == version, "latest changelog version differs from source"
    section = changelog[match.end() :].split("\n## ", 1)[0]
    assert re.search(r"^- \S.+", section, re.M), "release notes must describe actual changes"
    for filename in ("README.md", "RELEASE.md", "LICENSE"):
        assert (ROOT / filename).stat().st_size > 20, f"{filename} missing or empty"
    docs = (ROOT / "RELEASE.md").read_text()
    for term in ("make release-check", "make release", "vVERSION", "approval"):
        assert term in docs, f"release documentation missing {term}"
    revision, dirty = tree_state()
    if (ROOT / ".git").exists():
        assert not command("git", "tag", "--list", "v" + version), "release tag already exists"
    if kind == "rust":
        binary = ROOT / "target/release" / name
        assert binary.is_file() and not binary.is_symlink(), "release binary absent"
        assert command(str(binary), "--version") == version, "built binary version differs"
        assert command(str(binary), "7") == "14", "built CLI behavior differs"
        bad = subprocess.run(
            [str(binary), "9223372036854775807"], cwd=ROOT, capture_output=True, timeout=5
        )
        assert bad.returncode == 2, "binary must reject overflow"
    else:
        bundle = ROOT / "dist/sdd-source.tar.gz"
        assert bundle.is_file() and not bundle.is_symlink(), "make build before release-check"
        with tarfile.open(bundle) as package:
            required = {"Makefile", "VERSION", "LICENSE", "README.md", "RELEASE.md"}
            required |= {
                f"skills/{n}/SKILL.md"
                for n in ("monitoring-stack", "reliable-worker", "codebase-foundation")
            }
            assert required <= set(package.getnames()), (
                "source bundle missing required capabilities"
            )
            for member in package:
                path = Path(member.name)
                assert member.isfile() and not path.is_absolute() and ".." not in path.parts
                assert package.extractfile(member).read() == (ROOT / path).read_bytes(), (
                    "stale source bundle"
                )
            assert package.extractfile("VERSION").read().decode().strip() == version
    return {
        "name": name,
        "version": version,
        "source": revision,
        "dirty_preview": dirty,
        "kind": kind,
        "toolchain": command("rustc", "--version") if kind == "rust" else sys.version,
    }


def archive(path, members):
    """Fixed member order/metadata; source bundles are repeatable for identical bytes."""
    assert not path.is_symlink(), "archive destination must not be a symlink"
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as temporary:
        tmp = Path(temporary.name)
    try:
        with (
            tmp.open("wb") as raw,
            gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as compressed,
            tarfile.open(fileobj=compressed, mode="w") as bundle,
        ):
            for name, data, mode in sorted(members):
                info = tarfile.TarInfo(name)
                info.size, info.mode, info.mtime = len(data), mode, 0
                bundle.addfile(info, io.BytesIO(data))
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)
    with tarfile.open(path) as bundle:
        assert sorted(bundle.getnames()) == sorted(m[0] for m in members)
        for name, data, mode in members:
            member = bundle.getmember(name)
            assert member.isfile() and member.mode == mode
            assert bundle.extractfile(member).read() == data, "archive contents differ"
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_build():
    dist = safe_directory("dist")
    dist.mkdir(exist_ok=True)
    members = []
    for name in [
        "skills",
        "examples",
        "evaluation",
        "tests",
        "scripts",
        "docs",
        ".github",
        "README.md",
        "LICENSE",
        "VERSION",
        "CHANGELOG.md",
        "RELEASE.md",
        "Makefile",
        "shell.nix",
        "pyproject.toml",
        "requirements-dev.txt",
        "AGENTS.md",
        ".gitignore",
    ]:
        p = ROOT / name
        files = p.rglob("*") if p.is_dir() else [p]
        for f in files:
            if f.is_file() and "__pycache__" not in f.parts and f.suffix != ".pyc":
                assert not f.is_symlink(), "do not bundle symlinks"
                relative = f.relative_to(ROOT)
                if any(part in ("target", "dist", ".venv") for part in relative.parts):
                    continue
                members.append((str(relative), f.read_bytes(), 0o644))
    assert members, "empty source package"
    return archive(dist / "sdd-source.tar.gz", members)


def prepare():
    info = check()
    dist = safe_directory("dist")
    dist.mkdir(exist_ok=True)
    if info["kind"] == "rust":
        members = [
            (n, (ROOT / n).read_bytes(), 0o644) for n in ["README.md", "LICENSE", "CHANGELOG.md"]
        ]
        members += [(info["name"], (ROOT / "target/release" / info["name"]).read_bytes(), 0o755)]
    else:
        members = [("sdd-source.tar.gz", (dist / "sdd-source.tar.gz").read_bytes(), 0o644)]
    members.append(("manifest.json", (json.dumps(info, sort_keys=True) + "\n").encode(), 0o644))
    output = dist / f"{info['name']}-{info['version']}.tar.gz"
    digest = archive(output, members)
    checksums = dist / "SHA256SUMS"
    assert not checksums.is_symlink(), "checksum destination must not be a symlink"
    checksums.write_text(f"{digest}  {output.name}\n")
    print(json.dumps({"archive": str(output), "sha256": digest, **info}, sort_keys=True))
    print("Local preparation only. Publication requires separate explicit approval.")


def main():
    action = sys.argv[1]
    if action == "help":
        text = (ROOT / "Makefile").read_text()
        for line in text.splitlines():
            if "## " in line:
                print(line.split(":", 1)[0] + " - " + line.split("## ", 1)[1])
    elif action == "setup":
        setup()
    elif action == "clean":
        target = safe_directory("target" if (ROOT / "Cargo.toml").exists() else "dist")
        if target.exists():
            shutil.rmtree(target)
    elif action == "check":
        print(json.dumps(check(), sort_keys=True))
    elif action == "prepare":
        prepare()
    elif action == "source-build":
        print(source_build())
    else:
        raise ValueError("unknown action: " + action)


if __name__ == "__main__":
    try:
        main()
    except (AssertionError, OSError, ValueError, KeyError, subprocess.CalledProcessError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
