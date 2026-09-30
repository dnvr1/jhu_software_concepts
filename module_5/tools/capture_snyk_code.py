"""Capture genuine Snyk Code SAST output for the extra-credit evidence."""

from datetime import datetime, timezone
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.stdout.reconfigure(encoding="utf-8")
npm = shutil.which("npm.cmd") or shutil.which("npm")
if not npm:
    npm = r"C:\Program Files\nodejs\npm.cmd"
command = [npm, "exec", "--yes", "--package=snyk", "--", "snyk", "code",
           "test", "--json-file-output=snyk-code-results.json"]
result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True,
                        encoding="utf-8", errors="replace", check=False)
output = result.stdout + result.stderr
header = ("Snyk Code SAST - captured CLI output\n"
          f"Captured: {datetime.now(timezone.utc).isoformat()}\n"
          f"Exit code: {result.returncode}\n"
          "Command: snyk code test --json-file-output=snyk-code-results.json\n\n")
(ROOT / "snyk-code-analysis.txt").write_text(header + output, encoding="utf-8")
print(output)
raise SystemExit(result.returncode)
