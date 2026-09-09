"""Clean source text and invoke the instructor's local LLM package."""

from __future__ import annotations

import argparse
import copy
import hashlib
import html
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

from bs4 import BeautifulSoup
from storage import load_data, save_data

FIELDS = (
    "program",
    "program_name",
    "university",
    "comments",
    "date_added",
    "url",
    "status",
    "decision_date",
    "acceptance_date",
    "rejection_date",
    "term",
    "citizenship",
    "gre",
    "gre_v",
    "gre_aw",
    "gre_quantitative",
    "score_provenance",
    "gpa",
    "degree",
    "raw_program",
    "raw_text",
    "source_url",
)
LLM_FIELDS = ("llm-generated-program", "llm-generated-university")


def text_value(value: object) -> str | None:
    """Remove markup/entities and normalize display whitespace.

    Args:
        value: A source value, including None for unavailable information.

    Returns:
        Clean text or None when no text is available.
    """
    if value is None:
        return None
    text = str(value)
    # Do not interpret an ordinary mathematical '<' in a comment as markup.
    if re.search(r"</?[A-Za-z][^>]*>", text):
        text = BeautifulSoup(text, "html.parser").get_text(" ", strip=True)
    text = re.sub(r"\s+", " ", html.unescape(text)).strip()
    return text or None


def clean_data(records: list[dict]) -> list[dict]:
    """Clean presentation without inferring dates, scores, or outcomes.

    Args:
        records: Extracted applicant dictionaries, including raw fields.

    Returns:
        New dictionaries with consistent missing values and numeric scores.
    """
    output = []
    for record in records:
        item = {key: None for key in FIELDS}
        item.update(copy.deepcopy(record))
        for key, value in list(item.items()):
            if isinstance(value, str) and not key.startswith("raw_"):
                item[key] = text_value(value)
        for key in ("gre", "gre_v", "gre_aw", "gre_quantitative", "gpa"):
            value = item[key]
            if isinstance(value, str) and re.fullmatch(
                r"\d+(?:\.\d+)?", value
            ):
                number = float(value)
                item[key] = int(number) if number.is_integer() else number
        output.append(item)
    return output


