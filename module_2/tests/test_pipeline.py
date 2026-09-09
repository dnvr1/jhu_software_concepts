"""Offline regression tests; all applicant examples here are synthetic fixtures."""

import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from clean import clean_data, extend_with_llm
from scrape import (
    GradCafeScraper,
    ScrapingStopped,
    load_data,
    result_url,
    save_data,
)


def listing(identifier=101, program="Computer Science", next_link=True):
    """Return a synthetic example of the observed desktop/mobile table layout."""
    return f"""<!doctype html><html><title>Results</title><table><tbody>
    <tr><td><div>Example University</div></td>
    <td><div><span>{program}</span><span>Masters</span></div></td>
    <td>Sep 08, 2026</td><td>Accepted on Sep 08</td>
    <td><a href='/result/{identifier}'>View</a></td></tr>
    <tr><td colspan='100%'><div><span>Accepted on Sep 08</span>
    <span>Fall 2027</span><span>International</span><span>GPA 3.85</span>
    <span>GRE 325</span><span>GRE V 162</span><span>GRE AW 4.5</span></div></td></tr>
    <tr><td colspan='100%'><p>Research &amp; funding; someone said GPA 4.0.</p></td></tr>
    <tr><td colspan='100%'><div></div></td></tr>
    </tbody></table>
    {"<a rel='next' href='/survey?cursor=real-cursor'>Next »</a>" if next_link else ''}
    </html>"""


@pytest.fixture
def scraper(tmp_path):
    """Create an isolated collector authorized by a synthetic robots fixture."""
    policy = tmp_path / "policy.txt"
    policy.write_text(
        "User-agent: *\nAllow: /\nDisallow: /private\n", encoding="utf-8"
    )
    collector = GradCafeScraper(
        tmp_path / "applicant_data.json", tmp_path / "raw"
    )
    collector.check_robots(policy)
    return collector


def test_parser_extracts_all_source_fields_without_comment_score_leak(scraper):
    row = scraper.parse_html(listing(), result_url(1))[0]
    assert row["program"] == "Computer Science, Example University"
    assert row["program_name"] == "Computer Science"
    assert row["university"] == "Example University"
    assert row["degree"] == "Masters"
    assert row["status"] == "Accepted"
    assert row["date_added"] == "Sep 08, 2026"
    assert row["acceptance_date"] == "Sep 08"  # No invented year.
    assert row["rejection_date"] is None
    assert row["term"] == "Fall 2027"
    assert row["citizenship"] == "International"
    assert (row["gpa"], row["gre"], row["gre_v"], row["gre_aw"]) == (
        3.85,
        325,
        162,
        4.5,
    )
    assert row["comments"] == "Research & funding; someone said GPA 4.0."
    assert row["raw_program"] == "Computer Science Masters"
    assert "GPA 3.85" in row["raw_text"]


def test_missing_values_are_null_and_source_text_is_preserved(scraper):
    html = """<table><tr><td>Example U</td><td><span>Unknown &amp; New</span></td>
    <td></td><td>Wait listed</td><td><a href='/result/88'>View</a></td></tr></table>"""
    row = scraper.parse_html(html, result_url(1))[0]
    assert row["status"] == "Waitlisted"
    assert row["program_name"] == "Unknown & New"
    assert all(
        row[key] is None
        for key in (
            "gpa",
            "gre",
            "gre_v",
            "gre_aw",
            "degree",
            "comments",
            "date_added",
            "decision_date",
        )
    )


def test_multiple_records_keep_their_comments_separate(scraper):
    first = listing(1).split("<tbody>")[1].split("</tbody>")[0]
    second = (
        listing(2, "Math")
        .split("<tbody>")[1]
        .split("</tbody>")[0]
        .replace(
            "Research &amp; funding; someone said GPA 4.0.", "Second comment"
        )
    )
    rows = scraper.parse_html(
        f"<table><tbody>{first}{second}</tbody></table>", result_url(1)
    )
    assert len(rows) == 2
    assert rows[0]["comments"].startswith("Research")
    assert rows[1]["comments"] == "Second comment"


def test_mobile_decision_badge_is_not_a_comment_and_mfa_is_preserved(scraper):
    html = """<table><tr><td>Example College</td>
    <td><div><span>Creative Writing Fiction</span><span>MFA</span></div></td>
    <td>Sep 08, 2026</td><td>Accepted on Sep 08</td>
    <td><a href='/result/99'>View</a></td></tr>
    <tr><td colspan='100%'><div><div>Accepted on Sep 08</div>
    <div>Fall 2026</div><div>American</div></div></td></tr></table>"""
    row = scraper.parse_html(html, result_url(1))[0]
    assert row["comments"] is None
    assert row["degree"] == "MFA"


