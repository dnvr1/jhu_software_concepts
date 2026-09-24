"""Shared atomic JSON persistence for collection and local standardization."""

import json
import os
from pathlib import Path
import tempfile
import time


REPLACE_ATTEMPTS = 10
INITIAL_REPLACE_DELAY = 0.05


def _replace_with_retry(source: Path, destination: Path) -> None:
    """Replace a file despite brief Windows reader locks.

    A complete temporary file is retained between attempts. Only
    ``PermissionError`` is retried; unrelated filesystem failures remain
    immediately visible to the caller.
    """
    delay = INITIAL_REPLACE_DELAY
    for attempt in range(REPLACE_ATTEMPTS):
        try:
            os.replace(source, destination)
            return
        except PermissionError:
            if attempt == REPLACE_ATTEMPTS - 1:
                raise
            time.sleep(delay)
            delay = min(delay * 2, 0.5)


def save_json(data: object, filename: Path) -> None:
    """Replace a JSON file only after a complete UTF-8 write has succeeded.

    Args:
        data: JSON-compatible value to serialize.
        filename: Destination path, whose parent is created when needed.
    """
    filename.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=filename.parent,
            prefix=f".{filename.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            json.dump(
                data, handle, indent=2, ensure_ascii=False, allow_nan=False
            )
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        _replace_with_retry(temporary, filename)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def save_data(data: list[dict], filename: str | Path) -> None:
    """Save an applicant list using atomic JSON persistence.

    Args:
        data: Applicant records to save.
        filename: Destination JSON path.
    """
    save_json(data, Path(filename))


def load_data(filename: str | Path) -> list[dict]:
    """Load a JSON array and reject incompatible document shapes.

    Args:
        filename: Input UTF-8 JSON path.

    Returns:
        A list of applicant dictionaries.

    Raises:
        ValueError: The document is not an array of dictionaries.
    """
    with Path(filename).open(encoding="utf-8-sig") as handle:
        data = json.load(handle)
    if not isinstance(data, list) or any(
        not isinstance(row, dict) for row in data
    ):
        raise ValueError(
            f"{filename} must contain a JSON array of applicant objects"
        )
    return data
