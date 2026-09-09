"""Collect permitted GradCafe results or import saved browser HTML."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urljoin, urlparse, urlunparse
from urllib.request import HTTPRedirectHandler, Request, build_opener
from urllib.robotparser import RobotFileParser

from bs4 import BeautifulSoup
from clean import clean_data, text_value
from comment_scores import enrich_scores
import storage
from storage import save_json as _save_json

BASE_URL = "https://www.thegradcafe.com/"
USER_AGENT = "JHU-Module2-EducationalScraper/1.0"
PARSER_SCHEMA_VERSION = 4
SCORE_FIELDS = {"gre", "gre_v", "gre_aw", "gre_quantitative", "gpa"}


def _validate_checkpoint_schema(records: list[dict], source: Path) -> None:
    """Reject stale/mixed score schemas before any recovery writes."""
    for record in records:
        provenance = record.get("score_provenance")
        narrative_schema_valid = isinstance(
            record.get("comment_score_mentions"), list
        ) and isinstance(record.get("score_context"), dict)
        if (
            "gre_quantitative" not in record
            or not narrative_schema_valid
            or not isinstance(provenance, dict)
            or set(provenance) != SCORE_FIELDS
            or any(
                value
                not in {
                    None,
                    "structured_badge",
                    "comment_explicit_declaration",
                    "comment_labeled_narrative",
                }
                for value in provenance.values()
            )
        ):
            raise ValueError(
                f"Incompatible checkpoint schema in {source}. "
                "Replay saved HTML into new output/raw paths before resuming; "
                "old and new score schemas must not be mixed."
            )


def _declared_comment_gre(comment: str | None) -> dict:
    """Read a complete labeled score declaration, never narrative mentions.

    Quantitative is a distinct metric; it is not an inferred total GRE score.
    Anchoring the whole comment excludes historical or third-party prose.
    """
    if comment is None:
        return {}
    match = re.fullmatch(
        r"GRE\s*,\s*Quantitative\s*:\s*(\d+(?:\.\d+)?)\s*,\s*"
        r"Verbal\s*:\s*(\d+(?:\.\d+)?)\s*,\s*"
        r"Analytical Writing\s*:\s*(\d+(?:\.\d+)?)\s*\.?",
        comment.strip(),
        re.IGNORECASE,
    )
    if match is None:
        return {}
    return dict(zip(("gre_quantitative", "gre_v", "gre_aw"), match.groups()))


class ScrapingStopped(RuntimeError):
    """A restriction, unexpected response, or unsafe page stops collection."""


def save_data(
    data: list[dict], filename: str | Path = "applicant_data.json"
) -> None:
    """Atomically save applicant records to a UTF-8 JSON array.

    Args:
        data: Applicant dictionaries to serialize.
        filename: Destination path relative to the working directory.
    """
    storage.save_data(data, filename)


def load_data(filename: str | Path = "applicant_data.json") -> list[dict]:
    """Load a validated JSON array of applicant dictionaries.

    Args:
        filename: Input JSON path.

    Returns:
        Applicant records without modifying source values.
    """
    return storage.load_data(filename)


def result_url(page: int) -> str:
    """Construct a legacy page URL; live collection follows actual Next links.

    Args:
        page: Positive legacy page number.

    Returns:
        A public HTTPS GradCafe survey URL.
    """
    if page < 1:
        raise ValueError("Page numbers start at 1")
    return urlunparse(
        (
            "https",
            "www.thegradcafe.com",
            "/survey/",
            "",
            urlencode({"page": page}),
            "",
        )
    )


def validate_public_url(url: str) -> str:
    """Validate a public results or robots URL and remove its fragment.

    Args:
        url: Absolute URL to inspect.

    Returns:
        The validated URL without a fragment.

    Raises:
        ScrapingStopped: The URL leaves the permitted public site paths.
    """
    parsed = urlparse(url)
    if (
        parsed.scheme != "https"
        or parsed.hostname not in {"thegradcafe.com", "www.thegradcafe.com"}
        or parsed.username
        or parsed.password
        or parsed.port not in {None, 443}
    ):
        raise ScrapingStopped(
            f"Refusing a URL outside the public HTTPS GradCafe site: {url}"
        )
    if parsed.path not in {
        "/robots.txt",
        "/survey",
        "/survey/",
    } and not re.fullmatch(r"/result/\d+/?", parsed.path):
        raise ScrapingStopped(f"Refusing a non-results URL: {url}")
    return urlunparse(parsed._replace(fragment=""))


class _CheckedRedirect(HTTPRedirectHandler):
    def __init__(self, allowed):
        self.allowed = allowed

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        self.allowed(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class GradCafeScraper:
    """Checkpoint collection progress and stop on rejected requests."""

    def __init__(
        self,
        output: str | Path = "applicant_data.json",
        raw_dir: str | Path = "raw",
        delay: float = 6.0,
        timeout: float = 30.0,
    ):
        if delay < 2:
            raise ValueError(
                "Use a delay of at least 2 seconds; the default is 6 seconds."
            )
        self.output, self.raw_dir = Path(output), Path(raw_dir)
        self.delay, self.timeout = delay, timeout
        self.state_path = self.raw_dir / "checkpoint.json"
        self.robots = None
        self.last_request = 0.0
        self.state = {
            "parser_schema_version": PARSER_SCHEMA_VERSION,
            "completed_pages": {},
            "stop_reason": None,
            "updated_at": None,
            "next_url": urljoin(BASE_URL, "survey/"),
        }
        if self.state_path.exists():
            self.state.update(
                json.loads(self.state_path.read_text(encoding="utf-8"))
            )
        self.records = load_data(self.output) if self.output.exists() else []
        _validate_checkpoint_schema(self.records, self.output)
        version = self.state.get("parser_schema_version")
        if version != PARSER_SCHEMA_VERSION:
            raise ValueError(
                f"Checkpoint parser schema {version} is incompatible with "
                f"version {PARSER_SCHEMA_VERSION}; replay saved HTML into "
                "new output/raw paths."
            )
        self.seen = {row["url"] for row in self.records if row.get("url")}
        # Replay journals after interrupted aggregate/checkpoint writes.
        recovered = False
        journals = [
            (journal, json.loads(journal.read_text(encoding="utf-8")))
            for journal in sorted(self.raw_dir.glob("page-*.json"))
        ]
        # Preflight every journal before recovering even the first record.
        for journal, entry in journals:
            _validate_checkpoint_schema(entry["records"], journal)
            if (
                entry.get("parser_schema_version", PARSER_SCHEMA_VERSION)
                != PARSER_SCHEMA_VERSION
            ):
                raise ValueError(f"Incompatible parser schema in {journal}")
        for _, entry in journals:
            for record in entry["records"]:
                if record["url"] not in self.seen:
                    self.records.append(record)
                    self.seen.add(record["url"])
                    recovered = True
            page = str(entry["page"])
            if page not in self.state["completed_pages"]:
                self.state["completed_pages"][page] = entry["manifest"]
                recovered = True
        if recovered:
            last_page = max(self.state["completed_pages"], key=int)
            self.state["next_url"] = self.state["completed_pages"][
                last_page
            ].get("next_url")
            save_data(self.records, self.output)
            self._checkpoint()
        if self.state["completed_pages"] and not self.records:
            raise ValueError(
                "Checkpoint exists but records/journals are missing. "
                "Rebuild into a new directory from saved HTML."
            )

    def _checkpoint(self) -> None:
        self.state["updated_at"] = datetime.now(timezone.utc).isoformat()
        _save_json(self.state, self.state_path)

    def record_stop(self, reason: str) -> None:
        """Persist a stop reason so a blocked live run cannot retry itself.

        Args:
            reason: The rejection or error that stopped the collector.
        """
        self.state["stop_reason"] = reason
        self._checkpoint()

    def ensure_live_allowed(self) -> None:
        """Refuse new live operations after a saved rejection or block.

        Offline replay into separate paths remains possible. This method never
        clears the saved stop or treats a browser transport as authorization.
        """
        if self.state.get("stop_reason"):
            raise ScrapingStopped(
                "A previous live run stopped: "
                + self.state["stop_reason"]
                + " No automatic retry is permitted. Review the restriction "
                "before any separately authorized collection."
            )

    def resolve_parser_stop(self, resolution: str) -> None:
        """Clear only a reviewed parser-layout stop after offline validation.

        Access denials, challenges, rate limits, and transport failures cannot
        be cleared through this method.
        """
        reason = self.state.get("stop_reason")
        if not reason or not reason.startswith(
            "Unrecognized applicant row layout"
        ):
            raise ValueError("Current stop is not a parser-layout review stop")
        history = self.state.setdefault("stop_history", [])
        history.append(
            {
                "time": self.state.get("updated_at"),
                "reason": reason,
                "resolution": resolution,
            }
        )
        self.state["stop_reason"] = None
        self._checkpoint()

    def resolve_browser_transport_stop(self, resolution: str) -> None:
        """Clear a reviewed local Chrome connection failure only.

        This recovery is intentionally limited to Windows error 10054 and the
        WebSocket client's exact remote-host-loss message. Both indicate that
        the local Chrome DevTools socket closed. HTTP errors, access
        challenges, rate limits, policy stops, and other failures must remain
        blocking.

        Args:
            resolution: Human-readable evidence supporting the reviewed retry.

        Raises:
            ValueError: The saved stop is not the recognized transport error,
                or no review evidence was supplied.
        """
        reason = self.state.get("stop_reason")
        is_windows_socket_reset = bool(
            reason
            and "[WinError 10054]" in reason
            and "connection was forcibly closed" in reason.lower()
        )
        is_websocket_disconnect = (
            reason == "Connection to remote host was lost."
        )
        is_known_transport_stop = (
            is_windows_socket_reset or is_websocket_disconnect
        )
        if not is_known_transport_stop:
            raise ValueError(
                "Current stop is not the reviewed Chrome transport failure"
            )
        if not resolution.strip():
            raise ValueError("Transport recovery requires review evidence")
        history = self.state.setdefault("stop_history", [])
        history.append(
            {
                "time": self.state.get("updated_at"),
                "reason": reason,
                "resolution": resolution,
                "type": "reviewed_browser_transport_recovery",
            }
        )
        self.state["stop_reason"] = None
        self._checkpoint()

    def resolve_atomic_save_stop(self, resolution: str) -> None:
        """Clear a reviewed Windows lock on this collection's output file.

        The saved temporary-file replacement pattern must name the configured
        output on both sides. Website, parser, policy, and general filesystem
        failures cannot be cleared through this recovery path.
        """
        reason = self.state.get("stop_reason") or ""
        output_name = self.output.name.lower()
        lowered = reason.lower()
        is_output_lock = (
            reason.startswith("[WinError 5] Access is denied:")
            and f".{output_name}." in lowered
            and f"-> '{output_name}'" in lowered
        )
        if not is_output_lock:
            raise ValueError(
                "Current stop is not a reviewed atomic output-save lock"
            )
        if not resolution.strip():
            raise ValueError("Save recovery requires review evidence")
        self.state.setdefault("stop_history", []).append(
            {
                "time": self.state.get("updated_at"),
                "reason": reason,
                "resolution": resolution,
                "type": "reviewed_atomic_save_recovery",
            }
        )
        self.state["stop_reason"] = None
        self._checkpoint()

    def _allowed(self, url: str) -> None:
        validate_public_url(url)
        if urlparse(url).path != "/robots.txt" and (
            self.robots is None or not self.robots.can_fetch(USER_AGENT, url)
        ):
            raise ScrapingStopped(
                f"robots.txt does not permit this request: {url}"
            )

    def _request(self, url: str) -> tuple[bytes, str]:
        self.ensure_live_allowed()
        self._allowed(url)
        remaining = self.delay - (time.monotonic() - self.last_request)
        if remaining > 0:
            time.sleep(remaining)
        request = Request(
            url,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "text/html,text/plain;q=0.9",
            },
        )
        self.last_request = time.monotonic()
        try:
            with build_opener(_CheckedRedirect(self._allowed)).open(
                request, timeout=self.timeout
            ) as response:
                self._allowed(response.url)
                content_type = response.headers.get_content_type()
                if content_type not in {
                    "text/html",
                    "text/plain",
                    "application/xhtml+xml",
                }:
                    raise ScrapingStopped(
                        f"Unexpected content type {content_type} for {url}"
                    )
                return response.read(), response.url
        except HTTPError as exc:
            raise ScrapingStopped(
                f"HTTP {exc.code} for {url}. "
                "No retries; stop and inspect the restriction."
            ) from exc
        except (URLError, TimeoutError) as exc:
            raise ScrapingStopped(
                f"Request failed for {url}: {exc}. Saved progress is retained."
            ) from exc

    def check_robots(self, saved_file: Path | None = None) -> None:
        """Fetch robots.txt or inspect an explicitly supplied browser copy.

        Args:
            saved_file: Optional saved public policy; otherwise request it.

        Raises:
            ScrapingStopped: The policy is unreadable or denies results.
        """
        source = urljoin(BASE_URL, "robots.txt")
        if saved_file:
            payload = saved_file.read_bytes()
            method = f"user-supplied saved robots file: {saved_file.name}"
        else:
            payload, source = self._request(source)
            method = "urllib"
        text = payload.decode("utf-8-sig", errors="replace")
        if "<html" in text.lower() or "user-agent:" not in text.lower():
            raise ScrapingStopped(
                "robots.txt is not a readable robots policy; "
                "scraping is not authorized."
            )
        self.robots = RobotFileParser(source)
        self.robots.parse(text.splitlines())
        self._allowed(result_url(1))
        self.delay = max(self.delay, self.robots.crawl_delay(USER_AGENT) or 0)
        rate = self.robots.request_rate(USER_AGENT)
        if rate and rate.requests:
            self.delay = max(self.delay, rate.seconds / rate.requests)
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        (self.raw_dir / "robots.txt").write_bytes(payload)
        _save_json(
            {
                "source_url": source,
                "checked_at": datetime.now(timezone.utc).isoformat(),
                "method": method,
                "user_agent": USER_AGENT,
                "allowed_results": True,
                "sha256": hashlib.sha256(payload).hexdigest(),
                "delay_seconds": self.delay,
            },
            self.raw_dir / "robots_check.json",
        )

    @staticmethod
    def _parse_entry(main_row, details, page_url: str) -> dict:
        cells = main_row.find_all("td", recursive=False)
        link = main_row.find("a", href=re.compile(r"(?:^|/)result/\d+"))
        if link is None:
            raise ValueError("Applicant row has no stable result link")
        url = validate_public_url(urljoin(page_url, link["href"]))
        university = (
            text_value(cells[0].get_text(" ", strip=True)) if cells else None
        )
        program_cell = cells[1] if len(cells) > 1 else None
        program_node = (
            program_cell.find(["span", "h6", "strong"])
            if program_cell
            else None
        )
        program = (
            text_value(
                (program_node or program_cell).get_text(" ", strip=True)
            )
            if program_cell
            else None
        )
        if len(cells) < 4 or program_cell is None or not university:
            raise ValueError(
                "Unrecognized applicant row layout; "
                "refusing to silently discard fields"
            )
        date_added = text_value(cells[2].get_text(" ", strip=True))
        decision = text_value(cells[3].get_text(" ", strip=True))
        # Only detail chips, excluding comments, supply academic metrics.
        detail_soup = BeautifulSoup(
            "".join(str(row) for row in details), "html.parser"
        )
        comment_nodes = detail_soup.select(
            ".comment, .comments, [data-role='comment']"
        )
        if not comment_nodes:
            comment_nodes = detail_soup.find_all("p")
        comments = text_value(
            "\n".join(node.get_text(" ", strip=True) for node in comment_nodes)
        )
        for node in comment_nodes:
            node.decompose()
        metadata = detail_soup.get_text(" ", strip=True)
        status_match = re.search(
            r"\b(Accepted|Rejected|Wait\s*listed|Interview|Other)\b",
            decision or "",
            re.I,
        )
        status = (
            status_match.group(1).title().replace("Wait Listed", "Waitlisted")
            if status_match
            else decision
        )
        date_match = re.search(
            r"\bon\s+(.+?)(?:\s+(?:via|at)\b|$)", decision or "", re.I
        )
        decision_date = text_value(date_match.group(1)) if date_match else None
        term_match = re.search(
            r"\b(Fall|Spring|Summer|Winter)\s+(\d{4})\b", metadata, re.I
        )
        citizenship = next(
            (
                text
                for node in detail_soup.find_all(["div", "span"])
                if (text := node.get_text(" ", strip=True))
                in {"International", "American", "Domestic", "Other"}
            ),
            None,
        )
        degree_match = re.search(
            r"\b(Ph\.?\s?D\.?|Doctorate|Masters?(?:['’]s)?|"
            r"M\.?S\.?|M\.?A\.?)\b",
            program_cell.get_text(" ", strip=True),
            re.I,
        )
        program_spans = program_cell.find_all("span")
        degree = (
            text_value(program_spans[1].get_text(" ", strip=True))
            if len(program_spans) > 1
            else None
        )
        if degree is None and degree_match:
            degree = degree_match.group(1)
        item = {
            "program": f"{program}, {university}" if program else None,
            "program_name": program,
            "university": university,
            "comments": comments,
            "date_added": date_added,
            "url": url,
            "status": status,
            "decision_date": decision_date,
            "acceptance_date": decision_date if status == "Accepted" else None,
            "rejection_date": decision_date if status == "Rejected" else None,
            "term": " ".join(term_match.groups()) if term_match else None,
            "citizenship": citizenship,
            "degree": degree,
            "raw_program": program_cell.get_text(" ", strip=True),
            "raw_text": "\n".join(
                row.get_text(" ", strip=True) for row in [main_row, *details]
            ),
            "source_url": page_url,
        }
        patterns = {
            "gpa": r"\bGPA\s*:?\s*(\d+(?:\.\d+)?)",
            "gre": r"\bGRE\s*:?\s*(\d+(?:\.\d+)?)",
            "gre_v": r"\bGRE\s*(?:V|Verbal)\s*:?\s*(\d+(?:\.\d+)?)",
            "gre_aw": (
                r"\bGRE\s*(?:AW|AWA|Analytical Writing)"
                r"\s*:?\s*(\d+(?:\.\d+)?)"
            ),
        }
        for key, pattern in patterns.items():
            match = re.search(pattern, metadata, re.I)
            item[key] = match.group(1) if match else None
        item["gre_quantitative"] = None
        item["score_provenance"] = {
            key: "structured_badge" if item[key] is not None else None
            for key in (*patterns, "gre_quantitative")
        }
        for key, value in _declared_comment_gre(comments).items():
            if item[key] is None:
                item[key] = value
                item["score_provenance"][key] = "comment_explicit_declaration"
        return enrich_scores(item)

    def parse_html(self, html: str, page_url: str) -> list[dict]:
        """Extract applicants from a visible public results table.

        Args:
            html: Source HTML captured from the public page.
            page_url: Actual source URL, including any cursor.

        Returns:
            Clean applicant dictionaries retaining their raw source text.

        Raises:
            ScrapingStopped: The page is blocked or has an unknown layout.
        """
        validate_public_url(page_url)
        soup = BeautifulSoup(html, "html.parser")
        title = (
            soup.title.get_text(" ", strip=True).lower() if soup.title else ""
        )
        if any(
            marker in title
            for marker in (
                "just a moment",
                "access denied",
                "verify you are human",
                "attention required",
            )
        ) or soup.select_one("#challenge-form, #cf-challenge-running"):
            raise ScrapingStopped(
                "Browser verification/block page detected. "
                "Complete normal verification manually; do not automate it."
            )
        entries = []
        for table in soup.find_all("table"):
            main_row, details = None, []
            for row in table.find_all("tr"):
                if row.find("a", href=re.compile(r"(?:^|/)result/\d+")):
                    if main_row is not None:
                        entries.append(
                            self._parse_entry(main_row, details, page_url)
                        )
                    main_row, details = row, []
                elif main_row is not None and row.find("td"):
                    details.append(row)
            if main_row is not None:
                entries.append(self._parse_entry(main_row, details, page_url))
        if not entries:
            raise ScrapingStopped(
                "No recognizable applicant table. "
                "The source may be blocked or its layout may have changed."
            )
        return clean_data(entries)

    @staticmethod
    def next_url(html: str, page_url: str) -> str | None:
        """Find the site's actual Next link, including cursor pagination.

        Args:
            html: Captured source HTML.
            page_url: The source page's absolute URL.

        Returns:
            An absolute Next URL, or None when no link exists.
        """
        soup = BeautifulSoup(html, "html.parser")
        for anchor in soup.find_all("a", href=True):
            label = " ".join(
                (
                    anchor.get_text(" ", strip=True),
                    anchor.get("aria-label", ""),
                )
            ).strip()
            if "next" in anchor.get("rel", []) or re.search(
                r"\bnext\b", label, re.I
            ):
                url = validate_public_url(urljoin(page_url, anchor["href"]))
                if urlparse(url).path.rstrip("/") != "/survey":
                    continue
                if url == page_url:
                    raise ScrapingStopped(
                        "Next link points to the current page; "
                        "pagination is stuck."
                    )
                return url
        return None

    def ingest(
        self,
        payload: bytes,
        page: int,
        source_url: str | None = None,
        method: str = "urllib",
    ) -> int:
        """Commit one source page and append previously unseen applicants.

        Args:
            payload: Original source HTML bytes.
            page: Sequential capture number, starting at one.
            source_url: Actual page URL; legacy callers may omit it.
            method: Human-readable acquisition method for the manifest.

        Returns:
            Number of newly added records.

        Raises:
            ScrapingStopped: Policy, identity, or pagination checks fail.
        """
        source_url = source_url or result_url(page)
        self._allowed(source_url)
        digest = hashlib.sha256(payload).hexdigest()
        prior = self.state["completed_pages"].get(str(page))
        if prior:
            if prior["sha256"] != digest:
                raise ScrapingStopped(
                    f"Page {page} differs from its archived capture; "
                    "retain the checkpoint or use a new collection directory."
                )
            return 0
        for number, info in self.state["completed_pages"].items():
            if info["sha256"] == digest:
                raise ScrapingStopped(
                    f"Page {page} repeats the HTML of page {number}; "
                    "pagination may be stuck."
                )
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        archive = self.raw_dir / f"page-{page:06d}.html"
        # Archive before parsing to retain unexpected HTML for debugging.
        archive.write_bytes(payload)
        decoded = payload.decode("utf-8-sig", errors="replace")
        entries = self.parse_html(decoded, source_url)
        next_page_url = self.next_url(decoded, source_url)
        if next_page_url:
            self._allowed(next_page_url)
        new = []
        for entry in entries:
            if entry["url"] not in self.seen:
                self.seen.add(entry["url"])
                new.append(entry)
        if not new:
            raise ScrapingStopped(
                f"Page {page} contains no new applicant URLs; "
                "stopped to prevent an endless repeat loop."
            )
        manifest = {
            "sha256": digest,
            "source_url": source_url,
            "captured_at": datetime.now(timezone.utc).isoformat(),
            "method": method,
            "parsed_count": len(entries),
            "new_count": len(new),
            "archive": archive.name,
            "next_url": next_page_url,
        }
        _save_json(
            {
                "page": page,
                "manifest": manifest,
                "records": entries,
                "parser_schema_version": PARSER_SCHEMA_VERSION,
            },
            self.raw_dir / f"page-{page:06d}.json",
        )
        self.records.extend(new)
        save_data(self.records, self.output)
        self.state["completed_pages"][str(page)] = manifest
        self.state["next_url"] = next_page_url
        self._checkpoint()
        return len(new)

    def scrape_data(
        self, target: int = 30000, max_pages: int = 5000
    ) -> list[dict]:
        """Collect permitted pages until the target or a stop is reached.

        Args:
            target: Minimum desired number of unique applicant records.
            max_pages: Maximum sequential captures to consider.

        Returns:
            All committed applicant records, possibly below the target.
        """
        self.ensure_live_allowed()
        try:
            self.check_robots()
            for page in range(1, max_pages + 1):
                if len(self.records) >= target:
                    break
                if str(page) in self.state["completed_pages"]:
                    continue
                url = self.state.get("next_url")
                if not url:
                    break
                archive = self.raw_dir / f"page-{page:06d}.html"
                if archive.exists():
                    payload = archive.read_bytes()
                else:
                    payload, url = self._request(url)
                added = self.ingest(payload, page, url)
                print(
                    f"Page {page}: +{added}; "
                    f"{len(self.records)}/{target} applicants",
                    flush=True,
                )
            return self.records
        except (ScrapingStopped, ValueError) as exc:
            self.state["stop_reason"] = str(exc)
            self._checkpoint()
            raise


def scrape_data(**kwargs) -> list[dict]:
    """Collect using default files and keyword target/max_pages arguments."""
    return GradCafeScraper().scrape_data(**kwargs)


def main() -> int:
    """Run the collection CLI and return its completion/error exit code."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=Path("applicant_data.json")
    )
    parser.add_argument("--raw-dir", type=Path, default=Path("raw"))
    parser.add_argument("--target", type=int, default=30000)
    parser.add_argument("--max-pages", type=int, default=5000)
    parser.add_argument("--delay", type=float, default=6)
    parser.add_argument(
        "--html-dir",
        type=Path,
        help="Import page-NNNNNN.html from manually verified public pages",
    )
    parser.add_argument(
        "--robots-file",
        type=Path,
        help="Saved real robots.txt; required with --html-dir",
    )
    args = parser.parse_args()
    try:
        if args.target < 1 or args.max_pages < 1:
            raise ValueError("Target and max-pages must be positive")
        scraper = GradCafeScraper(args.output, args.raw_dir, args.delay)
        if args.html_dir:
            if not args.robots_file:
                raise ValueError(
                    "--html-dir requires --robots-file "
                    "from the public robots.txt page"
                )
            scraper.check_robots(args.robots_file)
            captures = sorted(
                (int(match.group(1)), path)
                for path in args.html_dir.glob("*.html")
                if (match := re.fullmatch(r"page-(\d+)\.html", path.name))
            )
            if not captures:
                raise ValueError("No page-NNNNNN.html captures found")
            for page, path in captures:
                if len(scraper.records) >= args.target:
                    break
                # Sidecars preserve cursors; filenames name capture sequence.
                sidecar = path.with_suffix(".meta.json")
                metadata = (
                    json.loads(sidecar.read_text(encoding="utf-8"))
                    if sidecar.exists()
                    else {}
                )
                source_url = metadata.get("source_url") or scraper.state.get(
                    "next_url"
                )
                if not source_url:
                    raise ValueError(
                        f"Missing source URL for {path.name}; "
                        "provide its .meta.json sidecar"
                    )
                added = scraper.ingest(
                    path.read_bytes(),
                    page,
                    source_url,
                    method="saved public browser HTML",
                )
                print(
                    f"Page {page}: +{added}; "
                    f"{len(scraper.records)}/{args.target} applicants"
                )
        else:
            scraper.scrape_data(args.target, args.max_pages)
        if len(scraper.records) < args.target:
            print(
                f"INCOMPLETE: {len(scraper.records)} genuine records; "
                f"target is {args.target}. Saved progress can be resumed.",
                file=sys.stderr,
            )
            return 2
        print(
            f"Saved {len(scraper.records)} applicant records in {args.output}"
        )
        return 0
    except (OSError, ValueError, ScrapingStopped) as exc:
        print(f"Collection stopped: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