def test_program_title_cannot_supply_citizenship_or_scores(scraper):
    html = """<table><tr><td>Example College</td>
    <td><span>International Studies GRE 300</span><span>PhD</span></td>
    <td>Sep 08, 2026</td><td>Accepted on Sep 08</td>
    <td><a href='/result/99'>View</a></td></tr>
    <tr><td colspan='100%'><div><div>Other</div></div></td></tr>
    <tr><td colspan='100%'><p>International applicant GPA 4.0</p></td></tr>
    </table>"""
    row = scraper.parse_html(html, result_url(1))[0]
    assert row["citizenship"] == "Other"
    assert row["gre"] is None
    assert row["gpa"] == 4.0
    assert row["score_provenance"]["gpa"] == "comment_labeled_narrative"


def test_missing_program_name_is_preserved_as_null(scraper):
    html = """<table><tbody><tr><td>Example Divinity School</td>
    <td><span></span><span>Masters</span></td><td>Mar 09, 2026</td>
    <td>Accepted on Mar 09</td><td><a href='/result/77'>View</a></td></tr>
    <tr><td colspan='5'><div>Fall 2026</div><div>American</div></td></tr>
    </tbody></table>"""
    row = scraper.parse_html(html, result_url(1))[0]
    assert row["program"] is None
    assert row["program_name"] is None
    assert row["university"] == "Example Divinity School"
    assert row["degree"] == "Masters"
    assert row["raw_program"] == "Masters"


def test_only_reviewed_parser_stop_can_be_resolved(scraper):
    scraper.record_stop("HTTP 403")
    with pytest.raises(ValueError):
        scraper.resolve_parser_stop("not allowed")
    scraper.state["stop_reason"] = (
        "Unrecognized applicant row layout; refusing to silently discard fields"
    )
    scraper.resolve_parser_stop("Empty program name represented as null")
    assert scraper.state["stop_reason"] is None
    assert scraper.state["stop_history"][-1]["resolution"].endswith("null")


def test_first_actual_capture_matches_inspected_source(scraper):
    capture = (
        Path(__file__).resolve().parents[1]
        / "browser_captures"
        / "page-000001.html"
    )
    if not capture.exists():
        pytest.skip("The optional real source capture is not present")
    rows = scraper.parse_html(
        capture.read_text(encoding="utf-8"),
        "https://www.thegradcafe.com/survey",
    )
    assert len(rows) == 20
    assert rows[0]["university"] == "Randolph College"
    assert rows[0]["program_name"] == "Creative Writing Fiction"
    assert rows[0]["degree"] == "MFA"
    assert rows[0]["comments"] is None
    assert rows[0]["acceptance_date"] == "Sep 08"
    heidelberg = next(
        row for row in rows if row["university"] == "Heidelberg University"
    )
    assert heidelberg["citizenship"] == "Other"


def test_model_source_guard_rejects_unsupported_new_names():
    pytest.importorskip("llama_cpp")
    from llm_hosting.app import _guard_source_candidate

    assert (
        _guard_source_candidate(
            "University of Dhaka",
            "University of Dhaaka",
            ["University of Dhaka"],
        )
        == "University of Dhaka"
    )
    assert (
        _guard_source_candidate(
            "Jewish Studies", "Jewiš Studies", ["Jewish Studies"]
        )
        == "Jewish Studies"
    )
    assert (
        _guard_source_candidate("New Program", "Invented Program", [])
        == "New Program"
    )


def test_explicit_complete_gre_comment_fills_only_missing_metrics(scraper):
    html = """<table><tr><td>Example University</td>
    <td><span>Engineering Management</span><span>Masters</span></td>
    <td>Aug 28, 2026</td><td>Accepted on Apr 10</td>
    <td><a href='/result/555'>View</a></td></tr>
    <tr><td><div>Fall 2026</div><div>GPA 2.21</div></td></tr>
    <tr><td><p>GRE, Quantitative: 165, Verbal: 159, Analytical Writing: 4</p>
    </td></tr></table>"""
    row = scraper.parse_html(html, "https://www.thegradcafe.com/survey")[0]
    assert row["gre"] is None
    assert row["gre_quantitative"] == 165
    assert row["gre_v"] == 159
    assert row["gre_aw"] == 4
    assert row["gpa"] == 2.21
    assert row["score_provenance"]["gre_v"] == "comment_explicit_declaration"
    assert row["score_provenance"]["gpa"] == "structured_badge"
    assert row["score_provenance"]["gre"] is None


