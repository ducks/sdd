"""Repository checks and local source release; delegates shared preparation."""

import ast
import importlib.util
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "skills/codebase-foundation/baseline/scripts/release.py"


def main():
    action = sys.argv[1]
    if action == "lint":
        paths = list((ROOT / "skills").rglob("*.py")) + list((ROOT / "tests").glob("*.py"))
        paths += list((ROOT / "examples").rglob("*.py")) + list((ROOT / "evaluation").rglob("*.py"))
        for path in paths:
            if "__pycache__" not in path.parts:
                ast.parse(path.read_text(), filename=str(path))
        subprocess.run(
            ["ruff", "check", "skills/codebase-foundation", "scripts", "tests/test_foundation.py"],
            check=True,
        )
        subprocess.run(
            [
                "ruff",
                "format",
                "--check",
                "skills/codebase-foundation",
                "scripts",
                "tests/test_foundation.py",
            ],
            check=True,
        )
        subprocess.run(
            [
                "cargo",
                "fmt",
                "--manifest-path",
                "skills/codebase-foundation/baseline/Cargo.toml",
                "--",
                "--check",
            ],
            check=True,
        )
        print(f"Syntax checked {len(paths)} Python files; foundation style and Rust format checked")
    else:
        spec = importlib.util.spec_from_file_location("local_release", HELPER)
        helper = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(helper)
        if action == "setup":
            for tool in ("cargo", "rustfmt", "ruff", "cc"):
                assert shutil.which(tool), (
                    f"missing {tool}; enter nix-shell or provision documented tools"
                )
                subprocess.run([tool, "--version"], check=True)
            subprocess.run(["cargo", "clippy", "--version"], check=True)
        helper.main()


if __name__ == "__main__":
    main()
