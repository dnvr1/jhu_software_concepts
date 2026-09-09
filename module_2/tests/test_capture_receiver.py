"""Verify the local capture receiver cannot accept arbitrary remote form data."""

from http.server import HTTPServer
import json
import threading
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import pytest

from capture_receiver import make_handler


@pytest.fixture
def receiver(tmp_path):
    """Run a temporary receiver without contacting GradCafe."""
    server = HTTPServer(("127.0.0.1", 0), make_handler(tmp_path, "test-token"))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}", tmp_path
    server.shutdown()
    server.server_close()
    thread.join()


def _submit(address, **changes):
    """Submit an explicitly synthetic HTML fixture to the local server."""
    fields = {
        "url": "https://www.thegradcafe.com/survey",
        "html": '<table><tr><td><a href="/result/1">Fixture</a></td></tr></table>',
        "token": "test-token",
    }
    fields.update(changes)
    request = Request(address, data=urlencode(fields).encode("utf-8"))
    return urlopen(request, timeout=5)


def test_capture_preserves_html_and_deduplicates_url(receiver):
    """Repeated capture of the same URL uses one source file and sidecar."""
    address, directory = receiver
    for _ in range(2):
        with _submit(address) as response:
            assert response.status == 200
    captures = list(directory.glob("*.html"))
    assert len(captures) == 1
    assert "Fixture" in captures[0].read_text(encoding="utf-8")
    metadata = json.loads(captures[0].with_suffix(".meta.json").read_text())
    assert metadata["source_url"] == "https://www.thegradcafe.com/survey"


@pytest.mark.parametrize(
    ("changes", "status"),
    [
        ({"token": "incorrect"}, 403),
        ({"url": "https://example.org/survey"}, 400),
        ({"url": "https://www.thegradcafe.com/result/1"}, 400),
        ({"html": "<h1>Verification required</h1>"}, 400),
    ],
)
def test_invalid_capture_writes_nothing(receiver, changes, status):
    """Invalid forms are rejected without leaving any files."""
    address, directory = receiver
    with pytest.raises(HTTPError) as caught:
        _submit(address, **changes)
    assert caught.value.code == status
    assert not list(directory.iterdir())
