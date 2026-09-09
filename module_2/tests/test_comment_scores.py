"""Synthetic narrative score regression cases; no live requests."""

import pytest

from comment_scores import enrich_scores


def entry(comment, **scores):
    keys = ("gpa", "gre", "gre_v", "gre_aw", "gre_quantitative")
    result = {key: scores.get(key) for key in keys}
    result["comments"] = comment
    result["score_provenance"] = {
        key: "structured_badge" if result[key] is not None else None
        for key in keys
    }
    return result


def test_missing_gre_and_cgpa_preserve_unknown_scale():
    row = enrich_scores(
        entry(
            "I am from India with the CGPA of 8.49 and with a GRE score of 318. Had work experience of 2.5 years in the relevant field."
        )
    )
    assert row["gre"] == 318
    assert row["gpa"] == 8.49
    assert row["score_context"]["gpa"]["label"] == "CGPA"
    assert row["score_context"]["gpa"]["scale"] is None
    for mention in row["comment_score_mentions"]:
        assert (
            row["comments"][mention["start"] : mention["end"]]
            == mention["excerpt"]
        )


def test_badges_keep_precedence_over_other_scales():
    row = enrich_scores(entry("GPA 5.49/6, GRE - 329/340.", gpa=3.7, gre=165))
    assert row["gpa"] == 3.7 and row["gre"] == 165
    assert [m["scale"] for m in row["comment_score_mentions"]] == [6, 340]
    assert not any(m["used_for_field"] for m in row["comment_score_mentions"])


@pytest.mark.parametrize(
    "comment",
    [
        "My friend has GPA 4.0",
        "Previous GPA 3.5",
        "Minimum GRE 320 required",
        "My target GPA 4.0",
        "Not my GRE 310",
        "GPA 3.0 and GPA 4.0",
        "GPA 5/4",
    ],
)
def test_ambiguous_or_invalid_mentions_are_review_only(comment):
    row = enrich_scores(entry(comment))
    assert row["gpa"] is None and row["gre"] is None
    assert all(m["review_reason"] for m in row["comment_score_mentions"])


def test_explicit_component_labels_and_scale():
    row = enrich_scores(entry("GRE Q 165, GRE V 159, GRE AW 4/6"))
    assert row["gre_quantitative"] == 165
    assert row["gre_v"] == 159
    assert row["gre_aw"] == 4
    assert row["gre"] is None
