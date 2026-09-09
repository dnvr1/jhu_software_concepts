"""Ensure the independent audit detects corrupted synthetic data."""

import hashlib
import json

from audit_data import audit


def test_audit_detects_changed_score_and_unbacked_entry(tmp_path):
    html = """<table><tbody><tr><td>Example University</td>
    <td><span>Example Program</span><span>Masters</span></td>
    <td>Sep 08, 2026</td><td>Accepted on Sep 08</td>
    <td><a href='/result/1'>View</a></td></tr>
    <tr><td colspan='5'><div>Fall 2026</div><div>American</div>
    <div>GPA 3.50</div></td></tr></tbody></table>"""
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / "page-000001.html").write_text(html, encoding="utf-8")
    manifest = {
        "archive": "page-000001.html",
        "source_url": "https://www.thegradcafe.com/survey",
        "sha256": hashlib.sha256(
            (raw / "page-000001.html").read_bytes()
        ).hexdigest(),
    }
    (raw / "page-000001.json").write_text(
        json.dumps({"manifest": manifest}), encoding="utf-8"
    )
    record = {
        "url": "https://www.thegradcafe.com/result/1",
        "university": "Example University",
        "program_name": "Example Program",
        "program": "Example Program, Example University",
        "degree": "Masters",
        "date_added": "Sep 08, 2026",
        "status": "Accepted",
        "decision_date": "Sep 08",
        "acceptance_date": "Sep 08",
        "rejection_date": None,
        "term": "Fall 2026",
        "citizenship": "American",
        "comments": None,
        "raw_program": "Example Program Masters",
        "gre": None,
        "gre_v": None,
        "gre_aw": None,
        "gpa": 3.5,
    }
    path = tmp_path / "data.json"
    path.write_text(json.dumps([record]), encoding="utf-8")
    assert not audit(path, raw)["mismatches"]
    record["gpa"] = 4.0
    path.write_text(json.dumps([record]), encoding="utf-8")
    assert audit(path, raw)["mismatches"][0]["field"] == "gpa"
    path.write_text(
        json.dumps([record, dict(record, url="missing")]), encoding="utf-8"
    )
    assert audit(path, raw)["unbacked_urls"] == ["missing"]
