"""Collect visible results from a normal, manually verified Chromium browser.

This optional helper attaches to a dedicated local debugging port. It never
solves challenges, changes browser protections, or retries rejected pages.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import sys
import time
from urllib.parse import urlparse
from urllib.request import urlopen

import websocket

from scrape import (
    BASE_URL,
    GradCafeScraper,
    ScrapingStopped,
    validate_public_url,
)


class BrowserPage:
    """A local CDP page with command IDs and document-rejection checks."""

    def __init__(self, socket_url: str):
        self.socket = websocket.create_connection(
            socket_url, timeout=30, suppress_origin=True
        )
        self.command_id = 0
        self.rejection = None
        self.command("Network.enable")

    def command(self, method: str, params: dict | None = None) -> dict:
        """Send a command while recording document-rejection events."""
        self.command_id += 1
        identifier = self.command_id
        self.socket.send(
            json.dumps(
                {"id": identifier, "method": method, "params": params or {}}
            )
        )
        while True:
            message = json.loads(self.socket.recv())
            if message.get("method") == "Network.responseReceived":
                event = message["params"]
                response = event["response"]
                if (
                    event.get("type") == "Document"
                    and response["status"] >= 400
                ):
                    self.rejection = (
                        f"HTTP {int(response['status'])}: {response['url']}"
                    )
            if message.get("id") == identifier:
                if "error" in message:
                    raise RuntimeError(str(message["error"]))
                return message.get("result", {})

    def evaluate(self, expression: str):
        """Read a page expression by value and surface JavaScript errors."""
        result = self.command(
            "Runtime.evaluate",
            {
                "expression": expression,
                "returnByValue": True,
            },
        )
        if "exceptionDetails" in result:
            raise RuntimeError(str(result["exceptionDetails"]))
        return result["result"].get("value")

    def snapshot(self) -> dict:
        """Read the currently displayed document and its actual URL."""
        value = self.evaluate(
            """(() => ({
            url: location.href,
            title: document.title,
            html: document.documentElement.outerHTML,
            text: document.body ? document.body.innerText : '',
            first: document.querySelector('table a[href*="/result/"]')?.href,
            ready: document.readyState,
            login_form: Array.from(document.querySelectorAll(
                'input[type="password"], form[action*="login"], '
                + 'form[action*="sign-in"], form[action*="signin"]'))
                .some(element => element.getClientRects().length),
            headings: Array.from(document.querySelectorAll('h1,h2'))
                .filter(element => element.getClientRects().length)
                .map(element => element.textContent.trim()),
            account_controls: Array.from(document.querySelectorAll(
                'header a, header button, nav a, nav button, '
                + '[role="navigation"] a, [role="navigation"] button, '
                + 'a[href*="logout"], a[href*="signout"], '
                + 'a[href*="sign-out"], form[action*="logout"]'))
                .filter(element => element.getClientRects().length
                    || /logout|signout|sign-out/i.test(
                        element.getAttribute('href')
                        || element.getAttribute('action') || ''))
                .map(element => ({text: element.textContent.trim(),
                    target: element.getAttribute('href')
                        || element.getAttribute('action') || ''})),
            authenticated_marker: Boolean(document.querySelector(
                '[data-authenticated="true"], [data-logged-in="true"]'))
        }))()"""
        )
        if self.rejection:
            raise ScrapingStopped(self.rejection)
        title = value["title"].lower()
        if any(
            word in title
            for word in (
                "just a moment",
                "access denied",
                "verify you are human",
                "attention required",
            )
        ):
            raise ScrapingStopped(
                "Browser challenge appeared. Collection stopped; normal "
                "verification must be completed manually before a later run."
            )
        _require_anonymous_public_page(value)
        return value

    def navigate(self, url: str, previous_first: str | None = None) -> dict:
        """Navigate once and wait for the actual new page, without retrying."""
        validate_public_url(url)
        self.rejection = None
        result = self.command("Page.navigate", {"url": url})
        if result.get("errorText"):
            raise ScrapingStopped(result["errorText"])
        deadline = time.monotonic() + 45
        while time.monotonic() < deadline:
            snapshot = self.snapshot()
            if (
                snapshot["ready"] == "complete"
                and _same_page(snapshot["url"], url)
                and (
                    previous_first is None
                    or snapshot.get("first") != previous_first
                )
            ):
                return snapshot
            time.sleep(0.5)
        raise ScrapingStopped(
            "The new page did not become visible within 45 seconds. "
            "No automatic retry was attempted."
        )

    def close(self) -> None:
        """Disconnect the local debugging socket without closing user pages."""
        self.socket.close()


def _same_page(actual: str, requested: str) -> bool:
    """Allow a trailing-slash redirect while retaining the exact cursor."""
    validate_public_url(actual)
    first, second = urlparse(actual), urlparse(requested)
    return (
        first.path.rstrip("/") == second.path.rstrip("/")
        and first.query == second.query
    )


def _require_anonymous_public_page(snapshot: dict) -> None:
    """Reject explicit login gates and evidence of a signed-in account."""
    url = snapshot.get("url", "")
    path = urlparse(url).path.lower()
    if re.search(r"/(?:login|signin|sign-in|auth|account)(?:/|$)", path):
        raise ScrapingStopped(
            "Login/account redirect detected; stop collection."
        )
    headings = " ".join(snapshot.get("headings", []))
    if snapshot.get("login_form") or re.search(
        r"\b(?:sign in|log in|login)\b", headings, re.I
    ):
        raise ScrapingStopped("Login-required page detected; stop collection.")
    for control in snapshot.get("account_controls", []):
        if re.search(
            r"\b(?:log\s*out|sign\s*out|my account|my profile|"
            r"manage account|account settings)\b",
            control.get("text", ""),
            re.I,
        ) or re.search(
            r"/(?:logout|signout|sign-out)(?:/|$)",
            control.get("target", ""),
            re.I,
        ):
            raise ScrapingStopped(
                "Signed-in account controls detected; only anonymous "
                "public pages may be collected."
            )
    if snapshot.get("authenticated_marker"):
        raise ScrapingStopped("Authenticated page marker detected; stop.")
    validate_public_url(url)


def _browser_executable(name: str) -> str:
    executable = "msedge.exe" if name == "edge" else "chrome.exe"
    found = shutil.which(executable)
    if found:
        return found
    folder = (
        "Microsoft/Edge/Application"
        if name == "edge"
        else "Google/Chrome/Application"
    )
    for variable in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA"):
        parent = os.environ.get(variable)
        candidate = Path(parent or ".") / folder / executable
        if parent and candidate.is_file():
            return str(candidate)
    raise FileNotFoundError(
        f"Could not locate {name}; provide --browser-path."
    )


def _tabs(port: int) -> list[dict]:
    with urlopen(f"http://127.0.0.1:{port}/json/list", timeout=5) as response:
        return json.load(response)


def _find_page(port: int) -> BrowserPage:
    for tab in _tabs(port):
        parsed = urlparse(tab.get("url", ""))
        if (
            tab.get("type") == "page"
            and parsed.hostname in {"www.thegradcafe.com", "thegradcafe.com"}
            and parsed.path == "/robots.txt"
        ):
            return BrowserPage(tab["webSocketDebuggerUrl"])
    raise ValueError(
        "Open public https://www.thegradcafe.com/robots.txt in the "
        "dedicated browser before attaching. Do not sign into an account."
    )


def main() -> int:
    """Run an explicitly verified browser session and resume saved progress."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--browser", choices=("edge", "chrome"), default="edge"
    )
    parser.add_argument(
        "--browser-path", help="Optional installed Chromium executable"
    )
    parser.add_argument(
        "--attach",
        action="store_true",
        help="Use an already running dedicated debugging session",
    )
    parser.add_argument("--port", type=int, default=9222)
    parser.add_argument(
        "--profile", type=Path, default=Path(".browser_profile")
    )
    parser.add_argument("--target", type=int, default=30000)
    parser.add_argument("--delay", type=float, default=6)
    parser.add_argument(
        "--output", type=Path, default=Path("applicant_data.json")
    )
    parser.add_argument("--raw-dir", type=Path, default=Path("raw"))
    args = parser.parse_args()
    page = None
    collector = None
    try:
        if not 1024 <= args.port <= 65535 or args.target < 1:
            raise ValueError(
                "Use a port from 1024 to 65535 and a positive target."
            )
        collector = GradCafeScraper(args.output, args.raw_dir, args.delay)
        collector.ensure_live_allowed()
        if len(collector.records) >= args.target:
            print(f"Target already met: {len(collector.records)} records.")
            return 0
        if not args.attach:
            try:
                connection = socket.create_connection(
                    ("127.0.0.1", args.port), timeout=1
                )
            except OSError:
                connection = None
            if connection is not None:
                connection.close()
                raise ValueError(
                    "Debugging port is occupied. Use --attach for your "
                    "existing dedicated browser, or choose another --port."
                )
            binary = args.browser_path or _browser_executable(args.browser)
            # The visible browser is explicitly part of this interactive flow.
            # A dedicated profile avoids accessing the user's default profile.
            subprocess.Popen(  # pylint: disable=consider-using-with
                [
                    binary,
                    f"--remote-debugging-port={args.port}",
                    "--remote-debugging-address=127.0.0.1",
                    f"--user-data-dir={args.profile.resolve()}",
                    "--new-window",
                    BASE_URL + "robots.txt",
                ]
            )
        print(
            "Open robots.txt in the dedicated browser. If challenged, "
            "complete normal human verification yourself."
        )
        print(
            "Wait for the robots.txt policy text. Do not sign into any "
            "GradCafe account or disable browser protections."
        )
        input("Press Enter only when robots.txt is visible without login: ")
        page = _find_page(args.port)
        policy = page.snapshot()
        if not _same_page(policy["url"], BASE_URL + "robots.txt"):
            raise ValueError(
                "The initial public robots policy is not visible."
            )
        args.raw_dir.mkdir(parents=True, exist_ok=True)
        policy_path = args.raw_dir / "browser-robots.txt"
        policy_path.write_text(policy["text"], encoding="utf-8")
        collector.check_robots(policy_path)
        screenshot = page.command("Page.captureScreenshot", {"format": "jpeg"})
        evidence = args.output.parent / "screenshot-robots-live.jpg"
        evidence.write_bytes(base64.b64decode(screenshot["data"]))
        url = collector.state.get("next_url")
        if not url:
            print(
                "Source pagination has no Next URL; collection is incomplete."
            )
            return 2
        previous_first = None
        page_number = (
            max(map(int, collector.state["completed_pages"]), default=0) + 1
        )
        while len(collector.records) < args.target:
            collector.ensure_live_allowed()
            time.sleep(collector.delay)
            current = page.navigate(url, previous_first)
            collector.ingest(
                current["html"].encode("utf-8"),
                page_number,
                current["url"],
                method="normal manually verified Chromium DOM",
            )
            print(
                f"Page {page_number}: "
                f"{len(collector.records)}/{args.target} records",
                flush=True,
            )
            previous_first = current.get("first")
            page_number += 1
            url = collector.state.get("next_url")
            if not url:
                break
        return 0 if len(collector.records) >= args.target else 2
    except (
        OSError,
        RuntimeError,
        ValueError,
        websocket.WebSocketException,
    ) as exc:
        if collector is not None and not collector.state.get("stop_reason"):
            collector.record_stop(str(exc))
        print(f"Browser collection stopped: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print(
            "Stopped by user; committed page progress is retained.",
            file=sys.stderr,
        )
        return 130
    finally:
        if page is not None:
            page.close()


if __name__ == "__main__":
    raise SystemExit(main())
