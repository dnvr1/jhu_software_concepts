"""Run one safe Module 2 scrape and append new applicants to PostgreSQL."""

from __future__ import annotations

from datetime import datetime, timezone
import os
from pathlib import Path
from threading import Event, Lock, Thread
from typing import Callable
from uuid import uuid4

from sqlalchemy.dialects.postgresql import insert

from load_data import COLUMNS, normalize_record
import models
from scrape import GradCafeScraper


RUNTIME_ROOT = Path(__file__).with_name("runtime") / "pull_data"


def collect_current_entries() -> list[dict]:
    """Reuse the Module 2 scraper to collect the newest public results page.

    Creates a unique capture directory under SCRAPE_RUN_ROOT. SCRAPE_DELAY
    and SCRAPE_MAX_PAGES configure pacing and the maximum page count.

    Returns:
        Cleaned records from the first complete permitted page.

    Raises:
        ValueError: Delay/page settings are invalid.
        scrape.ScrapingStopped: Site policy or a response blocks collection.
        OSError: Capture evidence cannot be persisted.
    """
    run_name = (
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        + "-"
        + uuid4().hex[:8]
    )
    run_directory = Path(
        os.getenv("SCRAPE_RUN_ROOT", str(RUNTIME_ROOT))
    ) / run_name
    output = run_directory / "applicant_data.json"
    raw_directory = run_directory / "raw"
    delay = float(os.getenv("SCRAPE_DELAY", "6"))
    max_pages = int(os.getenv("SCRAPE_MAX_PAGES", "1"))
    if max_pages < 1:
        raise ValueError("SCRAPE_MAX_PAGES must be at least 1")

    scraper = GradCafeScraper(output, raw_directory, delay=delay)
    # A fresh run starts at the current results page. A target of one means
    # the complete first page is committed, without walking old pagination.
    return scraper.scrape_data(target=1, max_pages=max_pages)


def prepare_mappings(records: list[dict]) -> tuple[list[dict], int]:
    """Normalize usable records and skip malformed or repeated source URLs.

    Args:
        records: Scraped applicant dictionaries; originals are not mutated.

    Returns:
        Database column mappings and the number of malformed or repeated
        records skipped within this batch. Existing DB rows are not checked.
    """
    mappings: list[dict] = []
    seen_urls: set[object] = set()
    rejected = 0
    url_index = COLUMNS.index("url")

    for record in records:
        try:
            row = normalize_record(record)
        except (TypeError, ValueError):
            rejected += 1
            continue
        url = row[url_index]
        if url in seen_urls:
            rejected += 1
            continue
        seen_urls.add(url)
        mappings.append(dict(zip(COLUMNS, row)))
    return mappings, rejected


def insert_new_records(records: list[dict]) -> tuple[int, int]:
    """Insert unseen URLs atomically and return inserted/rejected counts.

    Args:
        records: Scraped applicant dictionaries to normalize and insert.

    Returns:
        Inserted count and input-rejection count. Conflicts with existing
        database URLs are skipped, but do not increment the rejection count.

    Raises:
        sqlalchemy.exc.SQLAlchemyError: The transaction cannot complete.
    """
    mappings, rejected = prepare_mappings(records)
    if not mappings:
        return 0, rejected

    # The unique URL constraint resolves races between concurrent processes;
    # a Python-only existence check would not make insertion idempotent.
    statement = (
        insert(models.Applicant)
        .values(mappings)
        .on_conflict_do_nothing(index_elements=[models.Applicant.url])
        .returning(models.Applicant.p_id)
    )
    with models.SessionLocal.begin() as session:  # pylint: disable=no-member
        inserted = len(session.scalars(statement).all())
    return inserted, rejected


class ScrapeJobManager:
    """Coordinate one background scrape and expose a serializable status."""

    def __init__(
        self,
        collector: Callable[[], list[dict]] = collect_current_entries,
        loader: Callable[[list[dict]], tuple[int, int]] = insert_new_records,
    ) -> None:
        """Initialize injectable work functions and an idle status snapshot.

        Args:
            collector: No-argument callable returning applicant dictionaries.
            loader: Callable accepting those records and returning the
                inserted and rejected counts. Exceptions become job failures.
        """
        self._collector = collector
        self._loader = loader
        self._lock = Lock()
        self._state_lock = Lock()
        self._finished = Event()
        self._finished.set()
        self._state = {
            "status": "idle",
            "message": "No Pull Data request is currently running.",
            "started_at": None,
            "finished_at": None,
            "records_found": 0,
            "records_inserted": 0,
            "records_rejected": 0,
        }

    def snapshot(self) -> dict:
        """Return a copy that Flask can safely render or serialize.

        Returns:
            A lock-protected shallow copy of scalar job-state fields, so
            callers cannot mutate the manager's internal state dictionary.
        """
        with self._state_lock:
            return dict(self._state)

    def start(self) -> tuple[bool, dict]:
        """Start one worker, refusing a second request while it is active.

        Returns:
            A started flag and status snapshot. A false flag means another
            thread already holds the job lock; no second scrape is started.
        """
        # Ownership intentionally spans threads: start acquires the job lock,
        # and the worker releases it in finally. A with block would end early.
        if not self._lock.acquire(  # pylint: disable=consider-using-with
            blocking=False
        ):
            return False, self.snapshot()

        self._finished.clear()
        started_at = datetime.now(timezone.utc).isoformat()
        with self._state_lock:
            self._state.update(
                status="running",
                message=(
                    "Pull Data is checking GradCafe for newly submitted "
                    "application results. This may take some time."
                ),
                started_at=started_at,
                finished_at=None,
                records_found=0,
                records_inserted=0,
                records_rejected=0,
            )
        Thread(target=self._run, name="pull-data", daemon=True).start()
        return True, self.snapshot()

    def wait(self, timeout: float | None = None) -> bool:
        """Wait for the active job without polling or arbitrary sleeps.

        Args:
            timeout: Maximum seconds to wait, or None to wait indefinitely.

        Returns:
            True when finished (including failed jobs), or False on timeout.
        """
        return self._finished.wait(timeout)

    def _run(self) -> None:
        """Collect, insert, and publish the outcome of an accepted job.

        Worker exceptions are converted into a failed status because they
        cannot propagate to the initiating HTTP request. The finally block
        releases the job lock and wakes waiters for either outcome.
        """
        try:
            records = self._collector()
            inserted, rejected = self._loader(records)
            duplicate_count = max(len(records) - rejected - inserted, 0)
            message = (
                f"Pull Data finished: {len(records)} records checked, "
                f"{inserted} new records added"
            )
            if duplicate_count:
                message += f", and {duplicate_count} existing records skipped"
            if rejected:
                message += f". {rejected} unusable records were ignored"
            message += "."
            with self._state_lock:
                self._state.update(
                    status="succeeded",
                    message=message,
                    finished_at=datetime.now(timezone.utc).isoformat(),
                    records_found=len(records),
                    records_inserted=inserted,
                    records_rejected=rejected,
                )
        except Exception as error:  # pylint: disable=broad-exception-caught
            with self._state_lock:
                self._state.update(
                    status="failed",
                    message=f"Pull Data stopped: {error}",
                    finished_at=datetime.now(timezone.utc).isoformat(),
                )
        finally:
            self._lock.release()
            self._finished.set()


scrape_manager = ScrapeJobManager()
