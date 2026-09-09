"""Offline checks for isolated process orchestration and ordered merging."""

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from parallel_clean import run_batches, validate


def test_validation_rejects_changes_and_missing_names():
    source = [{"program": "Example", "url": "example/1"}]
    with pytest.raises(ValueError):
        validate(source, [])
    with pytest.raises(ValueError):
        validate(source, [{"program": "Changed"}])
    with pytest.raises(ValueError):
        validate(source, source)


def test_parallel_merge_keeps_order_and_separate_outputs(tmp_path):
    source = [
        {"program": f"Example {i}", "url": f"example/{i}"} for i in range(5)
    ]

    def fake_run(command, **kwargs):
        assert kwargs["env"]["N_THREADS"] == "2"
        input_path = Path(command[command.index("--file") + 1])
        output_path = Path(command[command.index("--output") + 1])
        rows = json.loads(input_path.read_text(encoding="utf-8"))
        for row in rows:
            row.update(
                {
                    "llm-generated-program": row["program"],
                    "llm-generated-university": "Example University",
                }
            )
        output_path.write_text(json.dumps(rows), encoding="utf-8")
        return SimpleNamespace(returncode=0)

    with (
        patch("parallel_clean.subprocess.run", side_effect=fake_run),
        patch("parallel_clean.os.cpu_count", return_value=8),
    ):
        _, output = run_batches(source, tmp_path, 2, 2, batch_size=2)
    assert [r["url"] for r in output] == [r["url"] for r in source]
    assert len(list(tmp_path.glob("batch-*/output.json"))) == 3
    assert (tmp_path / "merged.json").exists()


def test_failed_worker_never_publishes_aggregate(tmp_path):
    with patch(
        "parallel_clean.subprocess.run",
        return_value=SimpleNamespace(returncode=1, stderr="failed"),
    ):
        with pytest.raises(RuntimeError):
            run_batches([{"program": "Example"}], tmp_path, 1, 1)
    assert not (tmp_path / "merged.json").exists()


def test_cpu_oversubscription_rejected(tmp_path):
    with patch("parallel_clean.os.cpu_count", return_value=4):
        with pytest.raises(ValueError):
            run_batches([{}], tmp_path, 2, 4)