def extend_with_llm(
    input_path: Path,
    output_path: Path,
    package: Path,
    batch_size: int = 100,
    python: str = sys.executable,
) -> int:
    """Run the supplied local app in restartable batches.

    The package defines model setup and canonical lists. No API or
    replacement model is selected. Completed batches are cached by input and
    package hashes, so changing canonical lists invalidates the cache.

    Args:
        input_path: Original applicant JSON array.
        output_path: Destination for records with added standard fields.
        package: Directory containing the actual instructor app.py.
        batch_size: Records per restartable local-model invocation.
        python: Interpreter with the model dependencies installed.

    Returns:
        Number of standardized applicant records saved.

    Raises:
        FileNotFoundError: The supplied package is absent.
        ValueError: Input or model output fails validation.
        RuntimeError: The supplied model process fails.
    """

    package = package.resolve()
    app = package / "app.py"
    if not app.is_file():
        raise FileNotFoundError(
            "Missing instructor package: llm_hosting/app.py. "
            "Download Canvas file 19121115, extract into llm_hosting, "
            "and follow its README."
        )
    if batch_size < 1:
        raise ValueError("batch_size must be positive")
    records = load_data(input_path)
    if not records:
        raise ValueError(
            "No applicant records to normalize; collect real records first."
        )
    package_hash = hashlib.sha256()
    model_configuration = {
        key: os.environ.get(key, default)
        for key, default in {
            "MODEL_REPO": "TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF",
            "MODEL_FILE": "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf",
            "N_CTX": "2048",
            "CANON_UNIS_PATH": "canon_universities.txt",
            "CANON_PROGS_PATH": "canon_programs.txt",
        }.items()
    }
    package_hash.update(
        json.dumps(model_configuration, sort_keys=True).encode()
    )
    for path in sorted(package.rglob("*")):
        if (
            path.is_file()
            and path.suffix
            in {".py", ".json", ".txt", ".csv", ".yaml", ".yml"}
            and not any(
                part in {".venv", "venv", "__pycache__", "models", ".cache"}
                for part in path.relative_to(package).parts
            )
        ):
            package_hash.update(str(path.relative_to(package)).encode())
            package_hash.update(path.read_bytes())
    cache = output_path.parent / ".llm_cache"
    cache.mkdir(parents=True, exist_ok=True)
    extended = []
    for start in range(0, len(records), batch_size):
        batch = records[start : start + batch_size]
        key = hashlib.sha256(
            (
                package_hash.hexdigest() + json.dumps(batch, sort_keys=True)
            ).encode()
        ).hexdigest()
        cached = cache / f"{key}.json"
        if cached.exists():
            candidates = load_data(cached)
        else:
            with tempfile.TemporaryDirectory(prefix="gradcafe-llm-") as temp:
                batch_path = Path(temp) / "input.json"
                save_data(batch, batch_path)
                result = subprocess.run(
                    [
                        python,
                        "-X",
                        "utf8",
                        str(app),
                        "--file",
                        str(batch_path),
                        "--stdout",
                    ],
                    cwd=package,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    check=False,
                )
                if result.returncode:
                    raise RuntimeError(
                        f"Local LLM failed (exit {result.returncode}):\n"
                        f"{result.stderr[-4000:]}"
                    )
                try:
                    candidates = json.loads(result.stdout)
                    if isinstance(candidates, dict):
                        candidates = [candidates]
                except json.JSONDecodeError:
                    try:
                        candidates = [
                            json.loads(line)
                            for line in result.stdout.splitlines()
                            if line.strip()
                        ]
                    except json.JSONDecodeError as exc:
                        raise ValueError(
                            "llm_hosting/app.py must print JSON/JSONL "
                            "to stdout; send diagnostic logs to stderr."
                        ) from exc
        if not isinstance(candidates, list) or len(candidates) != len(batch):
            raise ValueError(
                "LLM changed the number of records; output was not accepted."
            )
        merged_batch = []
        for original, candidate in zip(batch, candidates):
            if not isinstance(candidate, dict) or candidate.get(
                "program"
            ) != original.get("program"):
                raise ValueError(
                    "LLM changed original program text or record order; "
                    "output was not accepted."
                )
            for key in ("url", "raw_program"):
                if key in original and candidate.get(key) != original.get(key):
                    raise ValueError(
                        f"LLM changed {key}; output was not accepted."
                    )
            merged = copy.deepcopy(original)
            for field in LLM_FIELDS:
                value = candidate.get(field)
                if (
                    not isinstance(value, (str, type(None)))
                    or field not in candidate
                ):
                    raise ValueError(
                        f"LLM output is missing a valid {field} field."
                    )
                merged[field] = text_value(value)
            merged_batch.append(merged)
        save_data(merged_batch, cached)
        extended.extend(merged_batch)
        print(
            f"Standardized {len(extended)}/{len(records)} records",
            file=sys.stderr,
        )
    save_data(extended, output_path)
    return len(extended)


def main() -> int:
    """Run the local standardization CLI and return an exit code."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--file", type=Path, default=Path("applicant_data.json")
    )
    parser.add_argument(
        "--output", type=Path, default=Path("llm_extend_applicant_data.json")
    )
    parser.add_argument("--llm-dir", type=Path, default=Path("llm_hosting"))
    parser.add_argument("--batch-size", type=int, default=100)
    parser.add_argument(
        "--python",
        default=sys.executable,
        help="Python interpreter with the supplied LLM dependencies installed",
    )
    args = parser.parse_args()
    try:
        count = extend_with_llm(
            args.file, args.output, args.llm_dir, args.batch_size, args.python
        )
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"Cleaning stopped: {exc}", file=sys.stderr)
        return 1
    print(f"Saved {count} locally standardized records to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
