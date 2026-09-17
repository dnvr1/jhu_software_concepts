"""Migrate saved evidence into fresh journals without website requests."""

import argparse
import hashlib
import json
from pathlib import Path

from scrape import GradCafeScraper


def main():
    """Replay exact archived URLs and HTML into a new output directory."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path("raw"))
    parser.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args()
    if args.destination.exists():
        raise ValueError(
            "Use a fresh destination; existing progress is never overwritten"
        )
    checkpoint = json.loads(
        (args.source / "checkpoint.json").read_text(encoding="utf-8")
    )
    collector = GradCafeScraper(
        args.destination / "applicant_data.json", args.destination / "raw"
    )
    collector.check_robots(args.source / "robots.txt")
    for path in sorted(args.source.glob("page-*.json")):
        entry = json.loads(path.read_text(encoding="utf-8"))
        manifest = entry["manifest"]
        payload = (args.source / manifest["archive"]).read_bytes()
        if hashlib.sha256(payload).hexdigest() != manifest["sha256"]:
            raise ValueError("Source HTML hash mismatch; migration stopped")
        collector.ingest(
            payload,
            entry["page"],
            manifest["source_url"],
            method="offline schema migration from saved HTML",
        )
    for key in ("stop_history", "local_recovery_note"):
        if key in checkpoint:
            collector.state[key] = checkpoint[key]
    if checkpoint.get("stop_reason"):
        collector.record_stop(checkpoint["stop_reason"])
    else:
        collector._checkpoint()  # pylint: disable=protected-access
    print(f"Replayed {len(collector.records)} records offline")


if __name__ == "__main__":
    main()
