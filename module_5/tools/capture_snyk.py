"""Save genuine Snyk CLI output and machine-readable results."""

from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
command = [
    r"C:\Program Files\nodejs\npm.cmd", "exec", "--yes",
    "--package=snyk", "--", "snyk", "test",
    "--file=requirements.txt", r"--command=.venv\Scripts\python.exe",
    "--json-file-output=snyk-results.json",
]
result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True,
                        encoding="utf-8", errors="replace", check=False)
output = result.stdout + result.stderr
header = (
    "Snyk dependency scan - captured CLI output\n"
    f"Captured: {datetime.now(timezone.utc).isoformat()}\n"
    f"Exit code: {result.returncode}\n"
    "Command: snyk test --file=requirements.txt "
    "--command=.venv\\Scripts\\python.exe\n\n"
)
(ROOT / "snyk-analysis.txt").write_text(header + output, encoding="utf-8")
print(output)
raise SystemExit(result.returncode)
