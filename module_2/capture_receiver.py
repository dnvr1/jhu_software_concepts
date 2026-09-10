"""Save HTML captured from a manually verified browser through a local form.

This helper performs no remote requests and never solves browser challenges.
Run it from module_2, then submit the visible results table and its source URL.
"""

from __future__ import annotations

import argparse
import html
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
from pathlib import Path
import secrets
import tempfile
from urllib.parse import parse_qs, urlparse

from scrape import validate_public_url


def _atomic_write(path: Path, content: str) -> None:
    """Replace a capture after writing its complete UTF-8 text."""
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, delete=False
    ) as stream:
        temporary = Path(stream.name)
        stream.write(content)
    try:
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def make_handler(directory: Path, token: str) -> type[BaseHTTPRequestHandler]:
    """Create a local form handler restricted to public results."""

    class CaptureHandler(BaseHTTPRequestHandler):
        """Accept bounded local form submissions, with a per-run CSRF token."""

        def _reply(self, status: int, body: str) -> None:
            """Send a hardened, non-cacheable HTML response to localhost."""
            encoded = body.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Frame-Options", "DENY")
            self.end_headers()
            self.wfile.write(encoded)

        def do_GET(self) -> None:  # pylint: disable=invalid-name
            """Display the local capture form."""
            self._reply(
                200,
                "<!doctype html><title>GradCafe capture</title>"
                "<h1>Save visible GradCafe results</h1>"
                '<form method="post">'
                f'<input type="hidden" name="token" value="{token}">'
                '<label>Source URL<input name="url" required></label><br>'
                '<label>Captured HTML<textarea name="html" required '
                'rows="12" cols="90"></textarea></label><br>'
                '<button type="submit">Save capture</button></form>',
            )

        def do_POST(self) -> None:  # pylint: disable=invalid-name
            """Persist only a valid, bounded public admissions capture."""
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 2_000_000:
                    raise ValueError(
                        "Capture size must be between 1 and 2 MB."
                    )
                values = parse_qs(self.rfile.read(length).decode("utf-8"))
                if not secrets.compare_digest(
                    values.get("token", [""])[0], token
                ):
                    self._reply(403, "Invalid local form token.")
                    return
                url = validate_public_url(values["url"][0])
                if urlparse(url).path not in {"/survey", "/survey/"}:
                    raise ValueError(
                        "Only admissions result listings are accepted."
                    )
                markup = values["html"][0]
                if "<table" not in markup or "/result/" not in markup:
                    raise ValueError(
                        "Capture must contain the visible results table."
                    )
                existing = sorted(directory.glob("page-*.meta.json"))
                filename = None
                for metadata in existing:
                    if (
                        json.loads(metadata.read_text(encoding="utf-8")).get(
                            "source_url"
                        )
                        == url
                    ):
                        filename = metadata.name.removesuffix(".meta.json")
                        break
                if filename is None:
                    number = (
                        max(
                            (
                                int(item.name.split(".")[0].split("-")[1])
                                for item in existing
                            ),
                            default=0,
                        )
                        + 1
                    )
                    filename = f"page-{number:06d}"
                _atomic_write(directory / f"{filename}.html", markup)
                _atomic_write(
                    directory / f"{filename}.meta.json",
                    json.dumps(
                        {
                            "source_url": url,
                            "capture_method": "verified_browser_dom",
                        },
                        indent=2,
                    ),
                )
                self._reply(
                    200,
                    f"<h1>Saved {filename}.html</h1>"
                    "<a href='/'>Next capture</a>",
                )
            except (ValueError, KeyError, RuntimeError) as error:
                self._reply(400, html.escape(str(error)))

    return CaptureHandler


def main() -> None:
    """Start a loopback-only capture receiver until interrupted."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--directory", type=Path, default=Path("browser_captures")
    )
    parser.add_argument("--port", type=int, default=8766)
    args = parser.parse_args()
    args.directory.mkdir(parents=True, exist_ok=True)
    server = HTTPServer(
        ("127.0.0.1", args.port),
        make_handler(args.directory, secrets.token_urlsafe(32)),
    )
    print(f"Capture form: http://127.0.0.1:{args.port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
