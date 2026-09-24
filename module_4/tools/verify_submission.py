"""Verify that the Canvas ZIP matches the committed Module 3 folder."""

from __future__ import annotations

import hashlib
from pathlib import Path
import subprocess
import sys
import zipfile


MODULE_DIRECTORY = "module_3"
REQUIRED_FILES = {
    "github.txt",
    "limitations.pdf",
    "load_data.py",
    "models.py",
    "orm_queries.py",
    "query_data.py",
    "query_results.pdf",
    "README.md",
    "requirements.txt",
    "screenshots/flask_webpage.png",
    "screenshots/raw_sql_output.png",
    "screenshots/sqlalchemy_orm_output.png",
}
FORBIDDEN_PARTS = {
    ".env",
    ".pytest_cache",
    ".venv",
    "__pycache__",
    "runtime",
    "tmp",
}


def repository_root() -> Path:
    """Return the Git repository root containing this script."""
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        check=True,
        capture_output=True,
        text=True,
    )
    return Path(result.stdout.strip()).resolve()


def committed_files(root: Path) -> set[str]:
    """Return files committed under module_3 at the current HEAD."""
    result = subprocess.run(
        [
            "git",
            "ls-tree",
            "-r",
            "--name-only",
            "HEAD",
            MODULE_DIRECTORY,
        ],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return set(result.stdout.splitlines())


def main() -> int:
    """Validate required files, archive integrity, and Git correspondence."""
    root = repository_root()
    archive_path = root / "module_3.zip"
    if not archive_path.is_file():
        print(f"Missing archive: {archive_path}", file=sys.stderr)
        return 1

    expected = committed_files(root)
    expected_relative = {
        path.removeprefix(f"{MODULE_DIRECTORY}/") for path in expected
    }
    missing_required = REQUIRED_FILES - expected_relative
    if missing_required:
        print(
            "Missing required committed files: "
            + ", ".join(sorted(missing_required)),
            file=sys.stderr,
        )
        return 1

    unsafe = {
        path
        for path in expected
        if FORBIDDEN_PARTS.intersection(Path(path).parts)
    }
    if unsafe:
        print(
            "Generated or sensitive paths are committed: "
            + ", ".join(sorted(unsafe)),
            file=sys.stderr,
        )
        return 1

    with zipfile.ZipFile(archive_path) as archive:
        actual = {
            name for name in archive.namelist() if not name.endswith("/")
        }
        damaged = archive.testzip()

    if damaged:
        print(f"Archive CRC failure: {damaged}", file=sys.stderr)
        return 1
    if actual != expected:
        print("ZIP and Git file manifests differ.", file=sys.stderr)
        for path in sorted(expected - actual):
            print(f"  Missing from ZIP: {path}", file=sys.stderr)
        for path in sorted(actual - expected):
            print(f"  Extra in ZIP: {path}", file=sys.stderr)
        return 1

    digest = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    print(f"Submission verification passed: {len(actual)} files")
    print(f"Archive: {archive_path}")
    print(f"SHA-256: {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