def test_comment_declaration_never_overrides_badges(scraper):
    html = listing().replace(
        "Research &amp; funding; someone said GPA 4.0.",
        "GRE, Quantitative: 165, Verbal: 159, Analytical Writing: 4",
    )
    row = scraper.parse_html(html, "https://www.thegradcafe.com/survey")[0]
    assert (row["gre"], row["gre_v"], row["gre_aw"]) == (325, 162, 4.5)
    assert row["gre_quantitative"] == 165
    assert row["score_provenance"]["gre_v"] == "structured_badge"


@pytest.mark.parametrize(
    "comment",
    [
        "My friend has GRE, Quantitative: 165, Verbal: 159, Analytical Writing: 4",
        "GRE, Quantitative: 165, Verbal: 159, Analytical Writing: 4 in 2015",
        "No GRE",
        "McGill MA in Economics, GPA 3.55",
        "GRE 165/159/4",
    ],
)
def test_narrative_or_ambiguous_comment_scores_are_not_inferred(comment):
    from scrape import _declared_comment_gre

    assert _declared_comment_gre(comment) == {}


@pytest.mark.parametrize(
    "html",
    [
        "<title>Just a moment...</title>",
        "<form id='challenge-form'></form>",
        "<h1>Unexpected layout</h1>",
    ],
)
def test_challenges_and_layout_changes_fail_closed(scraper, html):
    with pytest.raises(ScrapingStopped):
        scraper.parse_html(html, result_url(1))


def test_cursor_pagination_uses_actual_link(scraper):
    url = "https://www.thegradcafe.com/survey/"
    assert (
        scraper.next_url(listing(), url)
        == "https://www.thegradcafe.com/survey?cursor=real-cursor"
    )
    assert scraper.next_url(listing(next_link=False), url) is None
    with pytest.raises(ScrapingStopped):
        scraper.next_url(
            "<a rel='next' href='https://other.example/survey'>Next</a>", url
        )


def test_robots_denial_prevents_collection(tmp_path):
    robots = tmp_path / "robots.txt"
    robots.write_text("User-agent: *\nDisallow: /survey\n", encoding="utf-8")
    collector = GradCafeScraper(tmp_path / "out.json", tmp_path / "raw")
    with pytest.raises(ScrapingStopped, match="robots.txt"):
        collector.check_robots(robots)
    assert not collector.output.exists()


def test_journals_resume_without_duplicate_records(scraper):
    scraper.ingest(listing().encode(), 1)
    resumed = GradCafeScraper(scraper.output, scraper.raw_dir)
    resumed.check_robots(scraper.raw_dir / "robots.txt")
    assert len(resumed.records) == 1
    assert resumed.ingest(listing().encode(), 1) == 0
    assert resumed.state["next_url"].endswith("cursor=real-cursor")
    assert (
        resumed.ingest(
            listing(102, next_link=False).encode(),
            2,
            resumed.state["next_url"],
        )
        == 1
    )
    assert len(load_data(resumed.output)) == 2


def test_recover_after_aggregate_write_is_interrupted(scraper):
    with patch(
        "scrape.save_data", side_effect=OSError("simulated disk interruption")
    ):
        with pytest.raises(OSError):
            scraper.ingest(listing().encode(), 1)
    resumed = GradCafeScraper(scraper.output, scraper.raw_dir)
    assert len(load_data(resumed.output)) == 1
    assert "1" in resumed.state["completed_pages"]


def test_rebuild_missing_aggregate_from_journals(scraper):
    scraper.ingest(listing().encode(), 1)
    scraper.output.unlink()
    resumed = GradCafeScraper(scraper.output, scraper.raw_dir)
    assert len(load_data(resumed.output)) == 1


def test_old_score_schema_is_rejected_without_touching_files(scraper):
    scraper.ingest(listing().encode(), 1)
    old = load_data(scraper.output)
    del old[0]["gre_quantitative"]
    del old[0]["score_provenance"]
    save_data(old, scraper.output)
    before = {path: path.read_bytes() for path in scraper.raw_dir.iterdir()}
    old_bytes = scraper.output.read_bytes()
    with pytest.raises(ValueError, match="Incompatible checkpoint schema"):
        GradCafeScraper(scraper.output, scraper.raw_dir)
    assert scraper.output.read_bytes() == old_bytes
    assert all(
        path.read_bytes() == payload for path, payload in before.items()
    )


def test_all_journals_are_checked_before_recovery_writes(scraper):
    scraper.ingest(listing(1).encode(), 1)
    journal = json.loads(
        (scraper.raw_dir / "page-000001.json").read_text(encoding="utf-8")
    )
    journal["page"] = 2
    journal["records"][0]["url"] = "https://www.thegradcafe.com/result/2"
    del journal["records"][0]["score_provenance"]
    second = scraper.raw_dir / "page-000002.json"
    second.write_text(json.dumps(journal), encoding="utf-8")
    scraper.output.unlink()
    scraper.state_path.unlink()
    with pytest.raises(ValueError, match="Incompatible checkpoint schema"):
        GradCafeScraper(scraper.output, scraper.raw_dir)
    assert not scraper.output.exists()
    assert not scraper.state_path.exists()


