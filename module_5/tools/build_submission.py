"""Build the Canvas ZIP from exact committed bytes, without EOL conversion."""

import subprocess
import zipfile

from verify_submission import committed_files, repository_root, main as verify


def main():
    root = repository_root()
    output = root / "module_5" / "output" / "module_5_submission.zip"
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name in sorted(committed_files(root)):
            contents = subprocess.run(
                ["git", "show", f"HEAD:{name}"], cwd=root,
                check=True, capture_output=True,
            ).stdout
            archive.writestr(name, contents)
    return verify()


if __name__ == "__main__":
    raise SystemExit(main())