def test_explicit_old_checkpoint_version_requires_replay(scraper):
    scraper.ingest(listing().encode(), 1)
    state = json.loads(scraper.state_path.read_text(encoding="utf-8"))
    state["parser_schema_version"] = 1
    scraper.state_path.write_text(json.dumps(state), encoding="utf-8")
    with pytest.raises(ValueError, match="Checkpoint parser schema 1"):
        GradCafeScraper(scraper.output, scraper.raw_dir)


def test_repeated_page_or_duplicate_only_page_stops(scraper):
    scraper.ingest(listing().encode(), 1)
    with pytest.raises(ScrapingStopped, match="repeats the HTML"):
        scraper.ingest(listing().encode(), 2)
    with pytest.raises(ScrapingStopped, match="no new applicant"):
        scraper.ingest(listing().replace("Results", "Results 2").encode(), 2)


def test_rejected_request_latches_stop_without_retry(scraper):
    scraper._request = Mock(side_effect=ScrapingStopped("HTTP 429"))
    with pytest.raises(ScrapingStopped, match="HTTP 429"):
        scraper.scrape_data()
    assert scraper._request.call_count == 1
    resumed = GradCafeScraper(scraper.output, scraper.raw_dir)
    resumed._request = Mock()
    with pytest.raises(ScrapingStopped, match="previous live run"):
        resumed.scrape_data()
    resumed._request.assert_not_called()


def test_html_cleaning_does_not_change_raw_fields():
    row = clean_data(
        [
            {
                "program": "<b>Math &amp; CS</b>",
                "raw_program": "  Math &amp; CS  ",
                "comments": "GPA < 3.0",
            }
        ]
    )[0]
    assert row["program"] == "Math & CS"
    assert row["raw_program"] == "  Math &amp; CS  "
    assert row["comments"] == "GPA < 3.0"


def test_json_unicode_round_trip_and_invalid_shape(tmp_path):
    path = tmp_path / "data.json"
    save_data([{"program": "Université — Études", "gpa": None}], path)
    assert load_data(path)[0]["gpa"] is None
    path.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="JSON array"):
        load_data(path)


def test_missing_instructor_package_is_explicit(tmp_path):
    with pytest.raises(FileNotFoundError, match="Canvas file 19121115"):
        extend_with_llm(
            tmp_path / "in.json", tmp_path / "out.json", tmp_path / "absent"
        )
    assert not (tmp_path / "out.json").exists()


def test_llm_adapter_preserves_source_and_resumes_cached_batches(tmp_path):
    package = tmp_path / "llm_hosting"
    package.mkdir()
    (package / "app.py").write_text(
        "# synthetic test stub, never a supplied-package replacement",
        encoding="utf-8",
    )
    original = {
        "program": "Math, Example U",
        "url": "https://www.thegradcafe.com/result/1",
        "raw_program": "Math",
        "gpa": 3.1,
    }
    candidate = {
        **original,
        "gpa": 9,
        "llm-generated-program": "Mathematics",
        "llm-generated-university": "Example University",
    }
    source, target = tmp_path / "in.json", tmp_path / "out.json"
    save_data([original], source)
    result = Mock(returncode=0, stdout=json.dumps([candidate]), stderr="")
    with patch("clean.subprocess.run", return_value=result) as run:
        assert extend_with_llm(source, target, package) == 1
        assert extend_with_llm(source, target, package) == 1
        assert run.call_count == 1
    row = load_data(target)[0]
    assert row["program"] == original["program"]
    assert row["gpa"] == 3.1
    assert row["llm-generated-program"] == "Mathematics"


def test_llm_refuses_changed_record_identity(tmp_path):
    package = tmp_path / "llm_hosting"
    package.mkdir()
    (package / "app.py").write_text("# synthetic test stub", encoding="utf-8")
    source, target = tmp_path / "in.json", tmp_path / "out.json"
    save_data(
        [{"program": "Math", "url": "https://www.thegradcafe.com/result/1"}],
        source,
    )
    result = Mock(
        returncode=0,
        stdout=json.dumps(
            [
                {
                    "program": "Math",
                    "url": "https://www.thegradcafe.com/result/2",
                }
            ]
        ),
    )
    with (
        patch("clean.subprocess.run", return_value=result),
        pytest.raises(ValueError, match="changed url"),
    ):
        extend_with_llm(source, target, package)
    assert not target.exists()
